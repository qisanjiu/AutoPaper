---
stage: S27
phase: P7
agent: writing
version: "1.0"
depends_on: [S26]
status: draft
---

# S27: Introduction & Related Work

> Agent: `writing`
> Phase: P7
> 目标: 撰写论文的 Introduction 和 Related Work 部分，建立研究动机，定位贡献

---

## 1. 核心目标

将 S02 的文献综述和 S24 的贡献声明转化为符合学术规范的 Introduction + Related Work。本阶段的核心任务是：
- **遵循框架**: 根据 S26 §3 的领域框架决策（Related Work 位置、section 命名等）组织内容
- **建立动机**: 让读者理解"为什么这个问题值得研究"
- **定位贡献**: 清晰说明我们的工作与已有工作的区别
- **展示领域理解**: 证明作者对领域有深入把握
- **术语统一**: 遵循 S26 §5 术语表和风格约定

---

## 2. Introduction 写作

### 2.1 结构（5 段式）

**段落 1: 背景 + 广泛意义**
- 从宏观角度引入研究领域
- 说明该领域的重要性和应用价值

**段落 2: 现有工作的进展 + 局限性**
- 简述领域已有进展（引用 2-3 篇关键工作）
- 指出现有方法的核心局限性（自然引出 Gap）
- 必须引用 S02 中识别的关键文献

**段落 3: 我们的方法 + 核心洞察**
- 一句话概括我们的核心方法
- 说明我们如何解决上述局限性
- 强调核心洞察（insight）

**段落 4: 主要贡献（bullet list）**
- 2-4 条贡献，每条具体、可验证
- 必须与 S24 的贡献声明一致
- 使用 "We propose...", "We design...", "We demonstrate..." 等主动句式

**段落 5: 论文结构概述**
- 简述后续各 section 的内容安排

### 2.2 写作原则
- **Anti-Leakage**: 所有 LLM 写作调用前必须附加 Anti-Leakage Prompt
- **Academic Style Prompt**: 所有 LLM 写作调用前必须附加 Academic Style Prompt
- **引用纪律**: 每个 claim 必须有引用支撑，不能编造
- **对比明确**: 明确指出 "与 [X] 不同，我们..."
- **长度控制**: 1.0-1.5 页（取决于 venue 页数限制，严格遵循 S26 §4 页数预算）
- **术语一致性**: 所有核心术语使用 S26 §5.1 术语表中定义的统一表述，首次出现时定义缩写

---

## 3. Related Work 写作

### 3.1 结构

按主题组织（而非按时间罗列）：

**子主题 A**: [方法学派/技术路线 A]
- 简述该方向的代表性工作（2-3 篇）
- 指出其局限性

**子主题 B**: [方法学派/技术路线 B]
- 同上

**与我们的区别**
- 表格对比或段落说明
- 明确列出 2-3 个关键差异

### 3.2 写作原则
- **对比和批判**: 不能只是文献列表，必须有分析和对比
- **引用最新工作**: 优先引用近 2 年的相关工作
- **公平性**: 不能故意贬低已有工作来抬高自己
- **长度控制**: 0.5-1.0 页

---

## 4. Reasoning Trail

- **为什么选择这个 Introduction 结构？** ...
- **为什么引用这些论文而非其他？** ...
- **Related Work 的分类依据是什么？** ...

---

## 5. 验证与检查

- [ ] Introduction 建立了清晰的研究动机
- [ ] 现有工作的局限性分析有文献支撑
- [ ] 我们的方法和洞察被清晰表述
- [ ] 贡献列表与 S24 一致
- [ ] Related Work 有对比和批判（非简单罗列）
- [ ] 所有引用在 `refs.bib` 中存在
- [ ] Anti-Leakage Prompt 已应用
- [ ] Academic Style Prompt 已应用
- [ ] 长度在 S26 §4 页数预算内
- [ ] Section 结构与 S26 §3 领域框架决策一致
- **学术风格自查**：
  - [ ] 无 contractions（don't, can't, won't, it's, we're 等）
  - [ ] 无博客式问句标题（"Why X?", "What went wrong?"）
  - [ ] 无口语化过渡词（"Let's dive into...", "Now, let's talk about..."）
  - [ ] 正文无 bullet list（贡献声明段除外）
  - [ ] 无单句段落（数学定义框后的过渡除外）
  - [ ] 所有结论性 claim 有适当 hedging（suggest/indicate，非 prove/demonstrate）
  - [ ] 无 informal emphasis（"a lot of", "really", "very", "huge"）
  - [ ] 核心术语与 S26 §5.1 术语表一致
  - [ ] 引用格式统一使用 `\cite{key}`，图表引用使用 `Figure~\ref{}` / `Table~\ref{}`

---

## 6. 风险与限制

| 风险 | 影响 | 缓解措施 | 状态 |
|------|------|---------|------|
| Introduction 过长 | 挤压后续 section 空间 | 严格控制 1.5 页以内 | 开放 |
| Related Work 遗漏关键文献 | 审稿人质疑领域理解 | 对照 S02 文献分类表检查 | 开放 |

---

## 7. 下游接口（传递给下游的关键信息）

1. Introduction 的核心动机句: ...
2. 贡献声明的表述方式: ...
3. Related Work 的分类框架: ...
4. 引用的关键文献列表: ...

---

## 8. 回溯触发器

- 如果 S33 发现 Introduction 动机不够强 → 回溯到 S27 重写
- 如果 S35 审稿人指出遗漏相关工作 → 回溯到 S27 补充引用
