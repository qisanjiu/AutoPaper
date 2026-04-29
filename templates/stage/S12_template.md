---
stage: S12
phase: P3
agent: experiment
version: "1.1"
depends_on: [S11]
status: draft
---

# S12: Experiment Execution, Result Collection & Preliminary Analysis

> Agent: `experiment`
> Phase: P3
> 目标: 执行实验迭代探索，收集所有实验结果进行初步观察。**不做 KEEP/DISCARD/FIX/BACKTRACK 决策——这些是 S13 (Analysis Agent) 的独占职责。**

---

## 1. 核心目标

执行实验迭代探索，收集所有实验结果并进行初步观察。本阶段内嵌实验迭代循环（Inner Loop）：
- **迭代探索**: 修改代码 → git commit → 运行实验 → 评估 → 初步观察 → 决定下一步探索方向
- **所有尝试保留**: 每次迭代都有 git commit 和 `results.tsv` 记录（**不做 git reset**）
- **收敛判断**: 当指标收敛、预算耗尽、或方向已充分探索时停止
- **不做最终决策**: S12 只记录"战术性方向判断"（往哪继续尝试），不做 KEEP/DISCARD/FIX/BACKTRACK 决策。这些决策由 S13 (Analysis Agent) 在深度分析后做出。

---

## 2. 产出文件清单（实际文件）

| 文件路径 | 类型 | 说明 |
|---------|------|------|
| `experiments/results/results.tsv` | 数据文件 | 所有实验迭代的完整结果记录 |
| `knowledge/S12_experiment_iteration.md` | 知识文件 | 实验迭代记录和战术方向观察报告 |
| `experiments/results/best_checkpoint/` | 目录 | 最佳结果的 checkpoint |
| `experiments/logs/` | 目录 | 每次迭代的训练日志 |

---

## 3. 实验迭代探索（AutoResearch Inner Loop）

### 3.1 迭代流程

```
Inner Loop:
  verify data availability → modify code → git commit → run iteration (5-30min) → evaluate → preliminary analysis
        ▲                                                                                    │
        └────────────────── 持续探索，所有尝试保留 ───────────────────────────────────────┘
```

**核心原则**:
- 每个 experiment iteration 都有 git commit 和 `results.tsv` 记录
- 所有实验尝试（包括失败的）都通过 git commit 保存，**不做 git reset**
- 当达到收敛条件（指标收敛/预算耗尽/方向已充分探索）时停止迭代
- **数据可用性在首次迭代前必须确认**（见 §3.2 步骤 0）
- **远程模式下先完成环境准备**（见 §3.2 步骤 0.5）

### 3.2 环境准备与迭代步骤

**步骤 0.5: 远程环境准备（仅 remote_ssh / remote_slurm 模式，首次执行）**

如果是远程模式，在数据检查之前须先完成远程环境准备：

```bash
# 使用 RemoteExecutor 完成一键 setup（读取项目本地 config/environment.yaml）
python -c "
from spiral.remote_executor import create_executor
from pathlib import Path
import yaml

with open('state/pipeline_state.yaml') as f:
    state = yaml.safe_load(f)
project_name = state['project']['name']
project_dir = Path.cwd()

executor = create_executor(project_name, project_dir)
# create_executor 自动读取 {project_dir}/config/environment.yaml
# 如果不存在则回退到 AutoPaper 全局默认配置
ok, msg = executor.setup()
print(msg)
if not ok:
    exit(1)
"
```

`executor.setup()` 依次执行：
1. `check_ssh_connection()` — 验证 SSH 连接可达
2. `setup_remote_env()` — 在远端创建 `~/AutoPaper/projects/{project_name}/experiments/` 目录 + `autopaper_{project_name}` conda 环境
3. `sync_to_remote()` — rsync 上传 `experiments/` 目录（排除 results/、checkpoints/、logs/、__pycache__/）
4. `install_requirements()` — 在远端 conda 环境中 `pip install -r requirements.txt`

> **注意**：`setup()` 仅在首次迭代前执行一次。后续迭代只需 `sync_to_remote()` + `run_remote()`。

**步骤 0: 数据可用性检查（首次迭代前执行，后续迭代可跳过）**

在进行任何实验之前，必须执行数据可用性验证：

