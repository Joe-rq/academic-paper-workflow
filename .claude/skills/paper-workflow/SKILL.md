---
name: paper-workflow
description: 中文学术论文 AI 辅助写作编排器 - 10 阶段全生命周期（选题→投稿），自有阶段直接执行，重能力阶段委托外部 skill，融合四层元架构与 rhetorical moves
argument-hint: '[命令] [参数]'
user-invocable: true
allowed-tools: 'Read, Write, Edit, Bash, AskUserQuestion, CronCreate'
version: 1.1.0
---

# Paper Workflow — 中文学术论文写作编排器

## 定位

本 skill 是**编排器**，不是全能执行体：串联 10 阶段，**自有阶段**（init/brainstorm/outline/figures/build/revise/archive + validate/verify）直接执行，**能力域阶段**（research/write/review）委托外部 skill（见路由表"实现"列）。不重复外部 skill 或 `scripts/` 已实现的能力——这是单一信息源原则。

## 核心架构：四层元架构

```
Layer 1 认知边界 → 实体约束 + 来源标注 + 元反思检查点
Layer 2 意图防护 → 输入验证 + 执行监控 + 输出标准
Layer 3 执行可靠 → 看门狗 + 引文校验 + 对齐验证
Layer 4 持续优化 → 模式积累 + 同类扫描
```

## 10 阶段路由

