---
name: paper-review-team
description: 论文同行评审多 agent 团队 — 组建 4 个真正独立的 agent(主编/方法论专家/领域专家/魔鬼代言人)并行评审 draft/paper.md，突破单 agent 串行扮演的"伪独立评审"，汇总共识与分歧输出修改路线图。用于论文质量验收、Stage 7 增强评审、需要严格多视角把关时。
argument-hint: '[论文路径，默认 draft/paper.md]'
user-invocable: true
allowed-tools: 'Read, Write, Edit, Bash, AskUserQuestion'
version: 1.0.0
---

# Paper Review Team — 论文同行评审多 agent 团队

## 解决什么问题

`paper-workflow` 的 Stage 7 按 `peer-review-simulation.md` 模拟 4 角色评审，但实现是**单个 agent 依次扮演 4 个角色**。方法论第 91 行要求"每位评审人**独立**阅读论文"，而单 agent 串行做不到真独立 —— 同一上下文里演完主编再演魔鬼代言人，前面读论文形成的印象会污染后续判断，所谓"4 位独立评审人"只是**名义上的**。

本 skill 把它升级为 **4 个真正独立的 agent 并行评审**（独立上下文、互不可见对方评审），再由 lead 汇总成修改路线图。

> **依赖**：评审维度、角色定义、评审表格式引用自 `../paper-workflow/references/peer-review-simulation.md`，本 skill 是其**执行层**，不复制内容。若脱离本项目单独使用，需自带该文档。

## 何时用

- 论文初稿完成、进入质量验收（对应 Stage 7）
- 需要严格的多视角把关（投稿前最后一道防线）
- 想要真正的对抗性评审，尤其是魔鬼代言人视角

## 何时不用

- 只想快速过一遍 → 用 `/paper-workflow review` 单 agent 即可，更快更省
- 论文还在大纲/片段阶段（先 `/paper-workflow outline` 或 `write`）
- 单节小修改 → 单 agent 评审足够

## 团队架构

| # | Teammate | 角色 | 关注点 | 文件所有权 | 模型 |
|---|----------|------|--------|-----------|------|
| — | **lead**（调用方会话） | 协调 + 汇总决策 | 汇总 4 份评审 → 修改路线图 | 读 4 份评审 + 写 `output/review-report.md` | 当前会话 |
| 1 | `reviewer-eic` | 主编(EIC) | 整体质量、创新性、期刊匹配度 | 读 `paper.md` + 写 `output/reviews/eic.md` | Sonnet 4.5 |
| 2 | `reviewer-method` | 方法论专家 | 研究设计、数据、分析方法 | 读 `paper.md` + 写 `output/reviews/method.md` | Sonnet 4.5 |
| 3 | `reviewer-domain` | 领域专家 | 理论贡献、实践意义、文献覆盖 | 读 `paper.md` + 写 `output/reviews/domain.md` | Sonnet 4.5 |
| 4 | `reviewer-devil` | 魔鬼代言人 | 主动找弱点、拒稿理由 | 读 `paper.md` + 写 `output/reviews/devil.md` | **Opus 4.6** |

**文件所有权零重叠**：4 评审全部**只读** `draft/paper.md`，各自写独立文件 → 满足 agent team 硬约束（无写冲突）。

**模型选择理由**：
- 3 位常规评审 = 只读 + 按文档维度填表 = well-defined 任务，Sonnet 足够且省
- 魔鬼代言人 = 对抗性深度推理，Opus 明显更"刁钻"，是评审质量命门，值得用 Opus

## 执行步骤

收到调用后，按以下步骤执行（核心是 spawn 4 个独立评审 teammate）：

1. **读取背景**：`Read` 论文（默认 `draft/paper.md`，或参数指定路径）+ `project_context.md`（写作意图）
2. **确认评审规范**：方法论（4 角色、7 维度、决策逻辑）参照 `../paper-workflow/references/peer-review-simulation.md`；**产出格式严格按 `references/review-template.md`**（评审表 + 汇总报告模板，不自创）
3. **并行 spawn 4 评审**（见下方 Prompt）—— delegate 模式，独立上下文，互不可见
4. **等待 4 份评审全部完成**
5. **lead 汇总**：按严重程度排序问题，标记共识（≥2 人提及）与分歧，生成修改路线图，写入 `output/review-report.md`

## 可用 Prompt（直接 spawn 团队）

```text
组建论文同行评审 agent team，对 draft/paper.md 做 4 角色独立评审。

先 Read draft/paper.md（全文）和 project_context.md（写作意图）。
方法论（角色/维度/决策）遵循 .claude/skills/paper-workflow/references/peer-review-simulation.md；
产出格式（评审表、汇总报告）严格按 .claude/skills/paper-review-team/references/review-template.md。

Spawn 4 个评审 teammate（delegate 模式，独立上下文，互相不可见对方评审，
确保真正独立——这是与单 agent 串行评审的根本区别）：

1. "reviewer-eic" - 扮演主编(EIC)。关注整体质量、创新性、与目标期刊
   匹配度。核心问题：这篇论文是否值得发表？按 7 维度填评审表，给出
   接受/小修/大修/拒绝 结论。只读 draft/paper.md，写到
   output/reviews/eic.md。不修改论文。Use Sonnet 4.5.

2. "reviewer-method" - 扮演方法论专家。深挖"研究方法""结果与讨论"
   两维。核心问题：方法是否严谨？证据链是否完整？有无逻辑跳跃？
   只读 paper.md，写到 output/reviews/method.md。Use Sonnet 4.5.

3. "reviewer-domain" - 扮演领域专家。深挖"文献综述""选题与创新性"。
   核心问题：对领域的贡献是什么？研究缺口陈述是否成立？核心文献
   有无遗漏？只读 paper.md，写到 output/reviews/domain.md。Use Sonnet 4.5.

4. "reviewer-devil" - 扮演魔鬼代言人。主动找弱点、过度声称、逻辑漏洞、
   可被拒稿的理由。务必尖锐、具体、可操作，不要客套。只读 paper.md，
   写到 output/reviews/devil.md。Use Opus 4.6.

4 份评审全部完成后，由我(lead)汇总：按严重程度排序所有问题，
标记共识(≥2人提及)与分歧，生成修改路线图(优先级1必须改/2应该改/
3建议改)，写入 output/review-report.md。汇总遵循 peer-review-simulation.md
的 Phase 2-3。

Use delegate mode. tmux layout: tiled.
```

## 输出物

```
output/
├── reviews/
│   ├── eic.md          # 主编评审
│   ├── method.md       # 方法论专家评审
│   ├── domain.md       # 领域专家评审
│   └── devil.md        # 魔鬼代言人评审（最尖锐）
└── review-report.md    # lead 汇总：共识/分歧 + 修改路线图
```

`review-report.md` 是给 Stage 8（`/paper-workflow revise`）的输入 —— 修改时按路线图优先级逐项处理。

## 与 paper-workflow 的关系

- **引用而非复制**（遵循 `docs/architecture.md` 决策 1）：评审方法论单一信息源在 `peer-review-simulation.md`，本 skill 只负责执行
- **解耦**：可独立 `/paper-review-team` 调用，不强制依赖 paper-workflow 的命令链
- **集成点**：作为 Stage 7 的增强执行器 —— 想要更严格评审时用它替代默认的单 agent `review`

## 致谢

本 skill 的多 agent 独立评审设计，方法论基础来自 `paper-workflow/references/peer-review-simulation.md`（其源头见 paper-workflow 的致谢声明：academic-research-skills，Cheng-I Wu，CC BY-NC 4.0）。
