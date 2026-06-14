# Academic Paper Workflow

中文学术论文 AI 辅助写作工作流框架。覆盖期刊论文、毕业论文、征文等场景。

## 快速开始

```bash
# 1. 克隆项目
git clone <repo-url>
cd academic-paper-workflow

# 2. 安装 Python 依赖
uv sync

# 3. 在 Claude Code 中使用
/paper-workflow init -n "论文标题" -t journal-paper
```

## 10 阶段工作流

```
Stage 1  [init]       项目初始化    → 从模板创建论文项目
Stage 2  [brainstorm] 头脑风暴      → 34问结构化框架
Stage 3  [research]   文献研究      → /deep-research
Stage 4  [outline]    大纲设计      → 生成论文大纲
Stage 5  [write]      分节写作      → 按 rhetorical moves 逐节写作
Stage 6  [figures]    图表制作      → matplotlib 生成图表
Stage 7  [review]     同行评审      → /paper-review-team（多agent）/ /academic-paper-reviewer
Stage 8  [revise]     修改迭代      → 根据评审意见修改
Stage 9  [build]      构建输出      → md→docx + 交叉引用
Stage 10 [archive]    归档定稿      → 版本快照
```

## 架构

```
academic-paper-workflow/
├── .claude/skills/
│   ├── paper-workflow/             # 主 Skill（10 阶段工作流）
│   │   ├── SKILL.md                # 工作流定义
│   │   ├── references/             # 写作知识库
│   │   └── scripts/                # 构建脚本
│   └── paper-review-team/          # 多 agent 评审团队（Stage 7 增强）
│       └── SKILL.md                # 4 角色独立并行评审
├── templates/                      # 论文项目模板
│   ├── journal-paper/              # 期刊论文
│   ├── thesis/                     # 毕业论文
│   └── essay/                      # 征文
└── docs/                           # 文档
```

## 融合设计

本项目融合了三个来源的优秀实践：

| 来源 | 继承内容 |
|------|----------|
| **实际论文项目** | 构建链（md→docx、交叉引用、引文校验）、迭代模式 |
| **thesis-v2** | 四层元架构（认知边界/意图防护/执行可靠/持续优化） |
| **codex-claude-academic-skills** | 34问头脑风暴、section rhetorical moves、evidence labeling |

## 依赖 Skill

本工作流通过引用已有 skill 完成各阶段工作：

- `deep-research` — 文献研究（Stage 3）
- `academic-paper` — 写作引擎（Stage 5）
- `academic-paper-reviewer` — 同行评审（Stage 7）
- `md-to-docx` — md→docx 构建（Stage 9）
- `humanizer-cn` — 降 AI 检测（Stage 7-8）

## 内置增强 Skill

本项目自带以下 skill，无需额外安装：

- `paper-workflow` — 主工作流（10 阶段）
- `paper-review-team` — 多 agent 同行评审。组建 4 个真正独立的评审 agent（主编/方法论专家/领域专家/魔鬼代言人）并行评审，突破单 agent 串行扮演的"伪独立评审"。Stage 7 质量验收时调用 `/paper-review-team` 获得更严格的对抗性评审。

## 可选增强

### 中文文献发现：秘塔 MCP

Stage 3 内置的三大库（OpenAlex / Semantic Scholar / Crossref）以英文为主，对中文期刊召回率有限，知网/万方又无开放 API——这是本框架在中文文献检索上的已知短板。

如果你写中文论文且常引中文期刊，**强烈建议**接入秘塔 AI 搜索的官方 MCP 作为补充：

```jsonc
// 加到 ~/.claude.json 或项目 .mcp.json
{
  "mcpServers": {
    "metaso": {
      "url": "https://metaso.cn/api/mcp",
      "headers": { "Authorization": "Bearer ${METASO_API_KEY}" }
    }
  }
}
```

- API Key 申请：https://metaso.cn/search-api/api-keys（需注册）
- 远程 HTTP MCP，**不需要 pip/npm 装本地 server**
- 详细配置、调用示例、能力边界（什么能补、什么补不了）见 `.claude/skills/paper-workflow/references/academic-search-guide.md` §9

**用法定位**：秘塔只用作"中文文献发现"，**不替代**知网博硕/闭源 CSSCI 全文的人工核实，**也不参与** Stage 7 的 `verify_references.py` 真实性校验。

### 论文全文下载：Aut_Sci_Download

Stage 3 查到文献元数据（DOI/题名）后，如何获取全文 PDF？本框架不内置下载能力。[Aut_Sci_Download](https://github.com/ShZhao27208/Aut_Sci_Download)（MIT 协议）根据 DOI / arXiv ID / PMID 自动路由到 8 个数据源下载 PDF，**包括知网**（需高校 FSSO/WebVPN 账号）。

```bash
# 安装
git clone https://github.com/ShZhao27208/Aut_Sci_Download.git
cd Aut_Sci_Download && pip install -r requirements.txt

# 配置 API Key（存入 ~/.aut-sci-download/.env）
# Elsevier / Springer / IEEE / Unpaywall 各需免费 Key
# 详见 https://github.com/ShZhao27208/Aut_Sci_Download
```

- 支持：Elsevier / Springer / IEEE / arXiv / Unpaywall / Semantic Scholar / PubMed / **知网**
- 知网中文检索 + 下载需高校账号（FSSO 统一认证或 WebVPN）
- 仓库自带 Claude Code skill（`.claude/skills/sci-download.md`），克隆后即可在对话中调用
- 详细配置、路由逻辑、能力边界见 `.claude/skills/paper-workflow/references/academic-search-guide.md` §10

**用法定位**：只做"下载全文"，不做文献发现（搜文献仍用 OpenAlex/秘塔），不做参考文献校验（仍用 `verify_references.py`）。

## 支持的论文类型

| 类型 | 模板 | 说明 |
|------|------|------|
| `journal-paper` | 期刊论文 | 6000-10000字，GB/T 7714 引用格式 |
| `thesis` | 毕业论文 | 30000+字，完整论文结构 |
| `essay` | 征文 | 3000-8000字，较灵活的结构 |

## 致谢

本项目参考了以下开源项目，感谢作者的公开贡献：

| 项目 | 作者 | 协议 | 借鉴内容 |
|------|------|------|---------|
| [codex-claude-academic-skills](https://github.com/zLanqing/codex-claude-academic-skills) | zLanqing | MIT | 34问头脑风暴框架、6节写作语步、来源标注规范 |
| [academic-research-skills](https://github.com/Imbad0202/academic-research-skills) | Cheng-I Wu | CC BY-NC 4.0 | 文献研究方法论、写作流程、评审维度 |
| [Humanizer-zh](https://github.com/op7418/Humanizer-zh) | 歸藏 | MIT | 22种中文 AI 写作模式检测与消除 |
| [Aut_Sci_Download](https://github.com/ShZhao27208/Aut_Sci_Download) | ShZhao27208 | MIT | 论文全文 PDF 下载（8 源自动路由，含知网 FSSO） |
