# 学术文献检索指南

> 适用于 Stage 3（文献研究）。本指南给出可直接调用的学术数据库 API，
> 让 Claude 在文献检索阶段获取真实、可引用的论文——从源头避免编造参考文献。
> 与 `deep-research-guide.md`（方法论）配合：前者讲"怎么搜、怎么整理"，本指南讲"去哪搜、怎么调 API"。

---

## 0. 先读这一段：中文论文的检索现实

**核心约束**：知网(CNKI)、万方、维普**没有公开 API**，无法程序化检索。本指南的三个数据库（OpenAlex / Semantic Scholar / Crossref）都是**英文为主的国际库**，对中文文献的覆盖如下：

| 数据库 | 中文期刊覆盖 | 中文政策/标准 | 适用场景 |
|--------|------------|--------------|---------|
| **OpenAlex** | 部分（收录部分 CSSCI/北大核心刊元数据，如《教育发展研究》《中国职业技术教育》） | ❌ 无 | 题名搜索、英文文献、部分中文核心刊 |
| **Semantic Scholar** | 较少（偏英文） | ❌ 无 | 引用图谱、TLDR 摘要、英文文献推荐 |
| **Crossref** | 极少（仅带 DOI 的） | ❌ 无 | DOI→元数据查证、引文格式验证 |
| **秘塔 MCP（`paper` scope）** | ✅ 较好（开放获取期刊 + 网络可见学术资源） | ◐ 部分 | **中文文献发现**首选（需自行安装，见 §9） |
| **Aut_Sci_Download** | ◐ 知网需高校账号 | ❌ 无 | 查到 DOI/题名后**下载全文 PDF**（见 §10） |
| **Google Scholar** | ✅ 最全（含知网索引页） | ✅ 部分政策文件 | 兜底检索（通过 WebSearch，无 API） |
| **知网/万方** | ✅ 全（含博硕全文） | ✅ 全 | **必须人工检索**（无开放 API） |

**实操建议**：
- 英文文献、国际期刊 → OpenAlex/S2 API 自动检索 → Aut_Sci_Download 拿全文 PDF
- 中文核心刊 → 先试 OpenAlex（可能命中），未命中走秘塔 MCP（如已装），仍无果转知网/万方人工
- 中文博硕论文、闭源 CSSCI 全文、政策文件 → 知网/万方/政府网站人工检索（秘塔不索引知网博硕）
- **查到 DOI 后需要全文** → Aut_Sci_Download 按 DOI 自动路由下载（Elsevier/Springer/IEEE/arXiv/Unpaywall/S2/PubMed/知网，8 个源）
- **写作时优先引用可验证来源**（有 DOI 或 OpenAlex 收录），降低 Stage 7 的人工核实量

**注意**：秘塔结果只用作"发现"，**不能**喂给 `verify_references.py`——它返回 URL+摘要而非 DOI，不构成参考文献真实性的可靠校验源。Aut_Sci_Download 只做下载，**不做校验**，不能替代 verify。

---

## 1. 数据库选型表

| 你要找…… | 首选数据库 | 也考虑 |
|----------|-----------|--------|
| 某主题的论文 | **OpenAlex** | Semantic Scholar |
| 某主题的**中文**论文 | **秘塔 MCP**（`paper` scope） | OpenAlex 中文题名搜索 |
| 某篇论文（有 DOI） | **Crossref** | OpenAlex、Unpaywall |
| 某篇论文（只有题名） | **OpenAlex** | Semantic Scholar |
| 谁引用了某篇论文（前向引用） | **Semantic Scholar** | OpenAlex |
| 某作者的所有论文 | **Semantic Scholar** | OpenAlex |
| 论文推荐（相似主题） | **Semantic Scholar** | — |
| 期刊/出版社元数据 | **Crossref** | OpenAlex |
| 开放获取 PDF | Unpaywall（按 DOI） | — |
| **按 DOI 下载全文 PDF** | **Aut_Sci_Download**（8 源自动路由） | Unpaywall |
| **知网论文 PDF**（需高校账号） | **Aut_Sci_Download**（FSSO/WebVPN） | 人工下载 |
| 最全的中文覆盖 | Google Scholar（WebSearch） | 知网/万方（人工） |

