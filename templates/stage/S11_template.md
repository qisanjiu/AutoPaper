---
stage: S11
phase: P3
agent: experiment
version: "1.0"
depends_on: [S10]
status: draft
---

# S11: Code Generation

> Agent: `experiment`
> Phase: P3
> 目标: 实现方法和所有 baseline 的代码，确保可运行、可复现

---

## 1. 核心目标

将 S06 的方法设计和 S09 的 baseline 选择转化为可运行的代码。本阶段的核心任务是：
- **方法实现**: 将核心算法转化为代码
- **Baseline 复现**: 实现或适配所有对比方法
- **代码结构**: 建立清晰、模块化的代码库
- **可复现性**: 确保代码能在干净环境中运行

---

## 2. 产出文件清单（实际文件）

| 文件路径 | 类型 | 说明 | 行数 |
|----------|------|------|------|
| `experiments/src/model.py` | 实际文件 | 核心方法实现 | ~XXX |
| `experiments/src/train.py` | 实际文件 | 训练脚本（AutoResearch 风格主文件） | ~XXX |
| `experiments/src/evaluate.py` | 实际文件 | 评估脚本 | ~XXX |
| `experiments/src/data_loader.py` | 实际文件 | 数据加载（含真实数据加载 + 合成降级） | ~XXX |
| `experiments/src/download_data.py` | 实际文件 | **数据集下载脚本**（基于 S07 §6 下载URL） | ~XXX |
| `experiments/src/utils.py` | 实际文件 | 工具函数 | ~XXX |
| `experiments/configs/main_exp.yaml` | 实际文件 | 主实验配置 | ~XXX |
| `experiments/configs/ablation_*.yaml` | 实际文件 | 消融实验配置 | ~XXX |
| `experiments/baselines/baseline_1/` | 实际目录 | baseline 1 实现 | ~XXX |
| `experiments/baselines/baseline_2/` | 实际目录 | baseline 2 实现 | ~XXX |
| `experiments/requirements.txt` | 实际文件 | 依赖 | ~XXX |

---

## 3. 代码结构概览

```
experiments/
├── src/
│   ├── model.py          # 核心方法实现
│   ├── train.py          # 训练脚本（AutoResearch 风格迭代主文件）
│   ├── evaluate.py       # 评估脚本
│   ├── data_loader.py    # 数据加载（基于 S07 预处理方案）
│   ├── download_data.py  # 数据集下载脚本（基于 S07 §6 下载URL）
│   └── utils.py          # 工具函数
├── configs/
│   ├── main_exp.yaml     # 主实验配置（基于 S08 超参数）
│   ├── dev_exp.yaml      # 开发调试配置（仅在有验证需求时使用）
│   └── ablation_*.yaml   # 消融实验配置（基于 S14）
├── baselines/
│   ├── baseline_1/       # baseline 1（基于 S09）
│   └── baseline_2/       # baseline 2
├── requirements.txt
└── .gitignore
```

---

## 4. 关键实现决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 深度学习框架 | PyTorch/TensorFlow/JAX | ... |
| 分布式训练 | 单卡/DDP | ... |
| 核心文件 | `train.py` | AutoResearch 风格：主要在此文件中迭代 |
| 配置管理 | YAML / Hydra / argparse | ... |

---

## 5. 数据加载与下载（强制规范）

> **核心原则**：`data_loader.py` 必须**首先尝试加载真实数据**。合成数据仅在真实数据确实不可获取时使用，且必须**显式记录原因**。

### 5.1 `download_data.py` — 数据集下载脚本（强制）

必须生成独立的下载脚本，包含：

```python
# download_data.py — 下载 S07 选定的所有数据集
# 基于 S07 §6.2 下载可行性报告中确认的 URL 和路径

DATASETS = {
    "dataset_name": {
        "url": "https://...",           # 来自 S07 §2
        "expected_size_gb": X,          # 来自 S07 §6.2
        "target_dir": "experiments/data/dataset_name/",
        "checksum": "...",              # 如可用
    },
    # ... 所有数据集
}

def download_all():
    for name, info in DATASETS.items():
        if os.path.exists(info["target_dir"]) and len(os.listdir(info["target_dir"])) > 0:
            print(f"[SKIP] {name}: already downloaded at {info['target_dir']}")
            continue
        print(f"[DOWNLOAD] {name}: downloading {info['expected_size_gb']}GB from {info['url']}")
        # 实际下载逻辑（使用 urllib / wget / gdown / kaggle API 等）
        ...
```

**要求**：
- 每个数据集有独立的下载函数
- 支持断点续传（如文件较大）
- 下载后验证文件完整性（文件数量、大小校验）
- 下载失败时输出明确错误信息（非静默跳过）

### 5.2 `data_loader.py` — 数据加载器规范

**禁止**以下模式（当前的实际问题模式）：

```python
# ❌ 禁止：_load_real() 是占位符，永远返回 False
def _load_real(self, data_root, ...):
    return False  # Placeholder — always falls back to synthetic
```

**必须**实现以下模式：

