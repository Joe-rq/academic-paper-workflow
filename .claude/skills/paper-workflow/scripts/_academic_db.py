# -*- coding: utf-8 -*-
"""学术参考文献处理与数据库查询共享模块。

为 verify_references.py（参考文献存在性验证）和将来的检索脚本提供统一能力：
  - GB/T 7714 文献归一化（从 build_academic_docx.py 提取，行为不变）
  - 题名相似度（difflib，比较前剥离版次括号与英文冠词）
  - DOI 提取（裸 DOI / doi.org URL / CNKI DOI= 三种形态）
  - Crossref / OpenAlex REST 查询（urllib，per-host 限速，429 退避）

零第三方依赖，仅用 stdlib。线程安全（ThreadPoolExecutor 并发调用安全）。
"""
from __future__ import annotations

import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from typing import Any

# 网络状态：检测到不可达后置 True。调用方据此跳过在线检查（Check A 仍可离线跑）。
OFFLINE = False


# =========================================================================
# 一、GB/T 7714 归一化（从 build_academic_docx.py 提取，行为完全不变）
# =========================================================================

def normalize_reference(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    text = text.replace("：", ":")
    text = text.replace("，", ",")
    text = text.replace("（", "(").replace("）", ")")
    text = text.replace(" (Eds.)", "")
    text = re.sub(r"\s+\[([A-Z]+(?:/[A-Z]+)?)\]", r"[\1]", text)
    text = re.sub(r"\]\s+\.", "].", text)
    text = re.sub(r"\s*:\s*", ": ", text)
    text = re.sub(r"\s*,\s*", ", ", text)
    text = normalize_english_authors(text)
    if not text.endswith("."):
        text += "."
    return text


def normalize_english_authors(text: str) -> str:
    """GB/T 7714 style: uppercase western surnames and keep initials undotted."""
    if not re.match(r"^\[\d+\]\s+[A-Za-z]", text):
        return text
    prefix, rest = text.split("] ", 1)
    author_part, sep, title_part = rest.partition(". ")
    if not sep:
        return text

    normalized_authors = []
    for author in author_part.split(", "):
        author = author.strip()
        match = re.match(r"^([A-Za-z][A-Za-z'\- ]*?)\s+([A-Z](?:\s+[A-Z])*)$", author)
        if match:
            surname = match.group(1).upper()
            initials = match.group(2).replace(".", "")
            normalized_authors.append(f"{surname} {initials}")
        else:
            normalized_authors.append(author.upper() if re.match(r"^[A-Za-z'\- ]+$", author) else author)
    return f"{prefix}] {', '.join(normalized_authors)}. {title_part}"


# =========================================================================
# 二、题名相似度
# =========================================================================

TITLE_SIMILARITY_THRESHOLD = 0.70

# 比较前剥离的噪声：括号版次/系列（(2nd ed.) / （第3版））、英文冠词、标点
_EDITION_PAT = re.compile(r"\s*\([^)]*(?:ed\.|edition|版|第[一二三四五六七八九十\d]+版)[^)]*\)", re.IGNORECASE)
_ARTICLES = {"the", "a", "an"}
_PUNCT_TO_SPACE = str.maketrans({c: " " for c in ".,;:!?()[]\"'—–-_/"})


def _normalize_title_for_match(s: str) -> str:
    """题名归一化用于相似度比较：剥离版次括号、英文冠词，标点转空格，小写。"""
    if not s:
        return ""
    s = _EDITION_PAT.sub("", s)
    s = s.translate(_PUNCT_TO_SPACE)
    tokens = [t for t in s.lower().split() if t not in _ARTICLES]
    return " ".join(tokens)


def title_similarity(a: str, b: str) -> float:
    """两题名相似度（0-1），基于 difflib SequenceMatcher 的归一化字符串。"""
    na, nb = _normalize_title_for_match(a), _normalize_title_for_match(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


# =========================================================================
# 三、DOI 提取
# =========================================================================

# 裸 DOI：10.xxxx/yyy（不含空白与结束符）
_BARE_DOI_PAT = re.compile(r"\b10\.\d{4,9}/[^\s\"<>]+")
# URL 嵌入：doi.org/xxx 或 dx.doi.org/xxx
_DOI_URL_PAT = re.compile(r"https?://(?:dx\.)?doi\.org/(10\.\S+?)[\s\"<>\]|)]*$", re.IGNORECASE)
# CNKI：DOI=10.xxx 或 DOI:10.xxx
_CNKI_DOI_PAT = re.compile(r"DOI[:=]\s*(10\.\S+?)[\s\"<>\]|)]*$", re.IGNORECASE)


def extract_doi(text: str) -> str | None:
    """从任意文本提取首个 DOI（支持裸 DOI、doi.org URL、CNKI DOI= 形式）。"""
    if not text:
        return None
    for pat in (_DOI_URL_PAT, _CNKI_DOI_PAT, _BARE_DOI_PAT):
        m = pat.search(text)
        if m:
            doi = m.group(1) if m.lastindex else m.group(0)
            return doi.rstrip(".,;)").strip()
    return None


# =========================================================================
# 四、HTTP 层（urllib，per-host 限速，429 退避，线程安全）
# =========================================================================

_POLITE_EMAIL = "paper-workflow@example.com"  # polite pool 标识，Crossref/OpenAlex 据此提速率
_DEFAULT_TIMEOUT = 8
_MAX_RETRIES = 3
_BACKOFF_SECONDS = 2.0

# per-host 限速间隔（秒）：带 mailto 进 polite pool，可放宽；匿名默认 1.0s
_host_min_interval = {"api.crossref.org": 0.2, "api.openalex.org": 0.15}
_host_locks: dict[str, threading.Lock] = {}
_host_last: dict[str, float] = {}
_registry_lock = threading.Lock()


def _throttle(host: str) -> None:
    """单 host 串行限速，线程安全（不同 host 可并发）。"""
    with _registry_lock:
        lock = _host_locks.setdefault(host, threading.Lock())
    with lock:
        min_interval = _host_min_interval.get(host, 1.0)
        last = _host_last.get(host)
        now = time.monotonic()
        if last is not None and now - last < min_interval:
            time.sleep(min_interval - (now - last))
        _host_last[host] = time.monotonic()


class ApiUnavailable(Exception):
    """数据库不可达（网络错误 / 持续 429 / 5xx）。调用方据此降级为人工核实。"""


def http_get_json(url: str, timeout: int = _DEFAULT_TIMEOUT) -> dict[str, Any]:
    """GET 一个 JSON 端点并返回解析后的 dict。

    - 404 → 返回空 dict（调用方按"未找到"处理）
    - 网络错误 / 429 重试耗尽 / 5xx → 设 OFFLINE=True 并抛 ApiUnavailable
    """
    global OFFLINE
    host = urllib.parse.urlparse(url).netloc
    headers = {
        "User-Agent": f"paper-workflow/1.0 (mailto:{_POLITE_EMAIL})",
        "Accept": "application/json",
    }
    req = urllib.request.Request(url, headers=headers)

    _throttle(host)
    for attempt in range(_MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {}
            if e.code == 429 and attempt < _MAX_RETRIES:
                time.sleep(_BACKOFF_SECONDS)
                continue
            if 500 <= e.code < 600 and attempt < _MAX_RETRIES:
                time.sleep(_BACKOFF_SECONDS)
                continue
            raise ApiUnavailable(f"{host} HTTP {e.code}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            OFFLINE = True
            raise ApiUnavailable(f"{host} 网络错误: {e}") from e
    raise ApiUnavailable(f"{host} 重试 {_MAX_RETRIES} 次后仍失败")


# =========================================================================
# 五、数据库查询
# =========================================================================

def query_crossref_doi(doi: str, expected_title: str) -> dict[str, Any]:
    """Crossref 按 DOI 查询，返回题名交叉验证结果。

    返回 {"resolved": bool, "title_match": bool, "db_title": str|None}：
      - resolved=False         → DOI 不存在（404）
      - resolved, title_match  → 题名相符
      - resolved, 无 title_match → DOI_MISMATCH（DOI 真实但指向另一篇，疑似张冠李戴）
    """
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='/')}"
    data = http_get_json(url)
    if not data:
        return {"resolved": False, "title_match": False, "db_title": None}
    msg = data.get("message", {})
    titles = msg.get("title") or []
    db_title = titles[0] if titles else ""
    matched = title_similarity(expected_title, db_title) >= TITLE_SIMILARITY_THRESHOLD
    return {"resolved": True, "title_match": matched, "db_title": db_title or None}


def query_openalex_title(title: str, year: int | None = None) -> dict[str, Any]:
    """OpenAlex 题名搜索，取相似度最高且≥阈值的结果，年份匹配加 0.05 分。

    返回 {"hit": bool, "db_title": str|None}。
    """
    # 搜索前剥离版次括号（(2nd ed.) 等），避免拉低检索召回
    search_term = _EDITION_PAT.sub("", title).strip()
    params = {
        "search": search_term, "per-page": "5",
        "select": "id,title,publication_year,authorships,doi",
        "mailto": _POLITE_EMAIL,  # polite pool：更高速率
    }
    url = f"https://api.openalex.org/works?{urllib.parse.urlencode(params)}"
    data = http_get_json(url)
    results = data.get("results", []) or []
    best: tuple[float, dict[str, Any]] | None = None
    for cand in results:
        cand_title = cand.get("title") or ""
        sim = title_similarity(title, cand_title)
        if sim < TITLE_SIMILARITY_THRESHOLD:
            continue
        year_match = year is not None and cand.get("publication_year") == year
        score = sim + (0.05 if year_match else 0.0)
        if best is None or score > best[0]:
            best = (score, cand)
    if best is None:
        return {"hit": False, "db_title": None}
    return {"hit": True, "db_title": best[1].get("title")}