---

## 2. OpenAlex API（首选通用库）

250M+ 学术作品，**免费、无需 key**（加 `mailto` 进 polite pool 速率更高）。覆盖最广，含部分中文核心刊。

**Base URL**：`https://api.openalex.org`

### 按题名搜索

```bash
curl "https://api.openalex.org/works?search=flipped+classroom+mathematics&per-page=5&select=id,title,publication_year,authorships,doi&mailto=your@email.com"
```

常用参数：
- `search`：全文搜索（题名+摘要+正文），支持 `AND`/`OR`/`NOT`（大写）
- `filter=from_publication_date:2020-01-01`：按日期过滤
- `filter=publication_year:2023`：按年份
- `filter=cited_by_count:>50`：引用数门槛
- `sort=cited_by_count:desc`：按引用数降序（先看高影响力）
- `per-page`：每页数（最大 100），`page`：页码

### 按 DOI 精确查询

```bash
curl "https://api.openalex.org/works/doi:10.1038/nature12373?mailto=your@email.com"
```

### 返回结构（关键字段）

```json
{
  "results": [{
    "id": "https://openalex.org/W2741809807",
    "title": "...",
    "publication_year": 2023,
    "doi": "https://doi.org/10.xxxx/yyy",
    "authorships": [{"author": {"display_name": "..."}, "institutions": [...]}],
    "cited_by_count": 123,
    "primary_location": {"source": {"display_name": "期刊名"}}
  }]
}
```

---

## 3. Semantic Scholar API（引用图谱 + 摘要）

200M+ 论文，特色是 **TLDR 摘要**（AI 生成的一句话总结）、**引用上下文**、**论文推荐**。免费，申请 key 更稳。

**Base URL**：`https://api.semanticscholar.org/graph/v1`

### 按题名搜索

```bash
curl "https://api.semanticscholar.org/graph/v1/paper/search?query=understanding+by+design&fields=title,year,abstract,citationCount,authors,openAccessPdf,tldr&limit=10"
```

`fields` 参数（逗号分隔，不加空格）：`title, year, abstract, venue, citationCount, influentialCitationCount, authors, openAccessPdf, tldr, fieldsOfStudy`

### 论文详情（接受多种 ID 前缀）

```bash
# DOI
curl "https://api.semanticscholar.org/graph/v1/paper/DOI:10.1038/nature12373?fields=title,abstract,references.title"
# arXiv ID
curl "https://api.semanticscholar.org/graph/v1/paper/ARXIV:2103.15348?fields=title"
# PMID
curl "https://api.semanticscholar.org/graph/v1/paper/PMID:34567890?fields=title"
```

### 引用图谱（前向引用：谁引用了这篇）

```bash
curl "https://api.semanticscholar.org/graph/v1/paper/{paperId}/citations?fields=title,citationCount&limit=20"
```

**速率**：无 key 约 1 req/s（共享池，易 429）；有 key 10 req/s。申请：https://www.semanticscholar.org/product/api#api-key-form

---

## 4. Crossref API（DOI 元数据 + 引文验证）

150M+ DOI 元数据。**最权威的 DOI 查证来源**——用于验证参考文献是否真实存在（Stage 7 的 `verify_references.py` 底层即用此）。

**Base URL**：`https://api.crossref.org`

### 按 DOI 查（最可靠）

```bash
curl "https://api.crossref.org/works/10.1038/nature12373" -H "User-Agent: paper-workflow/1.0 (mailto:your@email.com)"
```

404 = DOI 不存在（疑似编造信号）。

### 按题名搜索

```bash
curl "https://api.crossref.org/works?query.title=understanding+by+design&rows=5"
```

### 引文格式验证

Crossref 返回的 `message` 含完整元数据（作者、标题、期刊、年份、卷期页），可用于生成或校验 GB/T 7714 引文格式。

**Polite pool**：在 `User-Agent` 头加 `mailto:your@email.com`，速率从 5 req/s 提到 10 req/s。

---

