# 动态工作流（Dynamic Workflows）使用指引

> 本文档指导本项目**何时、如何**启用 Claude Code 动态工作流。它只给方法论与阶段映射，不提供脚本本身——脚本由 Claude 在运行时按任务即时生成（这正是"动态"的含义）。
>
> 方法论信息源：`D:\AI-resource` 研究库的两篇 summary（见文末）。

## 一、这是什么

Claude Code v2.1.154+ 的研究预览功能：任务描述后，Claude **自动生成一个 JS 脚本**，在隔离 runtime 里大规模编排子代理，主对话只收最终结果。

与本项目内置的 `paper-review-team`（agent team）的根本区别——**编排器是谁**：

| 维度 | agent team（paper-review-team） | 动态 workflow |
|------|--------------------------------|---------------|
| 谁决定下一步 | lead 逐轮协调 | **脚本** |
| 中间结果 | 共享任务列表 | 脚本变量，不进主上下文 |
| 可重跑 | 否 | **编排本身可版本化、可重放** |
| 规模 | 几个 teammate | 数十~数百子代理 |

一句话决策：**需要"角色互动 + 互相通信"用 agent team；需要"可重复质量模式 + 大规模扇出"用 workflow。** 二者互补，不冲突。

## 二、为什么要用：三种失效模式

单 agent 在长任务上会**结构性失效**，这正是写长论文（尤其 thesis 3 万字+）的痛点，也是 workflow 的存在理由：

| 失效模式 | 本项目表现 | workflow 如何防 |
|---------|-----------|---------------|
| **Agentic laziness**（偷懒） | Stage 5 写长稿漏节、Stage 7 评审只查部分维度、Stage 8 改几条就宣布完成 | 把每项拆给独立 subagent，结构上无法跳过 |
| **Self-preferential bias**（自评偏向） | Stage 7 单 agent 评审自己写的论文会手软 | adversarial verification——另一独立 agent 验证（`paper-review-team` 已部分解决） |
| **Goal drift**（目标漂移） | Stage 5 多轮 compaction 丢失"别写 X"约束、Stage 8 多轮修改偏离原始研究问题 | 每个 subagent 有独立、聚焦目标，不受主对话漂移影响 |

## 三、六种编排模式 × 本项目阶段

| 编排模式 | 机制 | 适用阶段 | 怎么用 |
|---------|------|---------|--------|
| **Fan-out-and-synthesize** | 多角度扇出 → barrier 等齐 → 汇总 | Stage 3 文献研究 | 多角度检索 → 交叉验证 → 综述（对标内置 `/deep-research`） |
| **Adversarial verification** | 每个输出配独立验证 agent | Stage 7 评审 | 4 角色评审之上再加独立 verifier（魔鬼代言人即此模式） |
| **Loop until done** | 无固定次数，按停止条件循环 | Stage 7-8 评审-修改 | 评审 → 定位问题 → 逐项修改 → 重测，直到过质量门槛 |
| **Generate-and-filter** | 批量生成 → rubric 筛选 → 去重 | Stage 5 写作 | 一节生成多版本草稿 → 按 rhetorical moves rubric 选最优 |
| **Tournament** | 多方案 pairwise 竞争 | Stage 2 选题 / Stage 4 框架 | 多个候选选题/框架两两比较，比绝对打分更稳 |
| **Classify-and-act** | 分类器路由 | Stage 4 框架决策 | 现有框架决策树可升级为路由 workflow |

**最高价值的两个切入点**：
1. **Stage 7-8 评审-修改对抗循环**（Loop + Adversarial）—— 质量命门，直接对抗 laziness / goal drift
2. **Stage 3 文献综述**（Fan-out + Adversarial）—— 多角度检索 + 交叉验证，引文质量更硬

## 四、何时触发

三种入口：

1. **关键词**：prompt 含 `ultracode:`（v2.1.160 之前为 `workflow`）
   ```text
   ultracode: 对 draft/paper.md 跑 4 角色评审，每个 P1 问题独立 spawn 修改 agent，改完重评直到无 P1
   ```
2. **模式**：`/effort ultracode`，本会话每个实质任务自动规划 workflow（配合 `xhigh` 推理努力）
3. **已保存命令**：内置 `/deep-research`，或自己保存的 `/<name>`（运行后按 `s` 存到 `.claude/workflows/`）

## 五、何时不该用

- **确定性脚本阶段**：init / figures / build / archive —— 用 workflow 是杀鸡用牛刀，违反最简优先
- 启动前自问 **"does it really need more compute?"** —— 常规单节修改、单次评审，单 agent 或 `paper-review-team` 足够
- workflow 比对话内处理**更费 token**（生成大量子代理）；大型任务前先在小范围（一个章节、一个狭窄问题）试跑

## 六、前置条件与硬限制

- **版本**：Claude Code v2.1.154+
- **并发**：最多 16 个并发子代理；单次运行最多 1,000 个
- **模型**：子代理沿用会话模型 —— Tournament / Adversarial 这类需要强推理的模式，在弱模型上效果打折
- **无中途输入**：阶段间需用户签认时，把每个阶段拆成独立 workflow
- 子代理在 `acceptEdits` 模式运行，文件编辑自动批准；Shell / 网络获取仍可能提示，长运行前预先加入允许列表

## 七、信息源

本指引提炼自 `D:\AI-resource` 研究库的两篇 summary：

- `wiki/summaries/12-a-harness-for-every-task-dynamic-workflows.md` — Anthropic 官方动态工作流深度解读（3 失效模式 + 6 编排模式 + 10 用例 + Quarantine 安全模式）
- `wiki/summaries/10-claude-code-dynamic-workflows.md` — Claude Code 动态工作流官方功能文档（触发 / 运行机制 / 保存复用 / 运行管理）
