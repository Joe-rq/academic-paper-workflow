# -*- coding: utf-8 -*-
"""参考文献验证：检测 AI 编造文献。

两道互补检查：
  Check A（格式合规，确定性）—— GB/T 7714 五阶段解析 + 三档规则
  Check B（存在性验证，尽力而为）—— 按"实际可验证性"分层查询学术数据库

诚实的设计：中文职教期刊多无 DOI，OpenAlex/Crossref 收录不全。因此
  - DOI_MISMATCH（DOI 真实但题名不符）= 最强防伪造信号（疑似张冠李戴/缝合）
  - 中文文献 OpenAlex 未命中 ≠ 编造，标"需人工核实"（建议知网/万方）
  - [S]/[Z]/[EB-OL] 标准政策网络资源 = 跳过（设计上不可库验）

用法:
  python verify_references.py --input paper.md              # 完整验证（在线）
  python verify_references.py --input paper.md --offline     # 仅格式校验（离线）
  python verify_references.py --input paper.md --json        # JSON 输出
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import _academic_db
from _academic_db import (
    ApiUnavailable,
    extract_doi,
    normalize_reference,
    query_crossref_doi,
    query_openalex_title,
)
from validate_citations import validate as check_numbering

# GB/T 7714 类型标签（含复合型 EB/OL 等）
_TYPE_TAG_PAT = re.compile(r"\[([A-Z]+(?:/[A-Z]+)?)\]")
# 不进数据库验证的类型：标准[S]/政策[Z]/网络[EB-OL]/报告[R]/专利[P]/档案[A]
_NON_DB_TYPES = {"S", "Z", "R", "P", "A", "EB", "DB", "CP", "EB/OL", "DB/OL", "CP/OL"}
_YEAR_PAT = re.compile(r"\b(19\d{2}|20\d{2})\b")
_DOI_FORMAT_PAT = re.compile(r"^10\.\d{4,9}/\S+$")
_REF_LINE_PAT = re.compile(r"^\[(\d+)\]\s+(.+)$", re.MULTILINE)
_CURRENT_YEAR = 2026

# 状态标识
S_VERIFIED = "verified"          # ✅ 已核实（DB 命中）
S_SUSPECT = "suspect"            # ❌ 疑似编造（DOI 404）
S_MISMATCH = "mismatch"          # ⚠️ 题名与 DOI 不符（疑似张冠李戴/缝合）
S_MANUAL = "manual"              # ◐ 需人工核实（DB 未收录，建议知网/万方）
S_SKIP = "skip"                  # — 跳过（标准/政策/网络资源）
S_OFFLINE = "offline"            # ◐ 网络不可达，跳过存在性验证
S_FORMAT_ERR = "format_error"    # ✗ 格式错误（Check A HIGH）
S_FORMAT_OK = "format_ok"        # ✓ 格式通过（离线模式，未做存在性验证）

_EMOJI = {
    S_VERIFIED: "✅", S_SUSPECT: "❌", S_MISMATCH: "⚠️",
    S_MANUAL: "◐", S_SKIP: "—", S_OFFLINE: "◐", S_FORMAT_ERR: "✗",
    S_FORMAT_OK: "✓",
}


def extract_references_section(md_text: str) -> list[tuple[int, str]]:
    """提取参考文献节：'# 参考文献' 之后到下一个标题或文末。"""
    lines = md_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^#+\s*参考文献\s*$", line.strip()):
            start = i + 1
            break
    if start is None:
        return []
    refs: list[tuple[int, str]] = []
    for line in lines[start:]:
        s = line.strip()
        if re.match(r"^#+\s", s):  # 下一个标题（附录/致谢等）→ 结束
            break
        m = _REF_LINE_PAT.match(s)
        if m:
            refs.append((int(m.group(1)), m.group(2)))
    return refs


def parse_reference(num: int, body: str) -> tuple[dict, list[tuple[str, str]]]:
    """GB/T 7714 五阶段解析。返回 (字段 dict, 格式问题列表[(级别, 说明)])。"""
    text = normalize_reference(f"[{num}] {body}")
    core = re.match(r"^\[\d+\]\s+(.+)$", text)
    core = core.group(1) if core else text

    issues: list[tuple[str, str]] = []

    # 阶段 3：类型标签
    tag_match = _TYPE_TAG_PAT.search(core)
    tag = tag_match.group(1) if tag_match else None
    if not tag:
        issues.append(("HIGH", "缺少文献类型标签（[J]/[M] 等）"))

    # 阶段 5：年份
    years = _YEAR_PAT.findall(core)
    year = int(years[0]) if years else None
    if not years:
        issues.append(("HIGH", "缺少年份"))
    elif year is not None and (year < 1900 or year > _CURRENT_YEAR + 1):
        issues.append(("HIGH", f"年份越界: {year}"))

    # 阶段 4：作者 + 题名（标签前，按首个 ". " 切分）
    authors = title = ""
    if tag_match:
        before = core[: tag_match.start()].strip()
        authors, sep, title = before.partition(". ")
        authors, title = authors.strip(), title.strip()
        if not authors:
            issues.append(("MEDIUM", "作者字段为空"))
        if not title:
            issues.append(("MEDIUM", "题名字段为空"))

    # DOI（任意位置提取 + 格式校验）
    doi = extract_doi(core)
    if doi and not _DOI_FORMAT_PAT.match(doi):
        issues.append(("HIGH", f"DOI 格式错误: {doi}"))

    # AI 自承认未核实标记检测：方括号内出现"待人工核验/待补充/待确认/待完善"等
    # 短语 → 整条按 HIGH 格式错误处理（等同缺少年份/标签），hard fail 阻断 build
    _UNVERIFIED_MARKERS = re.compile(
        r"\[待人工核验[^\]]*\]|" r"\[待补充[^\]]*\]|" r"\[待确认[^\]]*\]|" r"\[待完善[^\]]*\]"
    )
    unverified = _UNVERIFIED_MARKERS.findall(body)
    if unverified:
        issues.append(("HIGH", f"含 AI 自承认未核实标记: {'; '.join(unverified)}"))

    return {
        "num": num, "raw": body, "normalized": text, "core": core,
        "type": tag, "year": year, "authors": authors, "title": title, "doi": doi,
    }, issues


def check_existence(fields: dict, timeout: int) -> dict:
    """Check B：分层存在性验证。返回 {status, evidence, action}。"""
    tag = fields["type"]
    # Tier 4：标准/政策/网络资源 → 跳过
    if tag in _NON_DB_TYPES:
        return {"status": S_SKIP, "evidence": "标准/政策/网络资源，设计上不可库验",
                "action": "核实原始发布渠道（政府网站等）"}

    title, year, doi = fields["title"], fields["year"], fields["doi"]

    # Tier 1：带 DOI → Crossref DOI 查询 + 题名交叉验证
    if doi:
        try:
            r = query_crossref_doi(doi, title)
        except ApiUnavailable as e:
            return {"status": S_OFFLINE, "evidence": f"查询失败: {e}", "action": ""}
        if not r["resolved"]:
            return {"status": S_SUSPECT, "evidence": f"DOI {doi} 不存在（Crossref 404）",
                    "action": "高度疑似编造，请核实"}
        if r["title_match"]:
            return {"status": S_VERIFIED, "evidence": f"Crossref DOI 命中 + 题名匹配", "action": ""}
        return {"status": S_MISMATCH,
                "evidence": f"DOI 真实但题名不符（库中: {r['db_title'][:40] if r['db_title'] else '?'}）",
                "action": "疑似张冠李戴/缝合，请核实"}

    # 无 DOI：题名搜索（Tier 2 英文 / Tier 3 中文）
    if not title:
        return {"status": S_MANUAL, "evidence": "无法提取题名", "action": "人工核实"}
    is_en = bool(re.match(r"^[A-Za-z]", title))
    try:
        r = query_openalex_title(title, year)
    except ApiUnavailable as e:
        return {"status": S_OFFLINE, "evidence": f"查询失败: {e}", "action": ""}
    if r["hit"]:
        tier = "Tier2 英文" if is_en else "Tier3 中文核心刊"
        return {"status": S_VERIFIED, "evidence": f"OpenAlex 题名命中（{tier}）", "action": ""}
    # 未命中
    if is_en:
        return {"status": S_MANUAL, "evidence": "OpenAlex 未收录该英文文献", "action": "建议 Google Scholar 核实"}
    return {"status": S_MANUAL, "evidence": "OpenAlex 未收录该中文期刊",
            "action": f"建议知网/万方检索: 题名=\"{title[:30]}\""}


def run_check_b(parsed: list[dict], timeout: int, max_parallel: int) -> dict[int, dict]:
    """并发跑 Check B。返回 {num: result}。"""
    results: dict[int, dict] = {}
    todo = [f for f in parsed]  # 全部尝试（含 Tier 4，函数内自行跳过）
    with ThreadPoolExecutor(max_workers=max_parallel) as pool:
        future_map = {pool.submit(check_existence, f, timeout): f["num"] for f in todo}
        for fut in as_completed(future_map):
            num = future_map[fut]
            try:
                results[num] = fut.result()
            except Exception as e:  # 兜底：任何未预期错误降级为人工核实
                results[num] = {"status": S_MANUAL, "evidence": f"验证异常: {e}", "action": "人工核实"}
    return results


def main() -> None:
    # Windows 控制台默认 gbk，emoji 会触发 UnicodeEncodeError；强制 utf-8 输出
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass  # Python <3.7 或 stdout 已重定向到文件
    parser = argparse.ArgumentParser(description="参考文献验证（检测 AI 编造文献）")
    parser.add_argument("--input", required=True, type=Path, help="Markdown 论文文件")
    parser.add_argument("--offline", action="store_true", help="仅格式校验，跳过存在性验证")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--timeout", type=int, default=8, help="单次请求超时秒数")
    parser.add_argument("--max-parallel", type=int, default=3, help="并发查询数")
    args = parser.parse_args()

    md_text = args.input.read_text(encoding="utf-8")

    # 编号检查（informational，不阻断）
    numbering = check_numbering(md_text)
    numbering_issues = len(numbering["missing_refs"]) + len(numbering["uncited_refs"])

    # 提取参考文献
    refs = extract_references_section(md_text)
    if not refs:
        print("✗ 未找到参考文献节（# 参考文献）")
        sys.exit(1)

    # Check A：格式解析（离线确定性）
    parsed: list[dict] = []
    format_issues: dict[int, list] = {}
    for num, body in refs:
        fields, issues = parse_reference(num, body)
        parsed.append(fields)
        format_issues[num] = issues

    # Check B：存在性验证（除非 --offline）
    existence: dict[int, dict] = {}
    ran_online = not args.offline  # 是否尝试了在线验证
    if ran_online:
        existence = run_check_b(parsed, args.timeout, args.max_parallel)

    # 汇总状态：Check A HIGH 错误优先于 Check B
    final: list[dict] = []
    counts: dict[str, int] = {}
    for f in parsed:
        num = f["num"]
        entry = {"num": num, "raw": f["raw"], "type": f["type"], "year": f["year"],
                 "doi": f["doi"], "format_issues": format_issues[num]}
        high = [msg for lvl, msg in format_issues[num] if lvl == "HIGH"]
        if high:
            entry["status"] = S_FORMAT_ERR
            entry["evidence"] = high[0]
            entry["action"] = ""
        elif ran_online and num in existence:
            entry.update(existence[num])
        else:
            # 仅 args.offline 到此：格式通过，未做存在性验证
            entry["status"] = S_FORMAT_OK
            entry["evidence"] = "格式通过（离线模式未验证存在性）"
            entry["action"] = ""
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
        final.append(entry)

    # 退码：HIGH 格式错误 或 疑似编造(DOI 404) 或 DOI_MISMATCH → 1
    hard_fail = (counts.get(S_FORMAT_ERR, 0) + counts.get(S_SUSPECT, 0)
                 + counts.get(S_MISMATCH, 0))

    # ===== 输出 =====
    if args.json:
        output = {
            "input": str(args.input),
            "offline": args.offline or not ran_online,
            "numbering_issues": numbering_issues,
            "total": len(parsed),
            "counts": counts,
            "hard_fail": hard_fail,
            "references": sorted(final, key=lambda e: e["num"]),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(1 if hard_fail > 0 else 0)
    else:
        if numbering_issues:
            print(f"⚠ 编号检查: 缺失{len(numbering['missing_refs'])} 未引用{len(numbering['uncited_refs'])}"
                  f"（不阻断，详见 validate_citations.py）")
        print()
        print("参考文献验证报告")
        print("═" * 60)
        if ran_online:
            machinable = len(parsed) - counts.get(S_SKIP, 0)
            pct = (machinable / len(parsed) * 100) if parsed else 0
            verified_n = counts.get(S_VERIFIED, 0)
            suspicious = counts.get(S_SUSPECT, 0) + counts.get(S_MISMATCH, 0)
            manual = counts.get(S_MANUAL, 0) + counts.get(S_OFFLINE, 0)
            print(f"本次可机器核实: {machinable}/{len(parsed)} ({pct:.0f}%)  "
                  f"| 已核实 {verified_n} | 存疑(疑似编造) {suspicious} "
                  f"| 需人工核实 {manual} | 跳过 {counts.get(S_SKIP, 0)}")
        else:
            print(f"离线/格式模式: 共 {len(parsed)} 条，格式错误 {counts.get(S_FORMAT_ERR, 0)} 个")
        print("═" * 60)
        for e in sorted(final, key=lambda x: x["num"]):
            emoji = _EMOJI.get(e["status"], "?")
            label = {"verified": "VERIFIED", "suspect": "NOT FOUND",
                     "mismatch": "DOI_MISMATCH", "manual": "需人工核实",
                     "skip": "跳过（标准/政策/网络资源）", "offline": "需人工核实(网络不可达)",
                     "format_error": "格式错误", "format_ok": "格式通过"}.get(
                e["status"], e["status"])
            raw_short = e["raw"][:48] + ("…" if len(e["raw"]) > 48 else "")
            print(f"\n[{e['num']}] {raw_short}")
            print(f"    {emoji} {label}")
            if e.get("evidence"):
                print(f"    → {e['evidence']}")
            if e.get("action"):
                print(f"    → {e['action']}")
            meds = [m for lvl, m in e["format_issues"] if lvl != "HIGH"]
            if meds:
                print(f"    (格式提醒: {'; '.join(meds)})")
        print("═" * 60)
        if ran_online and counts.get(S_OFFLINE, 0) > 0:
            print("⚠ 部分查询网络不可达，相应文献已降级为人工核实。")

    if hard_fail > 0:
        print(f"\n✗ 发现 {hard_fail} 个需处理问题（格式错误/疑似编造/题名不符）")
        sys.exit(1)
    print("\n✓ 验证完成（需人工核实的中文文献不阻断）")


if __name__ == "__main__":
    main()
