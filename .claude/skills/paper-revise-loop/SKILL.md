---
name: paper-revise-loop
description: 论文修改 Worker/Verifier 对抗循环 — Worker 按评审路线图逐条改 draft/paper.md，独立 Verifier 对照 review-report 四态核验"改到位没"，收敛（N=2 重试预算+死锁检测+升级人工）破解 Stage 8 单 agent 自改自验的 self-preferential bias。用于投稿前严格修改验收、Stage 8 增强执行。
argument-hint: '[论文路径，默认 draft/paper.md]'
user-invocable: true
allowed-tools: 'Read, Write, Edit, Bash, Agent, AskUserQuestion'
version: 1.0.0
---

# Paper Revise Loop — 论文修改 Worker/Verifier 对抗循环

## 解决什么问题

`paper-workflow` 的 Stage 8 revise 默认是**单 agent 自己改自己验**：读评审报告 → 按优先级改 → 改完重跑 `validate`/`verify`。但 `validate`/`verify` 是脚本，只查引文编号一致性与文献真实性，**没有任何机制验收"评审意见是否被实质回应"**。

这是两个结构性失效模式的教科书现场：

- **Self-Preferential Bias**：写初稿的 agent 被要求改自己刚写的东西，天然倾向维护原文、逐条反驳评审意见。
- **Goal Drift**：改着改着"顺手"扩大改动范围，偏离评审报告的实际诉求。

本 skill 把 Stage 8 升级为 **Worker（改）/ Verifier（独立核验）对抗循环**：Worker 按修改路线图改，独立的 Verifier 逐条核验"改到位没"，不通过则带反馈打回重改，收敛或升级人工。与 `/paper-review-team` 形成闭环——**评审能真独立，修改也真有独立验收**。

> **理论依据**：收敛模型（重试预算、置信度四态、死锁检测、升级路径）映射自 Agent 平台基础设施层的 Worker/Verifier 对抗循环架构。

## 何时用

- 投稿前最后一道修改验收（对应 Stage 8）
- 手上有严格的 `review-report.md`（含 P1/P2/P3 修改路线图），要逐条确认落实
- 想要真正的独立验收，确认评审意见被**实质回应**而非表面应付

## 何时不用

- 只想快速过一遍 → 用 `/paper-workflow revise` 单 agent 即可，更快更省
- 没有 `review-report.md`（先 `/paper-workflow review` 或 `/paper-review-team`）
- 单条小修（改错别字 / 调格式）→ 单 agent 足够

## 团队架构

| # | 角色 | 关注点 | 文件所有权 | 模型 |
|---|------|--------|-----------|------|
| — | **lead**（调用方会话） | Team Engine：展开路线图为 checklist、驱动循环、汇总 | 读 review-report + 各轮产出 + 写 `output/revise/revise-report.md` | 当前会话 |
| 1 | `worker` | 按 checklist 逐条改 paper | 读 `draft/paper.md` + 读 `review-report` 路线图（或经 lead 展开的 checklist），**唯一写** `draft/paper.md` + 写 `output/revise/worker-roundN.md` | **Sonnet 4.5** |
| 2 | `verifier` | 独立核验"改到位没" | **只读** `draft/paper.md` + 只读 `review-report.md`，写 `output/revise/verifier-roundN.md` | **Opus 4.6** |

**文件所有权零重叠**：Worker 唯一写 `draft/paper.md`；Verifier 只读它 + 写独立报告 → 满足 agent 零写冲突硬约束。

**落地方式**：用 **Agent 工具（subagent 模式，非 Agent Team）** 串行 spawn。理由——Worker↔Verifier 是**串行依赖**（Worker 改完 Verifier 才能验，Verifier 不通过 Worker 才能再改），每轮是一次性任务，subagent 比 teammates 长期驻留更直接、lead 上下文更干净。与 `/paper-review-team`（并行评审用 Agent Team）形态不同，因任务结构不同。