## 5. Google Scholar（通过 WebSearch，无 API）

Google Scholar 覆盖最全（含知网索引页），但**无官方 API**、反爬严格。在 Claude Code 中用 `WebSearch` 工具间接检索：

### 搜索运算符

| 运算符 | 作用 | 示例 |
|--------|------|------|
| `"..."` | 精确短语 | `"翻转课堂"` |
| `author:` | 按作者 | `author:曹一鸣` |
| `source:` | 按期刊 | `source:数学教育学报` |
| `intitle:` | 标题含词 | `intitle:翻转课堂` |
| 年份范围 | 按时间 | `翻转课堂 2020..2024` |

### 引用追踪（前向引用）

Google Scholar 的 "Cited by" 链接可找后续引用，但需人工点击。批量需求改用 Semantic Scholar API 的 `/citations` 端点。

---

## 6. 标识符格式与互转

不同数据库用不同标识符。查询失败常因 ID 格式不匹配。

| 标识符 | 格式 | 示例 | 接受方 |
|--------|------|------|--------|
| DOI | `10.xxxx/yyy` | `10.1038/nature12373` | 全部 |
| PMID | 数字 | `34567890` | PubMed, S2 |
| arXiv ID | `YYMM.NNNNN` | `2103.15348` | arXiv, S2 |
| S2 paperId | 40 位 hex | `649def34f8be...` | Semantic Scholar |

**互转技巧**：Semantic Scholar 接受 `DOI:`/`PMID:`/`ARXIV:` 前缀；OpenAlex 接受 `doi:`/`pmid:` 前缀。用这些前缀可跨库查同一篇论文。

---

## 7. 检索实操流程（Stage 3 建议）

```
1. 提取研究问题的 3-5 个关键词（中英文各一组）
   ↓
2. 英文文献：OpenAlex search（sort=cited_by_count:desc）→ 取 top 10
   ↓
3. 中文文献：OpenAlex search（中文题名）→ 命中的取用
   ↓ 未命中 → 秘塔 MCP（如已装，scope=paper）
   ↓ 仍无果 → 知网/万方 人工检索
   ↓
4. 查到 DOI → Aut_Sci_Download（如已装）自动路由下载全文 PDF
   ↓ 下载失败或无 DOI → Unpaywall 查 OA 版本，或人工获取
   ↓
5. 核心文献：Semantic Scholar 查 TLDR + 引用图谱，扩展相关文献
   ↓
6. 每条记录：题名、作者、年份、期刊、DOI（如有）+ PDF 路径（如有）
   ↓ 写入 refs/ 文献笔记
7. 建立 文献矩阵（见 deep-research-guide.md Step 4）
```

---

## 8. 验证覆盖率意识（影响 Stage 7）

写作时对参考文献的可验证性有意识，能显著降低 Stage 7 `verify_references.py` 的"需人工核实"数量：

| 引用类型 | Stage 7 验证结果 | 写作建议 |
|---------|----------------|---------|
| 带 DOI 的英文/国际期刊论文 | ✅ 可自动验证 | 优先引用 |
| OpenAlex 收录的中文核心刊 | ✅ 可自动验证 | 优先引用 |
| OpenAlex 未收录的中文期刊 | ◐ 需人工核实（知网/万方） | 可用，但人工核实成本高 |
| 政策文件、课程标准 `[S]`/`[Z]` | — 跳过（不可库验） | 务必标注准确出处（文号、发布机关） |
| **AI 编造的文献**（DOI 指向另一篇 / DOI 不存在） | ⚠️❌ 自动检出 | **绝不引用未经检索确认的文献** |

**铁律**：任何由 AI 生成的参考文献，**必须经过上述数据库检索确认存在**后才能写入论文。无法确认的，标"需人工核实"并实际去知网核实——绝不可凭"看起来合理"就采用。

---

## 9. 秘塔 MCP（可选增强，补中文文献漏洞）

§0 已说明：本指南内置的三个数据库以英文为主，中文期刊召回率低；知网/万方无开放 API。**秘塔 AI 搜索**对中文学术资源（开放获取期刊、网络可见学术内容）覆盖较好，可作为 Stage 3 中文文献发现的补充工具。

