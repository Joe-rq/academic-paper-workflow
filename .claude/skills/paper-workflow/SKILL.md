---
name: paper-workflow
description: 中文学术论文 AI 辅助写作工作流 - 10 阶段全生命周期（选题→投稿），融合四层元架构与 rhetorical moves
argument-hint: '[命令] [参数]'
user-invocable: true
allowed-tools: 'Read, Write, Edit, Bash, AskUserQuestion, CronCreate'
version: 1.0.0
---

# Paper Workflow — 中文学术论文写作工作流

## 核心架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                        四层元架构                                     │
├──────────────────────────────────────────────────────────────────────┤
│ Layer 1: 认知边界层 → 实体约束 + 来源标注规范 + 元反思检查点         │
│ Layer 2: 意图防护层 → 风格档案 + 三重防护 + 自我校验                 │
│ Layer 3: 执行可靠层 → 看门狗监控 + 引文校验 + 对齐验证               │
│ Layer 4: 持续优化层 → 模式积累 + 同类扫描 + 倍速测试                 │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 10 阶段工作流

```mermaid
graph LR
    S1[1.项目初始化] --> S2[2.头脑风暴]
    S2 --> S3[3.文献研究]
    S3 --> S4[4.大纲设计]
    S4 --> S5[5.分节写作]
    S5 --> S6[6.图表制作]
    S6 --> S7[7.同行评审]
    S7 --> S8[8.修改迭代]
    S8 --> S9[9.构建输出]
    S9 --> S10[10.归档定稿]
```