**模型选择理由**（沿用 paper-review-team 哲学）：

- Worker = 按路线图既定方向执行修改 = well-defined 任务，Sonnet 够且省
- Verifier = 判断"实质诉求是否被回应" + 挑错 = adversarial reasoning，Opus 明显更"刁钻"，是验收质量命门

**成本**：一轮 = 1 Sonnet + 1 Opus 全文核验。N=2 最坏 = 2 Sonnet + 2 Opus。需省时可用"经济模式"（Verifier 降 Sonnet），但对抗性下降。

## 收敛规则（映射 Worker/Verifier 对抗循环）

| 维度 | 规则 | 取值 |
|------|------|------|
| **重试预算 N** | 单条路线图项最多改几轮 | **N=2**（论文修改重，2 轮仍不行多为结构性分歧，升级人） |
| **置信度四态** | Verifier 对每条路线图项给判定 | `已修复`(通过) / `部分修复`(附理由，打回) / `未修复`(打回) / `引入新问题`(打回) |
| **死锁检测** | Worker↔Verifier 连续轮次重复相同论据（N≥3 时为独立判据；N=2 下与升级路径重合） | N=2 下，第 2 轮仍不通过即触发升级 |
| **升级路径** | 预算耗尽 / 死锁 | 停循环，`revise-report.md` 列"需人工裁决项" + 双方论据，交作者 |

**全通过判定**：所有路线图项均为 `已修复` 且无 `引入新问题` → 收敛。

## 执行步骤

收到调用后（lead 即调用方会话，充当 Team Engine）：

1. **读取输入**：`Read` 论文（默认 `draft/paper.md`）+ 评审报告（默认 `output/review-report.md`）
2. **展开 checklist**：从 review-report 的"修改路线图"（P1/P2/P3 表，格式见 `../paper-review-team/references/review-template.md` §5）抽出每条 → 逐条编号，形成可核验 checklist
3. **Round 1 改**：用 **Agent 工具 spawn `worker`**（Sonnet）按 checklist 改 `draft/paper.md`，产出 `output/revise/worker-round1.md`
4. **Round 1 验**：用 **Agent 工具 spawn `verifier`**（Opus），**独立**读改后的 `draft/paper.md` + `review-report.md`（**不读 worker 说明**），对每条四态判定，产出 `output/revise/verifier-round1.md`
5. **判收敛**：全通过 → 跳到 8；否则进入 Round 2
6. **Round 2 改+验**：spawn `worker`（**带 verifier-round1 反馈**）再改 → spawn `verifier` 再核验
7. **判收敛/升级**：全通过 → 跳到 8；仍未通过 → 标记未通过项为"需人工裁决"，进 8
8. **汇总**：lead 写 `output/revise/revise-report.md`（收敛通过项 / 人工裁决项 + 双方论据）；重跑 `validate` + `verify --offline` 确认引文未破坏

## Verifier 核验要求（写进 verifier prompt）

Verifier 对每条路线图项只回答三件事，**不得评判"改得好不好看"**（那是作者的审美）：

1. **改了没**：该条涉及的章节 / 段落是否有对应修改
2. **实质回应了没**：评审意见的**实质诉求**是否被回应（不只看文字变化——防 Worker 博弈式表面应付，如换个近义词糊弄）
3. **有无引入新问题**：改动是否破坏了原有论证 / 数据 / 引文（底线对照 `../paper-workflow/references/quality-checklist.md` §四质量验收）

## 可用 Prompt（直接 spawn 循环）