> **本仓库不预装、不强制要求**。下面是给终端用户的安装引导——是否启用由你（论文作者）决定。

### 9.1 能力边界（先读这一段，避免误用）

| 维度 | 是 / 否 |
|------|--------|
| 中文开放获取期刊 | ✅ 较好 |
| 中文核心刊（CSSCI/北大核心）题录 | ◐ 部分（取决于该刊是否有网络可见全文/摘要） |
| **知网博硕论文全文** | ❌ 不索引 |
| **闭源 CSSCI 全文** | ❌ 不索引 |
| 返回稳定 DOI/可校验 ID | ❌（返回 URL + 摘要） |
| 适合做参考文献"真实性"核验源 | ❌（不能喂 `verify_references.py`） |
| 适合做"中文文献发现 + 综述背景扫描" | ✅ |

**结论**：用秘塔**找线索**，找到后人工去知网/期刊官网核对原文，把可验证的题录（最好带 DOI）写入参考文献。

### 9.2 安装（远程 HTTP MCP，无需本地 server）

秘塔官方提供托管 MCP 端点，**不需要 pip / npm / Docker**，只在 MCP 客户端配置一段 URL+Bearer 即可。

**Step 1：申请 API Key**

1. 访问 https://metaso.cn/ 注册并登录
2. 进入 https://metaso.cn/search-api/api-keys
3. 创建新 Key，妥善保存（页面提示不要放在浏览器/客户端代码中——本指南配置走环境变量，不写明文）

**Step 2：在 Claude Code 客户端配置 MCP**

在你的用户级 `~/.claude.json`（或项目级 `.mcp.json`，按你的偏好）中添加：

```json
{
  "mcpServers": {
    "metaso": {
      "url": "https://metaso.cn/api/mcp",
      "headers": {
        "Authorization": "Bearer ${METASO_API_KEY}"
      }
    }
  }
}
```

并在 shell 环境（或 `.env`）里 `export METASO_API_KEY=sk-xxxxx`。重启 Claude Code 后，`/mcp` 命令应能看到 `metaso` 已连接。

**VSCode 用户**走 `.vscode/mcp.json`：

```json
{
  "servers": {
    "metaso": {
      "url": "https://metaso.cn/api/mcp",
      "type": "http",
      "headers": { "Authorization": "Bearer ${METASO_API_KEY}" }
    }
  },
  "inputs": []
}
```

### 9.3 三个工具与 Stage 3 调用模式

| 工具 | 用途 | Stage 3 推荐场景 |
|------|------|-----------------|
| `metaso_web_search` | 多 scope 搜索 | **主力**：`scope="paper"` 找中文论文线索 |
| `metaso_web_reader` | URL → markdown/json | 命中后取全文做精读 |
| `metaso_chat` | RAG 问答 | 选题初期"先扫一圈中文学术共识" |

**调用示例（在 Claude Code 对话中直接写）**：

```
# 1) 中文文献发现
请用 metaso_web_search 搜索 "翻转课堂 高中数学 元认知"，scope=paper, size=10, includeSummary=true，
列出题名/作者/年份/期刊/URL，标注哪些可能在知网博硕、哪些是开放获取期刊。

# 2) 命中后取全文
对其中第 3 条，用 metaso_web_reader 读取 URL，format=markdown，提取核心论点和方法部分。

# 3) 综述背景扫描（选题阶段慎用，结果需查证）
请用 metaso_chat 回答："近五年关于 XX 的中文研究有哪些主要流派？"——
仅作思路启发，所有事实主张必须回到 metaso_web_search 检索原文核对。
```

### 9.4 与现有工作流的分工

| 阶段 | 谁主力 | 秘塔角色 |
|------|--------|---------|
| Stage 3 research（英文 / 国际期刊） | OpenAlex / S2 / Crossref + `/deep-research` | — |
| Stage 3 research（**中文文献发现**） | **秘塔 `paper` scope** | 主力 |
| Stage 3 research（中文博硕、闭源全文） | 知网/万方人工 | — |
| Stage 7 verify（参考文献真实性） | `verify_references.py` + Crossref/OpenAlex | **不参与** |

