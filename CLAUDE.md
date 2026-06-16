# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 这个仓库是什么

**不是应用程序，是中文学术论文 AI 辅助写作的 skill 框架。** "代码"由四部分组成：

- `.claude/skills/paper-workflow/SKILL.md` — 10 阶段工作流定义，作为 `/paper-workflow` 斜杠命令暴露给论文作者
- `.claude/skills/paper-workflow/scripts/*.py` — init / 构建 / 校验脚本（被 SKILL.md 调用）
- `.claude/skills/paper-review-team/` — Stage 7 的多 agent 评审 skill（独立可调用）
- `.claude/skills/paper-revise-loop/` — Stage 8 的多 agent 修改验收 skill（Worker/Verifier 对抗循环，独立可调用）
- `templates/{journal-paper,thesis,essay}/` — 论文项目模板
- `references/*.md` — 写作知识库（头脑风暴、检索实操、各节写作语步、评审、AI 模式检测）

**两种视角**：终端用户通过 `/paper-workflow <stage>` 写论文（用法见 `README.md`）；在此仓库工作 = 维护框架本身（改 SKILL.md / 脚本 / 模板 / 知识库）。

## 架构（关键设计）

- **Markdown 是唯一源文件**：论文写为 `draft/paper.md`，经脚本转 docx。格式与内容分离，diff 可读。
- **引用而非复制**：工作流各阶段委托给**外部** skill（`deep-research`/`academic-paper`/`academic-paper-reviewer`/`md-to-docx`/`humanizer-cn`，经 42plugin 安装）。本仓库只提供编排 + 三个内置 skill（`paper-workflow` 编排器 + `paper-review-team` 评审 + `paper-revise-loop` 修改验收）。改某阶段行为前先确认它是否实际跑在外部 skill 里。
- **单一信息源**：`paper-review-team` 的评审方法论引用 `paper-workflow/references/peer-review-simulation.md`，自身不复制。改评审逻辑时两处都要看。
- **四层元架构**（认知边界/意图防护/执行可靠/持续优化）是 SKILL.md 内对工作流阶段的约束，不是运行时代码——别去找它的实现。

## 命令

### 开发（维护本框架时）

```bash
uv sync                    # 安装依赖（python-docx, matplotlib, pillow；dev: ruff）
uv run ruff check .        # lint
uv run ruff format .       # 格式化

# 跑单个脚本：脚本自身目录会自动进 sys.path，裸 import _academic_db / validate_citations 可用
uv run python .claude/skills/paper-workflow/scripts/init_project.py --name "测试标题" -t journal-paper -o ./_scratch
uv run python .claude/skills/paper-workflow/scripts/validate_citations.py --input <paper>/draft/paper.md
uv run python .claude/skills/paper-workflow/scripts/verify_references.py --input <paper>/draft/paper.md --offline   # 仅格式校验，离线
uv run python .claude/skills/paper-workflow/scripts/verify_references.py --input <paper>/draft/paper.md             # 含在线存在性验证

# PPT 编译（可选，独立 Node 工具链）
cd templates/journal-paper/slides && npm install && node compile.js
```

**无单元测试套件**。脚本的验证方式 = 在一篇示例论文上跑 `doctor` / `validate` / `verify` 看输出正确。改脚本时带上一个真实/示例 `paper.md` 做冒烟测试。

### 工作流（终端用户，在 Claude Code 内）

`/paper-workflow <stage>`，10 阶段：`init → brainstorm → research → outline → write → figures → review → revise → build → archive`。辅助命令：`status`、`doctor`（依赖检查）、`validate`、`verify`、`build-ppt`、`watchdog`。`/paper-review-team` = Stage 7 多 agent 评审执行器；`/paper-revise-loop` = Stage 8 多 agent 修改验收执行器（Worker/Verifier 对抗循环）。**完整命令表与参数见 `SKILL.md`，勿在此重复。**

## 关键约定

- **`validate` ≠ `verify`**：`validate`（`validate_citations.py`）查引文**编号**一致性，快、离线，build 前置；`verify`（`verify_references.py`）查参考文献**真实性**（GB/T 7714 格式合规 + 数据库存在性），检测 AI 编造，评审阶段用。`verify_references.py` 内部复用 `validate_citations.validate`。
- **脚本共享模块**：`_academic_db.py`（OpenAlex/Crossref/S2 查询、题名相似度、GB/T 7714 归一化）被 `verify_references.py` 等裸 import 复用。新校验脚本沿用同一模块，勿重复实现数据库查询。
- **扩展点**：新论文类型 → `templates/`；新写作语步 → `references/section-rhetorical-moves/`；新构建/校验脚本 → `scripts/` 并在 `SKILL.md` 命令表注册；新阶段委托 → `SKILL.md` 技能集成表加行。

## 中文文献检索与获取短板（用户引导职责）

`_academic_db.py` 走 OpenAlex/Crossref/S2 三库，**以英文为主**；知网/万方/维普无开放 API，闭源 CSSCI 全文也不可程序化检索。这是本框架在中文文献场景下的**结构性短板**，无法靠改代码补齐。

两个补丁都是**用户侧可选配置**，本仓库不预装、不通过代码强制依赖：

| 补丁 | 解决什么 | 位置 | 形态 |
|------|---------|------|------|
| **秘塔 MCP** | 中文文献**发现** | 用户 `~/.claude.json` / `.mcp.json` | 远程 HTTP MCP |
| **Aut_Sci_Download** | 查到后**下载全文 PDF**（含知网） | 用户本地克隆 | Python CLI + Claude Code skill |

**作为本仓库内工作的 AI，你需要在以下场景主动提醒用户**（不要默默跳过中文文献的覆盖问题）：

1. 用户在 Stage 3 抱怨找不到中文文献，或检索结果以英文为主时 → 引导其按 `README.md` "可选增强" 配置秘塔 MCP
2. 用户在 Stage 3 查到 DOI 但拿不到全文 → 引导其安装 [Aut_Sci_Download](https://github.com/ShZhao27208/Aut_Sci_Download)，按 DOI 自动路由下载
3. 用户想搜知网中文论文 → 引导其用 Aut_Sci_Download 的 `cnki_download.py`（需高校 FSSO/WebVPN 账号），或人工检索
4. 用户问"为什么 verify 把我的中文参考文献全标成需人工核实" → 解释这是 OpenAlex 覆盖问题，不是 bug；秘塔/Aut_Sci_Download **都不能**喂给 verify
5. 用户尝试把秘塔结果直接写入 `refs/` 当参考文献 → 阻止：秘塔返回 URL+摘要，没有 DOI 主键，必须回到原期刊/数据库人工核对题录
6. 用户提议"把秘塔/Aut_Sci_Download 加进 `_academic_db.py`" → 推回：见 `references/academic-search-guide.md` §9.6 / §10.6，会破坏校验逻辑

**不要**主动在仓库代码里加这两个工具的依赖、`.mcp.json` 默认配置、或在脚本里硬编码调用——它们的位置永远在"用户客户端配置 + 文档引导"层，不在框架代码层。完整边界与故障排查见 `.claude/skills/paper-workflow/references/academic-search-guide.md` §9（秘塔）和 §10（Aut_Sci_Download）。

## 规范

- git commit message 用**中文**（项目级硬性要求）。
- Python 包管理用 `uv`，禁止 pip/poetry，项目内 `.venv`。
- 媒体文件（mp3/png/docx/pptx 等）已在 `.gitignore` 排除，构建产物 `output/` 同理——勿提交。