```text
对 draft/paper.md 执行修改 Worker/Verifier 对抗循环。先 Read draft/paper.md 与
output/review-report.md，把后者的"修改路线图"(P1/P2/P3) 逐条展开为 checklist。

收敛规则：重试预算 N=2；Verifier 对每条给四态(已修复/部分修复/未修复/引入新问题)；
全"已修复"且无"引入新问题"才收敛；第 2 轮仍不通过 → 升级人工。

用 Agent 工具(subagent 模式，非 Agent Team)串行驱动：

1. spawn "worker"（Sonnet）— 按 checklist 逐条改 draft/paper.md，唯一写权。
   产出 output/revise/worker-round1.md 说明每条怎么改的。不评判自己改得好不好。

2. spawn "verifier"（Opus）— 独立读改后的 draft/paper.md + review-report.md，
   **不读 worker 说明**。对每条路线图项四态判定，重点核验"实质诉求是否被回应"
   (不只看文字变化，防表面应付) + "是否引入新问题"(对照 quality-checklist.md §四)。
   写 output/revise/verifier-round1.md，每条附证据(原文片段)。

3. 若未全通过：spawn worker(带 verifier-round1 反馈) 二改 → spawn verifier 二验。

4. 第 2 轮仍不通过 → 停，未通过项标记"需人工裁决"。

5. lead 汇总写 output/revise/revise-report.md：收敛通过项 / 人工裁决项(附双方论据)。
   收敛后重跑 validate_citations.py 与 verify_references.py --offline 确认引文未破坏。

Use Sonnet 4.5 for worker, Opus 4.6 for verifier. Cost: 每轮 1 Sonnet + 1 Opus 全文。
```

## 输出物

```
output/revise/
├── worker-round1.md       # Worker：每条路线图项怎么改的
├── verifier-round1.md     # Verifier：逐条四态 + 证据(原文片段)
├── worker-round2.md       # (如进入) 带反馈二改
├── verifier-round2.md
└── revise-report.md       # lead 汇总：收敛通过项 / 人工裁决项(双方论据) + validate/verify 结果
```

`verifier-roundN.md` 骨架：

```markdown
# Verifier 核验 Round N

| # | 优先级 | 路线图项 | 判定 | 证据(原文片段) | 备注 |
|---|--------|---------|------|---------------|------|
| 1 | P1 | (问题摘要) | 已修复/部分修复/未修复/引入新问题 | "..." | (理由) |
```

`revise-report.md` 是给作者的最终交付——人工裁决项需作者拍板后回 Stage 8 单 agent 落实，或与原评审人沟通。

## 与 paper-workflow 的关系

- **引用而非复制**（遵循架构决策）：核验对象（P1/P2/P3 路线图格式）引用 `../paper-review-team/references/review-template.md` §5；质量底线引用 `../paper-workflow/references/quality-checklist.md` §四。本 skill 只定义 Worker/Verifier 编排逻辑，不复制上述内容。
- **闭环**：`/paper-review-team`（Stage 7，找问题）→ `review-report.md` → `/paper-revise-loop`（Stage 8，改问题 + 验收）
- **集成点**：作为 Stage 8 的增强执行器 —— Stage 8 默认单 agent `/paper-workflow revise`（快、省），需严格验收时用 `/paper-revise-loop`。与 Stage 7 的双模式（单 agent / `/paper-review-team`）完全对称。

## 风险与克制

- **不做成"无限改到完美"**：N=2 后必须升级人。论文修改的最终裁决权在作者。
- **Verifier 不取代作者审美**：只核验"评审意见是否被实质回应"，不评判措辞好坏。
- **退化模式**：① Verifier 疲劳——N=2 循环短、每轮重读全文不依赖上轮记忆，风险低可接受；② Worker 博弈——Verifier 核验"实质诉求"而非"文字变化"，写进 prompt。

## 致谢

Worker/Verifier 对抗循环架构（收敛模型、死锁检测、升级路径、退化模式）来自 Agent 平台基础设施层研究，MiniMax Mavis 技术报告与 Anthropic Dynamic Workflows 失效模式分析。修改验收方法论基础引用自 `paper-workflow/references/peer-review-simulation.md`（源头见 paper-workflow 致谢）。