### 9.5 故障排查

| 现象 | 排查 |
|------|------|
| `/mcp` 看不到 metaso | 检查 `${METASO_API_KEY}` 是否被 shell 真正展开（在 Windows PowerShell 下 `$env:METASO_API_KEY`），重启 Claude Code |
| 401 Unauthorized | Key 失效或拼写错（必须 `Bearer ` 开头，注意空格） |
| 配额耗尽 | 在 https://metaso.cn/search-api 控制台查用量；考虑降低 `size` 或在选题确定后才大量调 |
| `paper` scope 返回少 | 中文核心刊/闭源资源本就不在索引内，转知网人工检索 |

### 9.6 不推荐的用法

- ❌ 把秘塔结果直接写进 `refs/` 当参考文献——必须人工去原期刊/数据库核对，至少补全题名/作者/年份/刊名/卷期页
- ❌ 在 `verify_references.py` 里加秘塔做第四数据源——返回结构无 DOI 主键，会破坏校验逻辑
- ❌ 用 `metaso_chat` 的回答直接当文献综述写入论文——RAG 输出仍是 AI 生成，存在编造风险，必须回到 `metaso_web_search` 找原文

---

## 10. Aut_Sci_Download（可选增强，按 DOI 下载全文 PDF）

§0–§8 解决了"去哪搜、怎么查元数据"的问题，但拿到 DOI 后**如何获取全文 PDF** 一直靠人工。Aut_Sci_Download 填补了这个缺口：根据 DOI / arXiv ID / PMID / 关键词，从 8 个学术平台自动路由下载论文 PDF——包括**知网**（需高校账号）。

> **本仓库不预装、不强制要求**。下面是给终端用户的安装引导——是否启用由你（论文作者）决定。

### 10.1 支持的数据源与认证方式

| 数据源 | DOI 前缀 / 输入类型 | 认证 | 覆盖 |
|--------|-------------------|------|------|
| Elsevier / ScienceDirect | `10.1016/...` | 免费 API Key | Elsevier 期刊 |
| Springer Nature | `10.1038/...` / `10.1007/...` | 免费 API Key | Springer / Nature 开放获取 |
| IEEE Xplore | `10.1109/...` | 免费 API Key | IEEE / IET 期刊与会议 |
| arXiv | arXiv ID（如 `2301.07041`） | 无需认证 | 物理、CS、数学预印本 |
| Unpaywall | 任意 DOI | 仅需邮箱 | 任意 DOI 的开放获取版本 |
| Semantic Scholar | DOI / arXiv ID / 关键词 | 无需认证 | 跨库 OA PDF 聚合 |
| PubMed Central | PMCID / PMID / DOI | 无需认证 | 生物医学开放获取 |
| **CNKI 知网** | 中文关键词 / 知网文献号 | **高校账号（FSSO 或 WebVPN）** | **中文期刊、学位论文** |

### 10.2 能力边界

| 维度 | 是 / 否 |
|------|--------|
| 拿到 DOI 后下载开放获取全文 PDF | ✅ 自动路由 8 源 |
| 知网中文论文 PDF | ✅ **但需高校账号**（FSSO 统一认证或 WebVPN） |
| 非开放获取且无高校权限的付费论文 | ❌ 只能拿元数据，PDF 需人工通过学校图书馆获取 |
| 文献发现（题名/关键词检索） | ◐ S2 / IEEE / arXiv / 知网支持关键词搜索，但不如 OpenAlex/秘塔全面 |
| 参考文献"真实性"校验 | ❌ 不做校验，不能替代 `verify_references.py` |

**定位**：本指南 §1–§8 解决"查到"，秘塔 MCP §9 补"中文发现"，**Aut_Sci_Download 解决"拿到全文"**——三层互补，不重叠。

### 10.3 安装

**Step 1：克隆仓库并安装依赖**

```bash
git clone https://github.com/ShZhao27208/Aut_Sci_Download.git
cd Aut_Sci_Download
pip install -r requirements.txt
```