| Stage | 命令 | 功能 | 输出物 | 参考文档 |
|-------|------|------|--------|---------|
| 1 | `init` | 从模板创建论文项目 | 项目目录 + paper-config.json | — |
| 2 | `brainstorm` | 34问结构化框架 | project_context.md | `brainstorming-guide.md` |
| 3 | `research` | 文献研究与综述 | refs/ + 文献笔记 | `deep-research-guide.md` |
| 4 | `outline` | 生成论文大纲 | draft/paper.md 骨架 | `writing-workflow.md` |
| 5 | `write` | 按 rhetorical moves 逐节写作 | 完整初稿 | `section-rhetorical-moves/` |
| 6 | `figures` | matplotlib 图表生成 | figures/*.png | — |
| 7 | `review` | 同行评审 + AI 检测 | 评审报告 | `peer-review-simulation.md`, `ai-pattern-detection.md` |
| 8 | `revise` | 根据评审意见修改 | 修改稿 | `quality-checklist.md` |
| 9 | `build` | md→docx + 交叉引用 + TOC | 投稿格式 .docx | — |
| 10 | `archive` | 版本快照 | _archive/vN/ | — |

### 辅助命令

| 命令 | 功能 | 说明 |
|------|------|------|
| `status` | 显示项目状态和当前阶段 | 读取 paper-config.json |
| `doctor` | 检查项目文件完整性 | 验证脚本和参考文档是否齐全 |
| `validate` | 引文编号校验 | 检测缺失/未引用的文献（快、离线） |
| `verify` | 参考文献防伪造校验 | 格式合规 + 存在性验证，检测 AI 编造文献（`verify_references.py`） |
| `build-ppt` | 生成答辩 PPT | 调用 slides/compile.js |
| `watchdog` | 进度监控与对齐验证 | Layer 3 看门狗 |

> `validate` 与 `verify` 分工：`validate` 查引文**编号**一致性（快、离线，build 前置）；
> `verify` 查参考文献**真实性**（格式 + 是否真实存在，检测编造，评审阶段用）。

---

## 完整使用流程

### Stage 1: 项目初始化

```bash
/paper-workflow init -n "论文标题" -t journal-paper -a "作者" -j "目标期刊"
```

参数说明：
- `-n, --name`: 论文标题（必填）
- `-t, --type`: 论文类型，可选 `journal-paper` / `thesis` / `essay`（默认 journal-paper）
- `-a, --author`: 作者姓名
- `-j, --journal`: 目标期刊/学校
- `-w, --words`: 目标字数（默认 8000）

**执行动作**：
1. 复制 `templates/{type}/` 到目标目录
2. 生成 `paper-config.json`
3. 创建 `draft/`、`refs/`、`figures/`、`output/` 目录

### Stage 2: 头脑风暴

```bash
/paper-workflow brainstorm
```

**执行动作**：交互式引导用户回答 34 问结构化框架，生成 `project_context.md`。

问题分为 6 个阶段：
1. 问题发现（Q1-7）：领域问题、智力缺口
2. 贡献结晶（Q8-13）：核心主张、证据映射
3. 评估设计（Q14-20）：实验方案
4. 定位与框架（Q21-25）：目标场域、竞争定位
5. 架构与约束（Q26-31）：设计决策、范围约束
6. 叙事主线（Q32-34）：故事弧线

> 详细问题见 `references/brainstorming-guide.md`

### Stage 3: 文献研究

```bash
/paper-workflow research "[研究主题]"
```

**执行动作**：按 `references/deep-research-guide.md`（方法论）+ `references/academic-search-guide.md`（API 检索实操）进行文献研究。

**方法论概要**（详见 `references/deep-research-guide.md`）：
1. 界定研究范围 → 提取关键词、确定检索源
2. 系统检索 → OpenAlex/Semantic Scholar API（英文+部分中文核心刊）+ 知网/万方（中文，人工）
3. 分级阅读 → L1精读(5-8篇) + L2泛读(10-15篇) + L3浏览
4. 文献矩阵 → 按维度整理核心文献
5. 缺口分析 → 识别方法/对象/视角/时间缺口
6. 综述撰写 → 3-Move 模式（类别聚类→逐类局限→定位句）

> **检索实操**：`references/academic-search-guide.md` 给出 OpenAlex / Semantic Scholar / Crossref 的
> 可直接调用 API（curl 示例）、数据库选型表、标识符互转，以及**中文文献覆盖的诚实说明**
> （知网/万方无 API，需人工检索）。**铁律**：任何 AI 生成的参考文献，必须经数据库检索确认存在后方可引用。

**输出物**：
- `refs/` 目录下的文献笔记
- 文献综述文本
- 引用信息（作者、标题、年份、DOI）

### Stage 4: 大纲设计

```bash
/paper-workflow outline
```

**执行动作**：
1. 读取 project_context.md 和文献笔记
2. 根据论文类型选择框架模板（问题解决型/案例分析型/经验总结型/比较研究型/理论建构型）
3. 生成论文骨架到 `draft/paper.md`
4. 用户确认后锁定大纲

**框架类型决策**：
```
论文主要做什么？
├─ 提出新方法/新路径 → 问题解决型
├─ 深度分析一个案例 → 案例分析型
├─ 总结实践经验 → 经验总结型
├─ 对比两种做法 → 比较研究型
└─ 提出新理论框架 → 理论建构型
```

### Stage 5: 分节写作

```bash
/paper-workflow write          # 交互式逐节写作
/paper-workflow write --section introduction  # 写特定节
```

**执行动作**：按 rhetorical moves 逐节写作，每节完成后用户确认。

**各节写作指南**（详见 `references/section-rhetorical-moves/`）：

| 节 | Rhetorical Moves | 要点 |
|----|-----------------|------|
| 摘要 | 问题→方法→过程→结论 | 200-300字，含关键词 |
| 引言 | 利益→问题缺口→核心抽象→设计直觉→贡献→结果预览 | 6-Move 序列 |
| 文献综述 | 类别聚类→逐类局限→定位句 | 定位工具，不是综述 |
| 方法/设计 | 抽象引入→设计论证→组件架构→关键决策→鲁棒性 | 先抽象后实现 |
| 结果/评估 | 设置→头对头→深入分析→要点综合→消融→鲁棒性 | 证据驱动 |
| 讨论 | 回答研究问题→理论贡献→实践意义→局限→未来方向 | 诚实且精确 |

**写作原则**（来源标注规范，详见 `references/evidence-labeling.md`）：
- `原文/已有数据`：直接引用的原始内容
- `用户确认内容`：用户明确提供的信息
- `根据上下文推断`：基于已有信息推断的内容
- `建议性扩展`：AI 建议的扩展内容

### Stage 6: 图表制作

```bash
/paper-workflow figures
```

**执行动作**：运行 `figures/generate_figures.py` 生成论文图表。

**图表规范**：
- 分辨率：300dpi
- 尺寸：1800×1200px（标准），可按需调整
- 字体：SimHei（中文标题）+ SimSun（中文正文）+ Arial（英文）
- 配色：低饱和度，灰度安全

### Stage 7: 同行评审

```bash
/paper-workflow review
```

> **多 agent 增强**：默认是单 agent 依次扮演 4 角色评审。如需 4 个真正独立的评审 agent 并行评审（突破"伪独立"），改用 `/paper-review-team`（独立 skill，详见 `.claude/skills/paper-review-team/`）。

**执行动作**：
1. 按照 `references/peer-review-simulation.md` 模拟 4 角色评审（主编/方法论专家/领域专家/魔鬼代言人）
2. 按 7 维度检查表逐项评审
3. 按照 `references/ai-pattern-detection.md` 检测 22 种 AI 写作模式
4. **参考文献防伪造**：运行 `verify`（`verify_references.py`）——格式合规 + 存在性验证，检出 AI 编造文献
5. 生成评审报告和修改路线图

> **文献真实性检查（防编造）**：`verify_references.py` 做两道检查：
> - **Check A 格式合规**（离线确定性）：GB/T 7714 五阶段解析，检出缺类型标签/年份越界/DOI 格式错等 AI 编造痕迹
> - **Check B 存在性验证**（在线分层）：带 DOI 的查 Crossref（DOI↔题名不符 = 最强防伪造信号，疑似张冠李戴/缝合）；无 DOI 的查 OpenAlex；中文期刊未收录标"需人工核实"（建议知网/万方），**不误判为编造**；政策/标准 `[S]`/`[Z]` 跳过
>
> 诚实的天花板：纯中文无 DOI 文献的完全编造无法机器检测，需人工知网核实。详见 `references/academic-search-guide.md` §8。

### Stage 8: 修改迭代

```bash
/paper-workflow revise
```

**执行动作**：
1. 读取评审报告
2. 按优先级排序修改项
3. 逐项修改并记录变更
4. 修改完成后重新验证

### Stage 9: 构建输出

```bash
/paper-workflow build                      # md→docx
/paper-workflow build --with-crossrefs      # 含交叉引用
/paper-workflow build-ppt                   # 生成答辩 PPT
```

**执行动作**：
1. 读取 `paper-config.json` 获取元数据
2. 调用 `scripts/build_academic_docx.py` 进行学术格式转换
3. 可选调用 `scripts/build_crossrefs.py` 添加交叉引用
4. 输出到 `output/` 目录

**输出格式规范**：
- 页面：A4 (21×29.7cm)
- 字体：宋体（中文）+ Times New Roman（英文）
- 标题：黑体 16pt(H1) / 15pt(H2) / 14pt(H3)
- 正文：宋体 12pt，1.5倍行距
- 参考文献：GB/T 7714-2015 格式
- 页码：前置部分罗马数字，正文阿拉伯数字

### Stage 10: 归档定稿

```bash
/paper-workflow archive -m "版本说明"
```

**执行动作**：
1. 快照当前版本到 `_archive/vN/`
2. 更新 paper-config.json 中的版本号
3. 生成版本变更记录

---

## 四层元架构详解

### Layer 1: 认知边界层

**实体约束**：
- 单次处理素材 ≤4 个
- 核心论点 ≤4 条
- 关键词 ≤5 个
- 参考文献首次引用排序

**来源标注规范**：所有内容必须标注信息层级（见 `references/evidence-labeling.md`）

**元反思检查点**：每阶段完成后自检 6 个问题：
1. 我是否理解了用户的真实意图？
2. 是否存在隐含假设？
3. 输出是否在约束范围内？
4. 是否偏离了原始目标？
5. 质量是否达到该阶段标准？
6. 下一步是否明确？

### Layer 2: 意图防护层

**三重防护**：
- 第一重（输入验证）：检查 paper-config.json、project_context.md 是否存在
- 第二重（执行监控）：限制每节输出 ≤3000 字，引用密度 ≥1个/段
- 第三重（输出标准）：生成前明确质量标准

### Layer 3: 执行可靠层

**看门狗机制**：
```bash
/paper-workflow watchdog
# 输出：进度检查 + 下一步行动 + 对齐验证结果
```

**引文校验**：
```bash
/paper-workflow validate
# 检测：缺失引用、未引用文献、编号不一致
```

### Layer 4: 持续优化层

**模式积累**：每完成一篇论文，提取写作模式到 `~/memory/patterns/`

**同类扫描**：新项目启动时扫描已有模式库

---

## 目录结构

```
论文项目目录/
├── paper-config.json        # 项目配置
├── project_context.md       # 头脑风暴产出（Stage 2）
├── draft/
│   └── paper.md             # 论文主稿（唯一源文件）
├── refs/                    # 参考文献（PDF + 笔记）
├── figures/
│   └── generate_figures.py  # 图表生成脚本
├── slides/
│   ├── compile.js           # PPT 编译脚本
│   └── slide-*.js           # 各页模块
├── output/                  # 构建产物（.docx）
└── _archive/                # 版本归档
    ├── v1/
    ├── v2/
    └── ...
```

---

## paper-config.json 结构

```json
{
  "title": "论文标题",
  "subtitle": "副标题（如有）",
  "author": "作者姓名",
  "affiliation": "单位",
  "target": "目标期刊/学校",
  "type": "journal-paper",
  "word_count": 8000,
  "citation_style": "GB/T 7714-2015",
  "version": 1,
  "build": {
    "input": "draft/paper.md",
    "output_dir": "output/",
    "crossrefs": true,
    "toc": true
  }
}
```

---

## 参考文档

| 文档 | 路径 | 用途 |
|------|------|------|
| 头脑风暴指南 | `references/brainstorming-guide.md` | Stage 2 交互式引导 |
| 学术文献检索 | `references/academic-search-guide.md` | Stage 3 API 检索实操 + 中文覆盖说明 |
| 各节写作语步 | `references/section-rhetorical-moves/` | Stage 5 分节写作参考 |
| 来源标注规范 | `references/evidence-labeling.md` | 全程信息层级标注 |
| 质量检查清单 | `references/quality-checklist.md` | Stage 7-8 质量验收 |
| 写作方法论 | `references/writing-workflow.md` | 6 阶段写作流程 |
| 动态工作流指引 | `references/dynamic-workflows.md` | 何时启用 Claude Code 动态工作流（ultracode / 6 模式 × 阶段映射） |

---

## 脚本清单

| 脚本 | 路径 | 功能 |
|------|------|------|
| 初始化项目 | `scripts/init_project.py` | 从模板创建论文项目 |
| 构建 DOCX | `scripts/build_academic_docx.py` | md→docx 学术格式转换（内置） |
| 构建 DOCX | `scripts/build_docx.py` | md→docx 构建协调器 |
| 交叉引用 | `scripts/build_crossrefs.py` | 注入引文超链接 |
| 引文校验 | `scripts/validate_citations.py` | 检测引文**编号**问题（快、离线） |
| 参考文献防伪造 | `scripts/verify_references.py` | 格式合规 + 存在性验证，检测 AI 编造文献 |
| 学术数据库查询 | `scripts/_academic_db.py` | OpenAlex/Crossref/S2 查询、题名相似度、GB/T 7714 归一化（共享模块） |
| 版本归档 | `scripts/archive_version.py` | 快照当前版本 |

---

## 致谢与版权声明

本项目在设计过程中参考了以下开源项目，感谢作者的公开贡献：

| 项目 | 作者 | 协议 | 本项目借鉴内容 |
|------|------|------|--------------|
| [codex-claude-academic-skills](https://github.com/zLanqing/codex-claude-academic-skills) | zLanqing | **MIT** | brainstorming-guide（34问框架→中文适配）、section rhetorical moves（6节写作语步→教育/社科适配）、evidence labeling（来源标注规范）、paper-lookup（学术数据库 API 参考→academic-search-guide.md） |
| [academic-research-skills](https://github.com/Imbad0202/academic-research-skills) | Cheng-I Wu | **CC BY-NC 4.0** | deep-research 文献研究方法论、academic-paper 写作流程、academic-paper-reviewer 评审维度、contamination_signals（参考文献防伪造验证方法论→verify_references.py 的分层验证设计） |
| [Humanizer-zh](https://github.com/op7418/Humanizer-zh) | 歸藏 | MIT | 22种中文 AI 写作模式检测与消除 |

**协议要求**：
- MIT 项目：已保留版权声明，允许自由使用和修改
- CC BY-NC 4.0 项目：已署名原作者，本项目为非商业教研用途
