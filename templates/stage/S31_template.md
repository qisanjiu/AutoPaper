---
stage: S31
phase: P7
agent: writing
version: "1.0"
depends_on: [S30]
status: draft
---

# S31: Abstract & Conclusion

> Agent: `writing`
> Phase: P7
> 目标: 撰写摘要和结论，精确概括全文核心贡献

---

## 1. 核心目标

为论文撰写独立可读的 Abstract 和简洁有力的 Conclusion。本阶段的核心任务是：
- **遵循框架**: 根据 S26 §3 的领域框架决策（Abstract 长度、Conclusion 风格等）撰写
- **Abstract 独立可读**: 不读正文也能理解核心贡献
- **数值精确**: Abstract 中的具体数字与正文完全一致
- **Conclusion 无新内容**: 不引入正文中未提及的论点
- **与 S24 一致**: 贡献表述与 S24 的贡献声明一致
- **术语统一**: 遵循 S26 §5 术语表

---

## 2. Abstract 写作

### 2.1 结构（150-250 词）

**一句话概括**: 用一句话概括论文的核心贡献（适合 Twitter/宣传）

**问题**: 1-2 句话描述研究背景和问题

**方法**: 1-2 句话描述核心方法

**结果**: 1-2 句话报告主要结果（具体数值）

**贡献**: 1 句话总结核心贡献

### 2.2 写作原则
- **无引用**: Abstract 通常不含引用
- **无缩写**: 首次出现的术语应写全称（除非领域通用）
- **具体数字**: 报告具体数值（如 "提升 3.2%" 而非 "显著提升"）
- **独立可读**: 不依赖正文的上下文

---

## 3. Conclusion 写作

### 3.1 结构（0.3 页）

**核心贡献回顾**: 2-3 句话回顾主要贡献（与 Abstract 呼应但不重复）

**主要发现**: 1-2 句话强调最重要的发现

**未来方向**: 1 句话简要提及未来工作（可引用 S25，但不展开）

### 3.2 写作原则
- **不引入新内容**: Conclusion 中不应出现正文未讨论的内容
- **不重复 Abstract**: 与 Abstract 互补而非重复
- **不夸张**: 诚实总结，不做过度的普遍性宣称

---

## 4. 数据一致性检查

| 数值 | Abstract | 正文 (S29) | 是否一致 |
|------|---------|-----------|---------|
| 主实验提升 | ... | ... | 是/否 |
| 数据集名称 | ... | ... | 是/否 |
| 指标名称 | ... | ... | 是/否 |

---

## 5. Reasoning Trail

- **Abstract 的哪句话最能吸引读者？** ...
- **Conclusion 是否准确反映了论文的实际贡献？** ...
- **Abstract 和 Conclusion 的分工是否清晰？** ...

---

## 6. 验证与检查

- [ ] Abstract 独立可读
- [ ] 所有数值与正文（S29）一致
- [ ] Conclusion 不引入新论点
- [ ] 与 S24 贡献声明一致
- [ ] 长度符合 S26 §4 页数预算（Abstract 150-250 词，Conclusion ~0.25 页）
- [ ] Anti-Leakage Prompt 已应用
- [ ] Academic Style Prompt 已应用
- **学术风格自查**：
  - [ ] 无 contractions（don't, can't, won't, it's, we're 等）
  - [ ] 无口语化过渡词
  - [ ] 正文无 bullet list（Abstract/Conclusion 不使用 bullet list）
  - [ ] 无单句段落
  - [ ] 所有结论性 claim 有适当 hedging
  - [ ] 无 informal emphasis（"a lot of", "really", "very", "huge"）
  - [ ] 术语与 S26 §5.1 术语表一致
  - [ ] Abstract 中无引用（除非 venue 明确要求）
  - [ ] Conclusion 不引入正文未提及的内容

---

## 7. 风险与限制

| 风险 | 影响 | 缓解措施 | 状态 |
|------|------|---------|------|
| Abstract 夸大贡献 | 审稿人期望过高 | 对照 S24 诚实评估 | 开放 |
| Conclusion 引入新内容 | 逻辑不一致 | 逐句核对正文 | 开放 |

---

## 8. 下游接口（传递给下游的关键信息）

1. Abstract 文本 → S33 (Full Draft Assembly)
2. Conclusion 文本 → S33
3. 核心贡献标准表述 → 确保全文一致

---

## 9. 回溯触发器

- 如果 S33 发现数值不一致 → 回溯到 S31 核对
- 如果 S35 审稿人建议修改 Abstract → 回溯到 S31 调整