```python
# ✅ 正确模式：优先真实数据，显式降级
class DataLoader:
    def __init__(self, data_root: str, use_synthetic: bool = False, synthetic_reason: str = ""):
        """
        Args:
            data_root: 真实数据集根目录（来自 main_exp.yaml）
            use_synthetic: 是否使用合成数据。仅在下述情况可设为 True：
                (a) 运行 download_data.py 后下载失败
                (b) S07 §6.3 降级策略中预先批准的场景
                (c) 资源预算不足，且已在 S12 中记录
            synthetic_reason: 使用合成数据的理由（强制，use_synthetic=True 时必填）
        """
        if use_synthetic:
            assert synthetic_reason, "Must provide reason when using synthetic data!"
            print(f"[WARNING] Using synthetic data. Reason: {synthetic_reason}")
            self._load_synthetic(...)
        else:
            if not os.path.exists(data_root):
                raise FileNotFoundError(
                    f"Data root '{data_root}' not found. "
                    f"Run 'python download_data.py' first, or set use_synthetic=True with a documented reason."
                )
            self._load_real(data_root, ...)

    def _load_real(self, data_root, ...):
        """加载真实数据集。必须完整实现，不得返回 False 占位。"""
        # 实际的数据加载逻辑
        ...
```

### 5.3 配置文件数据相关字段

`main_exp.yaml` 中数据相关配置：

```yaml
data:
  root: "experiments/data/"           # 数据集根目录（download_data.py 的下载目标）
  dataset: "dataset_name"             # 来自 S07
  use_synthetic: false                # 默认 false！仅在下载确实不可行时设为 true
  synthetic_reason: ""                # use_synthetic=true 时必填
  download_script: "experiments/src/download_data.py"
```

> **关键**：`use_synthetic` 默认值必须为 `false`。如果 S07 的下载可行性检验已确认数据可获取，则没有理由默认为 `true`。

---

## 6. 核心代码说明

对方法中最复杂的部分进行解释，附**关键代码片段 ≤15 行**。完整代码见实际文件。

### 6.1 [核心模块 A]
```python
# 关键代码片段（≤15 行）
...
```

### 6.2 [核心模块 B]
```python
# 关键代码片段（≤15 行）
...
```

---

## 7. 与设计的一致性

| 设计 (S06) | 实现 | 是否一致 | 差异原因（如有） |
|------------|------|---------|---------------|
| 组件 A | ... | 是/否 | ... |
| 组件 B | ... | 是/否 | ... |

---

## 8. 已知问题

| 问题 | 状态 | 说明 |
|------|------|------|
| ... | 已修复/待修复/已知限制 | ... |

---

## 9. 复现指南

```bash
# 环境安装
pip install -r experiments/requirements.txt

# 运行主实验（默认）
python experiments/src/train.py --config experiments/configs/main_exp.yaml

# 运行评估
python experiments/src/evaluate.py --checkpoint path/to/checkpoint

# 开发调试（仅在有验证需求时使用）
# python experiments/src/train.py --config experiments/configs/dev_exp.yaml
```

---

## 10. 验证与检查

- [ ] 所有代码已保存为实际文件（非仅 MD 描述）
- [ ] `S11_code_generation.md` 仅含描述和短片段（≤15 行），不含完整可执行代码
- [ ] 产出文件清单完整（路径、类型、说明、行数）
- [ ] **`download_data.py` 已生成**，包含所有数据集的下载逻辑（含断点续传和完整性校验）
- [ ] **`data_loader.py` 中 `_load_real()` 是完整实现**（非占位符 `return False`）
- [ ] **`main_exp.yaml` 中 `use_synthetic` 默认为 `false`**
- [ ] 下游 Agent 可直接运行 `python experiments/src/train.py`
- [ ] 代码能在干净环境中复现运行
- [ ] 随机种子已固定并记录
- [ ] 所有超参数保存在配置文件中
- [ ] 代码遵循 S06 设计（或差异已记录）

---

## 11. 风险与限制

| 风险 | 影响 | 缓解措施 | 状态 |
|------|------|---------|------|
| 实现与设计不符 | 实验结果不可靠 | 对照 S06 逐项检查 | 开放 |
| baseline 实现有 bug | 不公平对比 | sanity check：复现 baseline 论文报告结果 | 开放 |
| 数据下载脚本失败 | 实验使用合成数据 | 遵循 S07 §6.3 降级策略；在 S12 中记录原因 | 开放 |
| `_load_real()` 是占位符 | 静默使用合成数据 | §5.2 强制规范：抛出异常而非静默回退 | 开放 |

---

## 12. 下游接口（传递给下游的关键信息）

1. 核心文件已确定为 `src/train.py`，后续迭代主要修改此文件
2. 代码已测试通过的功能: ...
3. 可能需要额外关注的实现细节: ...
4. 完整代码 → S12 (Experiment Execution)

---

## 13. 回溯触发器

- 如果 S12 发现代码 bug 导致实验失败 → 回溯到 S11 修复
- 如果 S12 发现方法无法实现设计目标 → 回溯到 S06 重新设计
- 如果 S15 发现消融代码实现错误 → 回溯到 S11 修改基础代码
