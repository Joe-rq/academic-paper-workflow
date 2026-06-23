---
name: paper-review-team
description: 按论文类型组队的可插拔评审角色池（基础4：主编/方法论/领域/魔鬼代言人 + 按需统计/复现/伦理），独立 agent 并行评审 draft/paper.md，lead 汇总时做显式交叉验证与冲突裁决（多角色独立命中=高置信硬伤），输出修改路线图。用于论文质量验收、Stage 7 增强评审、需要严格多视角把关时。
argument-hint: '[论文路径，默认 draft/paper.md]'
user-invocable: true
allowed-tools: 'Read, Write, Edit, Bash, AskUserQuestion'
version: 1.1.0
---

# Paper Review Team — 论文同行评审多 agent 团队

## 解决什么问题

`paper-workflow` 的 Stage 7 按 `peer-review-simulation.md` 模拟评审，但有两个结构性短板：

1. **单 agent 串行扮演 = 伪独立**：同一上下文里演完主编再演魔鬼代言人，前面读论文形成的印象会污染后续判断，"多位独立评审人"只是名义上的。本 skill 升级为**真正独立的 agent 并行评审**（独立上下文、互不可见）。

2. **角色固定 + 无交叉验证**：固定 4 角色对医学 RCT 缺统计 / 伦理审稿人、对 CS 实验论文缺复现审稿人——最致命的问题往往只有对应专业角色才看得见。本 skill **按论文类型动态组队**（基础 4 + 按需专业角色），并在 lead 汇总时做**显式交叉验证**：同一问题被 ≥2 个互不可见独立上下文的角色命中 = 高置信硬伤。

> **依赖**：评审维度、角色池定义引用自 `../paper-workflow/references/peer-review-simulation.md`；交叉验证与冲突裁决方法论见 `references/conflict-detection.md`；产出格式见 `references/review-template.md`。本 skill 是方法论的**执行层**，不复制内容。若脱离本项目单独使用，需自带上述文档。

## 何时用

- 论文初稿完成、进入质量验收（对应 Stage 7）
- 需要严格的多视角把关（投稿前最后一道防线）
- 想要真正的对抗性评审，尤其是魔鬼代言人视角
- 论文有专业维度风险（统计 / 复现 / 伦理）→ 动态组队价值最大

## 何时不用

- 只想快速过一遍 → 用 `/paper-workflow review` 单 agent 即可，更快更省
- 论文还在大纲 / 片段阶段（先 `/paper-workflow outline` 或 `write`）
- 单节小修改 → 单 agent 评审足够

## 角色池（基础 4 + 按需 3）

| 角色 | 关注点 | 触发条件 | 模型 |
|------|--------|---------|------|
| `reviewer-eic` 主编 | 整体质量、创新性、期刊匹配度 | **必选** | Sonnet 4.5 |
| `reviewer-method` 方法论专家 | 研究设计、数据、分析方法 | **必选** | Sonnet 4.5 |
| `reviewer-domain` 领域专家 | 理论贡献、实践意义、文献覆盖 | **必选** | Sonnet 4.5 |
| `reviewer-devil` 魔鬼代言人 | 主动找弱点、拒稿理由 | **必选** | **Opus 4.6** |
| `reviewer-statistician` 统计审稿人 | 统计前提 / 效应量 / 样本量功效 / 多重比较 | 定量 / RCT / 计量论文 | Sonnet 4.5 |
| `reviewer-reproducibility` 复现审稿人 | 代码数据开放 / 实验可复跑 / 基准公平 | 含代码 / 数据论文 | Sonnet 4.5 |
| `reviewer-ethicist` 伦理审稿人 | IRB / 知情同意 / 数据保护 / 利益冲突 | 涉人体 / 动物研究 | Sonnet 4.5 |

各角色维度重点见 `../paper-workflow/references/peer-review-simulation.md`「评审团队」段。**文件所有权零重叠**：所有评审**只读** `draft/paper.md`，各自写 `output/reviews/{role}.md` → 满足 agent team 硬约束。

**模型选择理由**：常规评审 = well-defined 只读填表，Sonnet 够且省；魔鬼代言人 = 对抗性深度推理，Opus 更"刁钻"，是评审质量命门。

## 执行步骤

收到调用后，按以下步骤执行：

1. **读取背景**：`Read` 论文（默认 `draft/paper.md`）+ `project_context.md`（写作意图）
2. **组队判断**：lead 读论文，判断**学科 / 研究方法**，按下表组队，输出 `output/reviewer_set.json`
3. **（推荐）确认组队**：用 `AskUserQuestion` 把推荐的 `roles` 给作者确认 / 增删——组队错会浪费整轮评审 token
4. **并行 spawn**：按 `reviewer_set.roles` spawn 评审 teammate（delegate 模式，独立上下文，互不可见）；未选角色不 spawn
5. **等待全部完成**
6. **lead 汇总 + 交叉验证**：按 `references/conflict-detection.md` 做交叉验证（独立命中 → 置信度升级）与冲突裁决（分级 + 裁决），写入 `output/review-report.md`

### 组队规则表（步骤 2 依据）

| 论文特征 | 角色集 |
|---|---|
| 通用社科 / 教育 / 人文 | 基础 4 |
| 医学 / RCT / 涉人体研究 | 基础 4 + ethicist + statistician |
| CS / 计算 / 含代码数据 | 基础 4 + reproducibility |
| 计量 / 定量密集（非 RCT） | 基础 4 + statistician |