| Stage | 命令 | 功能 | 输出物 | 实现 |
|---|---|---|---|---|
| 1 | `init` | 从模板创建项目 | 项目目录 + paper-config.json | 自有 `init_project.py` |
| 2 | `brainstorm` | 34问结构化框架 | project_context.md | 自有，见 `brainstorming-guide.md` |
| 3 | `research` | 文献研究 | refs/ + 文献笔记 | **委托 `/deep-research`**，方法见 `deep-research-guide.md` |
| 4 | `outline` | 论文大纲 | draft/paper.md 骨架 | 自有，见 `writing-workflow.md` |
| 5 | `write` | 逐节写作 | 完整初稿 | **委托 `/academic-paper`**，语步见 `section-rhetorical-moves/` |
| 6 | `figures` | 图表生成 | figures/*.png | 自有 `generate_figures.py` |
| 7 | `review` | 同行评审 + AI 检测 | 评审报告 | 单 agent 自有 / 多 agent `/paper-review-team`；防伪造 `verify` |
| 8 | `revise` | 按评审修改 | 修改稿 | 自有，见 `quality-checklist.md` |
| 9 | `build` | md→docx + 交叉引用 | output/*.docx | 自有 `build_academic_docx.py` |
| 10 | `archive` | 版本快照 | _archive/vN/ | 自有 `archive_version.py` |

### 辅助命令

| 命令 | 功能 |
|---|---|
| `status` | 读 paper-config.json 显示当前阶段 |
| `doctor` | 检查脚本/参考文档/外部 skill 依赖完整性 |
| `validate` | 引文**编号**校验（快、离线，build 前置） |
| `verify` | 参考文献**真实性**校验（格式 + 存在性，检测 AI 编造，评审用） |
| `build-ppt` | 生成答辩 PPT（`slides/compile.js`） |
| `watchdog` | Layer 3 进度监控 + 对齐验证 |

> **`validate` vs `verify`**：`validate`（`validate_citations.py`）查引文编号一致性；`verify`（`verify_references.py`）查参考文献真实性——Check A 格式合规（GB/T 7714 解析）+ Check B 存在性（Crossref/OpenAlex 在线核验）。中文无 DOI 文献无法机器完全检测，需人工知网核实。

## 各阶段执行要点

### Stage 1 init
`/paper-workflow init -n "标题" -t journal-paper -a "作者" -j "期刊" -w 8000`
- `-t`：`journal-paper`/`thesis`/`essay`（默认 journal-paper）
- 动作：复制 `templates/{type}/` → 生成 paper-config.json → 建 draft/refs/figures/output/

### Stage 2 brainstorm
交互引导 34 问（6 阶段：问题发现 / 贡献结晶 / 评估设计 / 定位框架 / 架构约束 / 叙事主线），产 project_context.md。问题清单见 `brainstorming-guide.md`。

### Stage 3 research
委托 `/deep-research "主题"`。检索实操（OpenAlex / Semantic Scholar / Crossref API + 中文知网人工）见 `academic-search-guide.md`。**中文文献发现可选增强**：在客户端配置秘塔 MCP（远程 HTTP，需自行申请 API Key），用 `metaso_web_search` 的 `paper` scope 补国际库覆盖盲区——安装与边界见 `academic-search-guide.md` §9。**铁律：AI 生成的参考文献必须经数据库确认存在后方可引用。**

### Stage 4 outline
读 project_context.md + 文献笔记 → 选框架（问题解决 / 案例分析 / 经验总结 / 比较研究 / 理论建构）→ 生成 draft/paper.md 骨架 → 用户确认锁定。见 `writing-workflow.md`。

### Stage 5 write
委托 `/academic-paper`，按 rhetorical moves 逐节写作，各节语步见 `section-rhetorical-moves/`。**来源标注**（`evidence-labeling.md`）：`原文/已有数据`、`用户确认内容`、`根据上下文推断`、`建议性扩展`。

### Stage 6 figures
跑 `figures/generate_figures.py`（300dpi、中文 SimHei/SimSun、低饱和灰度安全；规范由脚本内置）。

### Stage 7 review
- 默认单 agent 按 `peer-review-simulation.md` 模拟 4 角色（主编 / 方法论 / 领域 / 魔鬼代言人）+ 7 维度 + `ai-pattern-detection.md` 22 模式
- 需真独立对抗评审 → `/paper-review-team`（4 独立 agent 并行）
- **必跑** `verify` 防伪造

### Stage 8 revise
读评审报告 → 按优先级逐项改 → 改完重跑 `validate`/`verify`。验收见 `quality-checklist.md`。

### Stage 9 build
```
/paper-workflow build [--with-crossrefs]
```
调 `build_academic_docx.py --input draft/paper.md --output output/xxx.docx`（学术投稿格式：A4 / 宋体+Times New Roman / 黑体标题 / GB/T 7714 / 页码分段，规范由脚本实现）；`--with-crossrefs` 再调 `build_crossrefs.py` 注入 [n]→参考文献跳转。PPT 另用 `build-ppt`。

### Stage 10 archive
`/paper-workflow archive -m "版本说明"` → 快照到 `_archive/vN/` + 更新 config 版本号。

## 全局约束（四层架构落地）

**实体约束（L1）**：单次素材 ≤4、核心论点 ≤4、关键词 ≤5、参考文献首次引用排序。

**来源标注（L1）**：所有内容标注 4 级信息层级（`evidence-labeling.md`）。

**元反思检查点（L1）**：每阶段完成后自检——真实意图？隐含假设？约束内？偏离目标？质量达标？下一步明确？

**三重防护（L2）**：输入验证（config/context 是否存在）→ 执行监控（每节 ≤3000 字、引用密度 ≥1/段）→ 输出标准（生成前明确）。

**看门狗（L3）**：`/paper-workflow watchdog` → 进度 + 下一步 + 对齐验证。

## 项目结构约定

```
论文项目/
├── paper-config.json     # 元数据（见下）
├── project_context.md    # brainstorm 产出（Stage 2）
├── draft/paper.md        # 唯一源文件
├── refs/                 # 参考文献 PDF + 笔记
├── figures/generate_figures.py
├── slides/               # 答辩 PPT（compile.js + slide-*.js）
├── output/               # 构建产物
└── _archive/vN/          # 版本归档
```

paper-config.json：
```json
{
  "title": "", "subtitle": "", "author": "", "affiliation": "",
  "target": "目标期刊/学校", "type": "journal-paper",
  "word_count": 8000, "citation_style": "GB/T 7714-2015", "version": 1,
  "current_stage": "init",
  "stages": { "init": "done@2025-06-14T10:30Z" },
  "build": { "input": "draft/paper.md", "output_dir": "output/", "crossrefs": true, "toc": true }
}
```

**阶段进度追踪**：`current_stage` 记录当前所在阶段；`stages` 记录每阶段的完成状态（`done@ISO时间` / `in_progress` / `skipped`）。**每阶段完成时，执行者（脚本或 AI）必须更新这两个字段**——这是 L3 对齐验证的硬信号。`status` 命令读取并展示。

## 脚本与参考文档

脚本（`scripts/`，`uv run python scripts/X.py`）：

| 脚本 | 用途 |
|---|---|
| `init_project.py` | Stage 1 初始化 |
| `build_academic_docx.py` | Stage 9 md→学术 docx（主） |
| `build_docx.py` | md→docx 协调器（委托 md-to-docx） |
| `build_crossrefs.py` | 引文交叉引用注入 |
| `validate_citations.py` | 引文编号校验（validate） |
| `verify_references.py` | 参考文献防伪造（verify） |
| `_academic_db.py` | 共享：OpenAlex/Crossref/S2 查询 + GB/T 7714 归一化 |
| `archive_version.py` | Stage 10 归档 |

参考文档（`references/`）：

| 文档 | 用于 |
|---|---|
| `brainstorming-guide.md` | Stage 2 |
| `academic-search-guide.md` / `deep-research-guide.md` | Stage 3 |
| `writing-workflow.md` | Stage 4 |
| `section-rhetorical-moves/` | Stage 5 |
| `evidence-labeling.md` | 全程来源标注 |
| `peer-review-simulation.md` / `ai-pattern-detection.md` | Stage 7 |
| `quality-checklist.md` | Stage 7-8 |
| `dynamic-workflows.md` | 何时启用 Claude Code 动态工作流 |

---

> 致谢、融合设计与论文类型说明见仓库 `README.md`。
