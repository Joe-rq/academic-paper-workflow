"""引文校验：检测 Markdown 论文中的引文编号问题。

支持的引用形式（GB/T 7714 及中文学术常见写法）：
  ^[1]                单引
  ^[1,2,3] / ^[1, 2]  多引（英文逗号）
  ^[1，2]             多引（中文逗号，识别但提示改为英文逗号）
  ^[1-3] ^[1－3]      区间（英文/全角连字符）
  ^[1—3] ^[1～3]      区间（中文破折号 / 全角波浪号）
  ^[1,3-5,8]          混合
  <sup>[...]</sup>    所有上述形式的 HTML 等价写法

用法: python validate_citations.py --input paper.md
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# `^[...]` 在中文学术语境里几乎只用于引用，放宽到"括号内任意非换行非右括号"
# 内容由 _parse_cite_group 二次解析；非数字 token 会进 bad_tokens 报告
_CITE_INNER = r"[^\]\n]+"
_CITE_PATTERN = re.compile(rf"\^\[({_CITE_INNER})\]|<sup>\[({_CITE_INNER})\]</sup>")
_RANGE_SEPS = ("-", "－", "—", "～")


def _expand_range(token: str) -> list[int]:
    """'1-3' / '1—3' / '1～3' / '1－3' → [1,2,3]；单数字 → [n]。

    无法解析则抛 ValueError。
    """
    for sep in _RANGE_SEPS:
        if sep in token:
            a, b = token.split(sep, 1)
            start, end = int(a.strip()), int(b.strip())
            if end < start:
                raise ValueError(f"区间倒序: {token}")
            return list(range(start, end + 1))
    return [int(token.strip())]


def _parse_cite_group(inner: str) -> tuple[list[int], list[str]]:
    """解析方括号内部，返回 (展开的编号列表, 无法解析的 token 列表)。"""
    nums: list[int] = []
    bad: list[str] = []
    for token in re.split(r"[,，]", inner):
        token = token.strip()
        if not token:
            continue
        try:
            nums.extend(_expand_range(token))
        except (ValueError, AttributeError):
            bad.append(token)
    return nums, bad


def validate(md_text: str) -> dict:
    """检查引文编号一致性。

    返回字段：
      cited / refs                正文引用集合 / 参考文献定义集合（去重排序）
      missing_refs / uncited_refs 缺失定义 / 未被引用
      compound_groups             识别到的复合引用原文，如 ['1,2,3', '1-5']
      bad_tokens                  无法解析的 token，如 ['abc']
      cn_comma_groups             使用中文逗号的复合引用（兼容识别但建议改为英文逗号）
    """
    cited: set[int] = set()
    compound_groups: list[str] = []
    bad_tokens: list[str] = []
    cn_comma_groups: list[str] = []

    for match in _CITE_PATTERN.finditer(md_text):
        inner = next(g for g in match.groups() if g is not None)
        nums, bad = _parse_cite_group(inner)
        cited.update(nums)
        bad_tokens.extend(bad)
        # 复合 = 多个数字 或 含区间分隔符
        is_compound = len(nums) > 1 or any(sep in inner for sep in _RANGE_SEPS)
        if is_compound:
            compound_groups.append(inner.strip())
        if "，" in inner:
            cn_comma_groups.append(inner.strip())

    refs = sorted(set(
        int(m.group(1))
        for m in re.finditer(r"^\[(\d+)\]\s+", md_text, flags=re.MULTILINE)
    ))
    return {
        "cited": sorted(cited),
        "refs": refs,
        "missing_refs": sorted(cited - set(refs)),
        "uncited_refs": sorted(set(refs) - cited),
        "compound_groups": compound_groups,
        "bad_tokens": bad_tokens,
        "cn_comma_groups": cn_comma_groups,
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
    if result["compound_groups"]:
        # 去重展示，避免一篇文里同样的复合引用刷屏
        uniq = sorted(set(result["compound_groups"]))
        print(f"识别到复合引用 {len(result['compound_groups'])} 处，去重 {len(uniq)} 种: {uniq}")

    issues = 0
    if result["missing_refs"]:
        print(f"⚠ 缺失引用（被引用但未定义）: {result['missing_refs']}")
        issues += len(result["missing_refs"])
    if result["uncited_refs"]:
        print(f"⚠ 未引用（已定义但未被引用）: {result['uncited_refs']}")
        issues += len(result["uncited_refs"])
    if result["bad_tokens"]:
        print(f"⚠ 无法解析的引用 token: {sorted(set(result['bad_tokens']))}")
        issues += len(set(result["bad_tokens"]))

    if result["cn_comma_groups"]:
        # 仅提示，不计入 issues（按规范应改英文逗号但不阻断）
        uniq = sorted(set(result["cn_comma_groups"]))
        print(f"💡 提示：以下复合引用使用了中文逗号（建议改为英文逗号 ','）: {uniq}")

    if issues == 0:
        print("✓ 引文校验通过")
    else:
        print(f"✗ 发现 {issues} 个引文问题")
        sys.exit(1)


if __name__ == "__main__":
    main()
