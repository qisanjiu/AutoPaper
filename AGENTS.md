# SpiralResearch — Agent 全局上下文

> **作用范围**: 本文件适用于所有在 SpiralResearch 框架内工作的 Agent。  
> **读取时机**: 每次会话初始化、Context Recovery、或不确定项目位置时。  

---

## 1. 目录结构约定

### 1.1 框架根目录 (Framework Root)

包含 `spiral/`、`docs/`、`config/`、`scripts/`、`templates/` 的目录即为框架根目录。

- 当前框架根目录：**`.`（本文件所在目录）**

### 1.2 项目根目录 (Projects Root)

所有研究项目统一存放在 **框架根目录的父目录下的 `projects/`** 中：

```
Projects Root = {Framework Root}/../projects
```

- 当前项目根目录：**`{FrameworkRoot}/../projects`**

### 1.3 项目文件夹命名格式

```
{sanitized_name}-{YYYYMMDD-HHMMSS}/
```

例如：`radar-vital-signs-20260423-135322/`

---

## 2. 项目发现流程（所有 Agent 通用）

当需要定位项目时，按以下顺序执行：

```
1. 推导项目根目录
   → Framework Root / .. / projects

2. 检查项目根目录是否存在
   → 不存在：创建该目录（mkdir -p）

3. 列出已有项目
   → 遍历 projects/ 下所有子目录
   → 筛选包含 state/pipeline_state.yaml 的有效项目

4. 确定目标项目
   a) 用户明确指定了项目路径 → 直接使用
   b) 用户指定了项目名称（部分匹配）→ 匹配唯一项目
   c) 存在 "current_project" 标记 → 使用该标记指向的项目
   d) 只有一个项目 → 自动选中
   e) 多个项目且未指定 → 列出所有项目，询问用户
```

### 2.1 当前活跃项目标记

用户主目录下的 `~/.spiral/current_project` 文件（纯文本，内容为项目目录的绝对路径）用于记录默认项目。

设置方式：
```bash
# 通过 state_manager 设置（在框架根目录执行）
python scripts/state_manager.py use ../projects/PROJECT-NAME
```
`use` 命令会将绝对路径写入 `~/.spiral/current_project`，确保后续命令不受 CWD 影响。

---

## 3. 关键路径速查表

| 路径 | 说明 |
|------|------|
| `.` | 框架根目录（本文件所在目录） |
| `{FrameworkRoot}/../projects` | 项目根目录 |
| `{project}/state/pipeline_state.yaml` | 项目状态文件 |
| `{project}/state/decision_log.md` | 决策日志 |
| `{project}/state/spiral_log.md` | 螺旋日志 |
| `{project}/knowledge/` | 知识产出目录 |
| `{project}/artifacts/` | 最终产物目录 |
| `{project}/drafts/` | 各 Stage 草稿目录 |

---

## 4. 环境变量（可选）

| 变量 | 作用 |
|------|------|
| `SPIRAL_FRAMEWORK_ROOT` | 覆盖框架根目录的自动检测 |

如果设置了该环境变量，框架根目录以该变量为准，项目根目录仍为其父目录下的 `projects/`。