**Step 2：配置 API Key**

所有密钥保存在 `~/.aut-sci-download/.env`：

```bash
# 必需（按你实际使用的源配置，不用全填）
ELSEVIER_API_KEY=your-key          # https://dev.elsevier.com/
SPRINGER_API_KEY=your-key          # https://dev.springernature.com/
IEEE_API_KEY=your-key              # https://developer.ieee.org/
UNPAYWALL_EMAIL=your@email.com     # Unpaywall 只需邮箱

# 可选
NCBI_API_KEY=your-key              # PubMed，无 key 也能用但速率低
```

通用配置保存在 `~/.aut-sci-download/config.json`：

```json
{
  "download_dir": "~/Downloads/papers",
  "proxy": null
}
```

**Step 3：知网配置（可选，需高校账号）**

```bash
# FSSO 模式（推荐，大部分高校支持）
python scripts/cnki_download.py set-mode fsso
python scripts/cnki_download.py status    # 检查认证状态
python scripts/cnki_download.py check     # 测试连通性

# WebVPN 模式（FSSO 不可用时）
python scripts/cnki_download.py set-mode webvpn
```

**Step 4：Claude Code skill 集成**

仓库自带 `.claude/skills/sci-download.md`。将 `Aut_Sci_Download` 仓库放在你的工作目录或 Claude Code 可识别的 skill 目录下，Claude 即可在对话中自动选择并调用下载脚本。

### 10.4 在 Stage 3 的调用模式

Aut_Sci_Download 不是 MCP 服务，是 CLI 脚本。在 Claude Code 对话中的使用方式：

```
# 1) 按 DOI 下载（自动路由到对应数据源）
请运行 python scripts/elsevier_download.py "10.1016/j.cell.2024.01.029"
# 或让 Claude 自动判断 DOI 前缀选脚本

# 2) arXiv 预印本
请运行 python scripts/arxiv_download.py "2301.07041"

# 3) 关键词搜索 + 下载（IEEE/S2/arXiv/知网支持）
请运行 python scripts/ieee_download.py --search "transformer attention mechanism" --limit 5
请运行 python scripts/semantic_scholar_download.py --search "flipped classroom" --limit 10

# 4) 知网中文检索（需先配置 FSSO/WebVPN）
请运行 python scripts/cnki_download.py search "翻转课堂 元认知" --limit 10
请运行 python scripts/cnki_download.py download ZGTB202401001 --dbcode CJFD
```

**自动路由逻辑**（让 Claude 判断）：

| 输入 | 优先源 |
|------|--------|
| `10.1016/...` | Elsevier |
| `10.1038/...` / `10.1007/...` | Springer Nature |
| `10.1109/...` | IEEE Xplore |
| arXiv ID | arXiv |
| PMCID / PMID | PubMed Central |
| 中文关键词 / 知网文献号 | CNKI 知网 |
| 其他 DOI | Unpaywall → Semantic Scholar |

### 10.5 与现有工作流的分工

| 阶段 | 谁主力 | Aut_Sci_Download 角色 |
|------|--------|---------------------|
| Stage 3 文献**发现**（英文） | OpenAlex / S2 + `/deep-research` | — |
| Stage 3 文献**发现**（中文） | 秘塔 MCP（§9） | ◐ 知网搜索（需高校账号） |
| Stage 3 文献**获取**（下载全文 PDF） | **Aut_Sci_Download** | 主力 |
| Stage 7 verify（参考文献真实性） | `verify_references.py` + Crossref/OpenAlex | **不参与** |

### 10.6 不推荐的用法

- ❌ 用它替代 OpenAlex/秘塔做文献发现——它的搜索能力有限，核心价值是**下载**
- ❌ 在 `verify_references.py` 里集成——它不做真实性校验
- ❌ 把下载的 PDF 内容直接当参考文献条目——PDF 是阅读材料，参考文献条目仍需从数据库（Crossref/OpenAlex）获取结构化元数据（作者/年份/卷期页/DOI）
- ❌ 在没有高校账号的情况下指望知网下载——FSSO/WebVPN 认证是硬性前提
