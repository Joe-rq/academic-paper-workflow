"""为论文 DOCX 添加交叉引用：正文 [n] → 跳转到参考文献第 n 条。

泛化自 add_crossrefs.py，支持自定义参考文献标题。
用法: python build_crossrefs.py --input paper.docx [--output paper_linked.docx] [--ref-heading 参考文献]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
CIT_PAT = re.compile(r"^\[(\d+)\]$")
REF_PAT = re.compile(r"^\[(\d+)\]")


def para_text(p) -> str:
    return "".join(t.text or "" for t in p.iter(f"{{{W}}}t") if t.text)


def main() -> None:
    parser = argparse.ArgumentParser(description="添加引文交叉引用")
    parser.add_argument("--input", required=True, type=Path, help="输入 DOCX")
    parser.add_argument("--output", type=Path, help="输出 DOCX（默认加 _linked 后缀）")
    parser.add_argument("--ref-heading", default="参考文献", help="参考文献节标题")
    args = parser.parse_args()

    inp: Path = args.input.resolve()
    out: Path = args.output.resolve() if args.output else inp.parent / f"{inp.stem}_linked{inp.suffix}"

    print(f"Input:  {inp}")
    print(f"Output: {out}")

    doc = Document(str(inp))
    body = doc.element.body

    # 定位参考文献区域
    refs_idx = None
    paras = body.findall(qn("w:p"))
    for i, p in enumerate(paras):
        if para_text(p).strip() == args.ref_heading:
            refs_idx = i
            break
    if refs_idx is None:
        print(f"ERROR: 未找到参考文献节（标题: '{args.ref_heading}'）")
        raise SystemExit(1)
    print(f"参考文献节位于 P{refs_idx}")

    # 检查已有书签
    existing: set[str] = set()
    max_id = 0
    for bs in body.iter(f"{{{W}}}bookmarkStart"):
        name = bs.get(f"{{{W}}}name", "")
        bid = bs.get(f"{{{W}}}id", "0")
        try:
            bid_int = int(bid)
            if bid_int > max_id:
                max_id = bid_int
        except ValueError:
            pass
        if name.startswith("ref_"):
            existing.add(name)
    print(f"已有 ref_ 书签: {len(existing)}（最大 bookmark id: {max_id}）")

    # 补缺书签
    next_id = max_id + 1
    added_bm = 0
    for i in range(refs_idx + 1, len(paras)):
        text = para_text(paras[i]).strip()
        if text.startswith("附录") or text.startswith("致谢"):
            break
        m = REF_PAT.match(text)
        if not m:
            continue
        bm_name = f"ref_{m.group(1)}"
        if bm_name in existing:
            continue
        bs = OxmlElement("w:bookmarkStart")
        bs.set(qn("w:id"), str(next_id))
        bs.set(qn("w:name"), bm_name)
        be = OxmlElement("w:bookmarkEnd")
        be.set(qn("w:id"), str(next_id))
        paras[i].insert(0, bs)
        paras[i].append(be)
        next_id += 1
        added_bm += 1
        existing.add(bm_name)
    print(f"新增 {added_bm} 个书签（总计 ref_ 书签: {len(existing)}）")

    # 正文引用转超链接
    link_count = 0
    for i in range(refs_idx):
        p = paras[i]
        runs = list(p.findall(qn("w:r")))
        for run in runs:
            text = "".join(t.text or "" for t in run.findall(qn("w:t")) if t.text)
            if not text:
                continue
            m = CIT_PAT.match(text.strip())
            if not m:
                continue
            anchor = f"ref_{m.group(1)}"
            if anchor not in existing:
                continue
            hl = OxmlElement("w:hyperlink")
            hl.set(qn("w:anchor"), anchor)
            run.addprevious(hl)
            hl.append(run)
            link_count += 1

    print(f"转换 {link_count} 个引用为超链接")
    doc.save(str(out))
    print(f"已保存: {out}")


if __name__ == "__main__":
    main()
