---
type: learned
learned_from: "基于深度学习和毫米波雷达的呼吸检测-20260418-170818"
stage: "S13"
date: "2026-04-20"
clear_after: "3 projects"
severity: medium
---

## 问题描述

S13（Experiment Execution）中，实验代码未设置随机种子，导致结果不可复现。S16 统计验证时发现 variance 异常高，回溯到 S13 重新执行。

## 根因分析

S12（Code Review）的 Stage Inspector 未包含"随机种子设置"检查项。Critic Team 在 S33 审查时才发现问题。

## 预防措施

执行 S11（Code Generation）时，Agent 必须：
1. 在代码中显式设置随机种子（`random.seed()`, `np.random.seed()`, `torch.manual_seed()`）
2. 将种子值记录在 `experiments/configs/config.yaml` 中
3. S12 Code Review 时，Inspector 必须检查随机种子设置

执行 S13 前，先运行 `utils/reproducibility_check.py`（如存在）验证可复现性。

## 验证方法

检查代码中是否存在 `seed` 相关设置，且配置文件中是否记录种子值。
