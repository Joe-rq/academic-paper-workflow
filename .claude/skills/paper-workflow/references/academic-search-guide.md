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
| **Google Scholar** | ✅ 最全（含知网索引页） | ✅ 部分政策文件 | 兜底检索（通过 WebSearch，无 API） |
| **知网/万方** | ✅ 全 | ✅ 全 | **必须人工检索**（无 API） |

**实操建议**：
- 英文文献、国际期刊 → OpenAlex/S2 API 自动检索
- 中文核心刊 → 先试 OpenAlex（可能命中），未命中转知网/万方人工检索
- 中文普通期刊、政策文件、课程标准 → 直接知网/万方/政府网站人工检索
- **写作时优先引用可验证来源**（有 DOI 或 OpenAlex 收录），降低 Stage 7 的人工核实量

---

## 1. 数据库选型表

| 你要找…… | 首选数据库 | 也考虑 |
|----------|-----------|--------|
| 某主题的论文 | **OpenAlex** | Semantic Scholar |
| 某篇论文（有 DOI） | **Crossref** | OpenAlex、Unpaywall |
| 某篇论文（只有题名） | **OpenAlex** | Semantic Scholar |
| 谁引用了某篇论文（前向引用） | **Semantic Scholar** | OpenAlex |
| 某作者的所有论文 | **Semantic Scholar** | OpenAlex |
| 论文推荐（相似主题） | **Semantic Scholar** | — |
| 期刊/出版社元数据 | **Crossref** | OpenAlex |
| 开放获取 PDF | Unpaywall（按 DOI） | — |
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
   ↓ 未命中
4. 知网/万方 人工检索（无 API，建议用户操作或 WebSearch 兜底）
   ↓
5. 核心文献：Semantic Scholar 查 TLDR + 引用图谱，扩展相关文献
   ↓
6. 每条记录：题名、作者、年份、期刊、DOI（如有）
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