1. **检查数据路径**: 验证 `main_exp.yaml` 中 `data.root` 路径存在且非空
2. **尝试下载**（如数据不存在）: 运行 `python experiments/src/download_data.py`
3. **下载结果判定**:

   | 情况 | 操作 | 记录要求 |
   |------|------|---------|
   | 数据已存在且完整 | 直接进入步骤 1 | 在 results.tsv 中记录 `data_source: real` |
   | 下载成功 | 验证完整性后进入步骤 1 | 记录下载耗时、文件数量 |
   | 下载失败（网络/权限/超时） | 查阅 S07 §6.3 降级策略 | **显式记录**失败原因，评估降级方案 |
   | 降级为合成数据 | 在 config 中设置 `use_synthetic: true` + `synthetic_reason` | **必须在 results.tsv 和最终论文中标注** |

4. **数据状态记录**: 在 `results.tsv` 第一条记录中写入数据来源状态：

   ```tsv
   commit_hash  metric  notes
   DATA_STATUS  -       data_source:real|synthetic  source_path:/path/to/data  reason:...
   ```

> **禁止行为**：数据不存在时静默使用合成数据。如果 data_root 为空且下载失败，必须**显式决策**并记录原因后才能继续。

**步骤 1-5（执行迭代，模式感知）**:

**本地模式 (mode: local)**：

1. **代码修改**: 根据上一次迭代的分析结果，修改实验代码
2. **git commit**: 记录本次修改的内容和目的
3. **运行实验**: `python experiments/src/train.py --config experiments/configs/main_exp.yaml`
4. **结果记录**: 将关键指标写入 `results.tsv`
5. **初步分析**: 评估本次迭代的效果变化

**远程模式 (mode: remote_ssh)**：

1. **代码修改**: 根据上一次迭代的分析结果，修改本地实验代码
2. **git commit**: 记录本次修改的内容和目的
3. **同步到远端**: `executor.sync_to_remote()` （仅同步 experiments/，排除 results/checkpoints/logs）
4. **远程执行**: `executor.run_remote("python train.py --config configs/main_exp.yaml")`
   - 自动执行: `conda activate autopaper_{project} && cd ~/AutoPaper/projects/{project}/experiments && python train.py ...`
5. **回传结果**: `executor.sync_from_remote()` （拉取 results/、checkpoints/、logs/）
6. **结果记录**: 将关键指标写入 `results.tsv`（读取回传的 results/ 目录）
7. **初步分析**: 评估本次迭代的效果变化

**远程模式 (mode: remote_slurm)**：

同上，但步骤 4 改为提交 Slurm 作业并等待完成。

### 3.3 收敛条件

- [ ] 主要指标在最近 N 次迭代中波动小于阈值（ε）
- [ ] 时间预算已耗尽
- [ ] 当前方向的变体已充分探索
- [ ] 已到达预设的最大迭代次数

---

## 4. 战术方向观察（非决策）

> **重要**: 以下表格记录的是 S12 在迭代过程中的**战术性方向判断**（"下一步往哪走"），
> **不是最终决策**。所有 git commit 均保留。最终的 KEEP/DISCARD/FIX/BACKTRACK 决策由 S13 (Analysis Agent) 做出。

### 4.1 单次迭代方向判断

| 方向判断 | 依据 | 后续动作 |
|---------|------|---------|
| **继续当前方向** | 指标有改善，趋势向好 | 下一轮在此方向上进一步尝试 |
| **换个方向** | 指标无改善或变差 | 尝试不同的修改方向 |
| **本轮无效** | 遇到 NaN/崩溃/OOM 等技术问题 | 标记问题类型，下一轮避开此配置 |

### 4.2 循环停止时的状态报告

在所有迭代完成后，向 S13 报告：
- 各方向探索的 commit 数量和覆盖的修改类型
- 表面指标最高的 commit 及其指标值（**非"最佳"判定，S13 会基于深度分析重新评估**）
- 各 commit 对应的完整复现路径（commit hash + 配置文件）

---

## 5. 数据质量检查

### 5.1 数据来源与完整性

- [ ] **数据来源确认**: `results.tsv` 第一条记录包含 `DATA_STATUS`，明确标注 `data_source: real | synthetic`
- [ ] 如使用合成数据：`synthetic_reason` 已填写，降级策略来自 S07 §6.3
- [ ] 缺失值检查：无 NaN 或异常空值
- [ ] 异常值检查：无超出合理范围的数值
- [ ] 分布检查：训练/验证/测试集分布一致

### 5.2 过拟合检测
- [ ] train/val 差距在合理范围（通常 < 5%）
- [ ] 验证集指标曲线稳定（非持续上升后陡降）
- [ ] 测试集仅用于最终评估，未参与任何超参选择

### 5.3 数据泄露检查
- [ ] 验证集信息未间接用于训练（如：在训练集上进行特征选择时使用了全数据集统计量）
- [ ] 数据增强不会在 train/val 间共享状态
- [ ] 预训练模型检查：未使用包含测试集的预训练数据