> 规则可叠加（如医学定量 RCT = 基础 4 + ethicist + statistician）。学科 / 方法判断**不依赖** `paper-config.json` 的文档体裁类型（journal-paper / thesis / essay 与组队无关），由 lead 当场读 draft 判断。
>
> **"定量密集"边界**：仅显式统计推断密集的论文（计量经济学 / 心理测量 / 多重回归建模 / 量表信效度分析）触发 statistician。普通准实验 / 问卷调查 / 案例研究的统计审查由方法论专家（methodologist）覆盖，不另加 statistician。

### `reviewer_set.json` 结构（步骤 2 产出）

```json
{
  "discipline": "临床医学",
  "method": "定量随机对照试验（RCT）",
  "roles": ["eic", "method", "domain", "devil", "ethicist", "statistician"],
  "role_rationale": {
    "ethicist": "涉人体研究，需核验 IRB / 知情同意 / 利益冲突",
    "statistician": "RCT 需核验随机化、样本量计算、统计前提"
  },
  "skipped": ["reproducibility"],
  "skip_rationale": {
    "reproducibility": "纯临床统计论文，无代码 / 数据集需开放复现"
  }
}
```

## 可用 Prompt（直接 spawn 团队）

```text
组建论文同行评审 agent team，对 draft/paper.md 做独立评审。

先 Read draft/paper.md（全文）和 project_context.md（写作意图）。

【组队】读论文判断学科 / 研究方法，按下表组队，写 output/reviewer_set.json：
  通用社科/教育/人文 → 基础4 (eic/method/domain/devil)
  医学/RCT/涉人体     → 基础4 + ethicist + statistician
  CS/含代码数据       → 基础4 + reproducibility
  计量/定量密集       → 基础4 + statistician
（规则可叠加）reviewer_set.json 含 roles/role_rationale/skipped/skip_rationale。
推荐用 AskUserQuestion 让作者确认 roles 后再 spawn。

方法论（角色/维度/决策）遵循
.claude/skills/paper-workflow/references/peer-review-simulation.md；
产出格式严格按 .claude/skills/paper-review-team/references/review-template.md。

按 reviewer_set.roles spawn 评审 teammate（delegate 模式，独立上下文，
互相不可见对方评审，确保真正独立）：

- reviewer-eic (Sonnet 4.5)：主编。整体质量、创新性、期刊匹配度。只读
  draft/paper.md，写 output/reviews/eic.md。
- reviewer-method (Sonnet 4.5)：方法论专家。研究设计、数据、分析方法。
  写 output/reviews/method.md。
- reviewer-domain (Sonnet 4.5)：领域专家。理论贡献、文献覆盖。写
  output/reviews/domain.md。
- reviewer-devil (Opus 4.6)：魔鬼代言人。主动找弱点、拒稿理由，务必尖锐
  具体可操作。写 output/reviews/devil.md。
- reviewer-statistician (Sonnet 4.5，按需)：统计前提/效应量/样本量功效/
  多重比较/缺失数据。重算关键统计量。写 output/reviews/statistician.md。
- reviewer-reproducibility (Sonnet 4.5，按需)：代码数据开放/实验可复跑/
  基准公平。写 output/reviews/reproducibility.md。
- reviewer-ethicist (Sonnet 4.5，按需)：IRB/知情同意/数据保护/利益冲突/
  试验注册号。写 output/reviews/ethicist.md。

全部完成后，由我(lead)汇总 + 交叉验证（遵循
references/conflict-detection.md）：对每个问题按命中角色数与命中方式定
置信度（≥2 独立上下文命中=🔴高置信硬伤）；对评价相反/建议矛盾/优先级
冲突分级(🔴🟡🟢)+裁决。生成修改路线图(P1/P2/P3)，写入
output/review-report.md。汇总遵循 peer-review-simulation.md Phase 2-3。

Use delegate mode. tmux layout: tiled.
```

## 输出物

```
output/
├── reviewer_set.json          # 组队决策（学科/方法/roles/rationale）
├── reviews/
│   ├── eic.md                 # 主编
│   ├── method.md              # 方法论专家
│   ├── domain.md              # 领域专家
│   ├── devil.md               # 魔鬼代言人（最尖锐）
│   ├── statistician.md        # 按需（定量 / RCT 论文）
│   ├── reproducibility.md     # 按需（代码 / 数据论文）
│   └── ethicist.md            # 按需（涉人体 / 动物研究）
└── review-report.md           # lead 汇总：交叉验证硬伤 + 冲突裁决 + 修改路线图
```

`review-report.md` 是给 Stage 8（`/paper-workflow revise` 或 `/paper-revise-loop`）的输入 —— Worker 按路线图逐项改，Verifier 核验改到位。交叉验证出的 🔴 高置信硬伤 = 验收时最该盯的项。

## 与 paper-workflow 的关系

- **引用而非复制**（遵循单一信息源原则）：评审方法论在 `peer-review-simulation.md`，交叉验证方法论在 `references/conflict-detection.md`，产出格式在 `references/review-template.md`；本 skill 只负责执行编排
- **解耦**：可独立 `/paper-review-team` 调用，不强制依赖 paper-workflow 命令链
- **集成点**：作为 Stage 7 的增强执行器 —— 想要更严格评审 + 专业维度覆盖时，用它替代默认的单 agent `review`

## 致谢

多 agent 独立评审设计的方法论基础来自 `paper-workflow/references/peer-review-simulation.md`（源头见 paper-workflow 致谢：academic-research-skills，Cheng-I Wu，CC BY-NC 4.0）；按类型动态组队 + 显式交叉验证 / 冲突裁决反移植自 EvoMap 黑客松项目 PaperSwarm 的 `structure` / `conflict` 节点（已用 med / cs / edu 三 run 验证）。
