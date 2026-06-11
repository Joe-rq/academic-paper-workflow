"""引文校验：检测 Markdown 论文中的引文编号问题。

用法: python validate_citations.py --input paper.md
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def validate(md_text: str) -> dict:
    """检查引文编号一致性。"""
    # 正文中的引用：^[n] 或 <sup>[n]</sup>
    cited = sorted(set(
        int(n)
        for match in re.finditer(r"\^\[(\d+)\]|<sup>\[(\d+)\]</sup>", md_text)
        for n in match.groups() if n
    ))
    # 参考文献定义：行首 [n]
    refs = sorted(set(
        int(m.group(1))
        for m in re.finditer(r"^\[(\d+)\]\s+", md_text, flags=re.MULTILINE)
    ))
    return {
        "cited": cited,
        "refs": refs,
        "missing_refs": sorted(set(cited) - set(refs)),
        "uncited_refs": sorted(set(refs) - set(cited)),
    }


def main() -> None:
    # Windows 控制台默认 gbk，emoji 会触发 UnicodeEncodeError；强制 utf-8 输出
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass  # Python <3.7 或 stdout 已重定向到文件
    parser = argparse.ArgumentParser(description="引文校验")
    parser.add_argument("--input", required=True, type=Path, help="Markdown 文件")
    args = parser.parse_args()

    md_text = args.input.read_text(encoding="utf-8")
    result = validate(md_text)

    print(f"正文引用: {result['cited']}")
    print(f"参考文献: {result['refs']}")

    issues = 0
    if result["missing_refs"]:
        print(f"⚠ 缺失引用（被引用但未定义）: {result['missing_refs']}")
        issues += len(result["missing_refs"])
    if result["uncited_refs"]:
        print(f"⚠ 未引用（已定义但未被引用）: {result['uncited_refs']}")
        issues += len(result["uncited_refs"])

    if issues == 0:
        print("✓ 引文校验通过")
    else:
        print(f"✗ 发现 {issues} 个引文问题")
        sys.exit(1)


if __name__ == "__main__":
    main()