### 5.4 训练稳定性
- [ ] loss 曲线正常（无 NaN、无突然跳变）
- [ ] 梯度范数在合理范围
- [ ] 多 seed 方差在合理范围（通常 std < 1%）

---

## 6. Reasoning Trail

- **为什么选择这个迭代策略？**（例如：从简单到复杂，从粗调到精调）
- **为什么在某次迭代中选择了特定的探索方向？**（具体原因和观察）
- **收敛条件是否合适？**（为什么选择这些收敛条件）
- **各探索方向的效果差异**（哪些方向有前景，哪些方向无效果）

---

## 7. 验证与检查

- [ ] 所有实验尝试都有 git commit 记录
- [ ] `results.tsv` 完整记录所有迭代结果（包括失败尝试）
- [ ] **`results.tsv` 第一条为 DATA_STATUS + ENV_STATUS 记录**（数据来源 + 执行模式：local/remote_ssh/remote_slurm + host）
- [ ] **远程模式：executor.setup() 已成功执行**（SSH 连接、目录创建、conda 环境、代码同步、依赖安装）
- [ ] **远程模式：每次迭代后 executor.sync_from_remote() 已执行**（结果已回传本地）
- [ ] 战术方向判断记录完整，每项有依据（注意：非最终决策，S13 做最终评估）
- [ ] 数据来源和完整性检查通过（§5.1）
- [ ] 过拟合检测完成，无异常
- [ ] 数据泄露检查完成，无风险
- [ ] 训练稳定性检查完成
- [ ] 最佳 checkpoint 已选定并保存
- [ ] 最佳结果的复现路径已记录（commit hash + 配置）
- [ ] 如使用合成数据：**论文 S29 中必须明确标注**（"due to data access limitations, experiments use synthetic data..."）

---

## 8. 风险与限制

| 风险 | 影响 | 缓解措施 | 状态 |
|------|------|---------|------|
| 迭代无法收敛 | 时间耗尽但无明显改善 | 设置最大迭代次数和预算上限 | 开放 |
| 数据未下载直接使用合成数据 | 实验结果无法反映真实性能 | **§3.2 步骤 0 数据可用性检查**；合成数据必须显式标注 | 开放 |
| SSH 连接断开 | 远程实验中断，结果丢失 | 每次迭代后立即 `sync_from_remote()`；使用 `ServerAliveInterval` | 开放 |
| 远程 conda 环境创建失败 | 无法在远端执行 | `setup()` 中降级为 minimal Python 环境；提示用户手动安装 PyTorch | 开放 |
| 数据泄露未被发现 | 结果不可信，回溯成本高 | 严格的 train/val 隔离检查 | 开放 |
| 过拟合未被检测 | 验证集指标虚高，测试集性能差 | 监控 train/val 差距，多 seed 验证 | 开放 |
| 代码 bug 导致无效结果 | 大量迭代时间浪费 | 先运行小规模 pilot 验证 pipeline | 开放 |
| 硬件不稳定导致结果噪声 | 指标波动无法判断真实趋势 | 同环境下多次运行 baseline 确认稳定性 | 开放 |

---

## 9. 下游接口（传递给下游的关键信息）

1. **最佳实验结果的 commit hash 和指标**: 供 S13 验证和分析使用
2. **所有尝试的完整记录** (`results.tsv`): 供 S13 统计分析和 S18 深度分析使用
3. **数据质量评估结论**: 供 S13 确认数据可信度
4. **数据来源状态** (`DATA_STATUS` in results.tsv): 真实数据 / 合成数据 + 原因 → S29（论文实验部分必须标注） + S13（分析时考虑数据可信度）
5. **执行环境信息**: 模式（local/remote_ssh/remote_slurm）+ 主机 + conda 环境名 → 复现性保证
6. **完整迭代记录 (`results.tsv`) 和战术方向观察**: 供 S13 进行深度分析后做出最终 KEEP/DISCARD/FIX/BACKTRACK 决策
7. **最佳 checkpoint 路径**: 供后续消融和分析实验使用

---

## 10. 回溯触发器

- 如果发现代码实现 bug 导致结果无效 → 回溯到 S11 (Code Generation)
- 如果发现方法设计缺陷（多次迭代后指标仍无改善）→ 回溯到 S06 (Methodology Design)
- 如果核心假设被实验结果否定（方法明显弱于 baseline）→ 回溯到 S04 (Hypothesis Generation)
- 如果数据质量存在系统性问题（如数据泄露无法修复）→ 回溯到 S07 (Benchmark Selection)
