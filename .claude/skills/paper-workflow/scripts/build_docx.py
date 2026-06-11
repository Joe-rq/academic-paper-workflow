"""构建 DOCX：读取配置，委托 md-to-docx skill 进行转换。

用法: python build_docx.py [--config paper-config.json] [--with-crossrefs]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def find_skill_script(script_name: str) -> Path | None:
    """在常见位置搜索 md-to-docx skill 的脚本。"""
    candidates = [
        Path.home() / ".claude" / "skills" / "md-to-docx" / "scripts" / script_name,
        Path.home() / ".claude" / "skills" / "md-to-docx" / script_name,
    ]
    # 项目级 skill
    for p in Path.cwd().rglob(f"**/md-to-docx/**/{script_name}"):
        candidates.append(p)
    for c in candidates:
        if c.exists():
            return c
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="构建 DOCX")
    parser.add_argument("--config", type=Path, default=Path("paper-config.json"))
    parser.add_argument("--with-crossrefs", action="store_true", help="添加交叉引用")
    args = parser.parse_args()

    config_path = args.config.resolve()
    if not config_path.exists():
        print(f"ERROR: 配置文件不存在: {config_path}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    build = config.get("build", {})
    md_input = (config_path.parent / build.get("input", "draft/paper.md")).resolve()
    output_dir = (config_path.parent / build.get("output_dir", "output/")).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    version = config.get("version", 1)
    title_slug = config.get("title", "paper")[:20]
    out_path = output_dir / f"{title_slug}_v{version}.docx"

    if not md_input.exists():
        print(f"ERROR: 源文件不存在: {md_input}")
        raise SystemExit(1)

    # 查找 md-to-docx skill 脚本
    skill_script = find_skill_script("build_academic_docx.py")
    if skill_script:
        print(f"使用 md-to-docx skill: {skill_script}")
        result = subprocess.run(
            [sys.executable, str(skill_script), "--input", str(md_input), "--output", str(out_path)],
            capture_output=True, text=True,
        )
        print(result.stdout)
        if result.returncode != 0:
            print(f"ERROR: {result.stderr}")
            raise SystemExit(1)
    else:
        print("WARNING: 未找到 md-to-docx skill，尝试直接使用 pandoc")
        result = subprocess.run(
            ["pandoc", str(md_input), "-o", str(out_path)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"ERROR: pandoc 失败且未找到 md-to-docx skill")
            print("请安装 md-to-docx skill 或 pandoc")
            raise SystemExit(1)

    # 可选交叉引用
    if args.with_crossrefs and out_path.exists():
        crossrefs_script = Path(__file__).parent / "build_crossrefs.py"
        if crossrefs_script.exists():
            linked_path = output_dir / f"{title_slug}_v{version}_linked.docx"
            subprocess.run(
                [sys.executable, str(crossrefs_script), "--input", str(out_path), "--output", str(linked_path)],
                capture_output=True, text=True,
            )
            out_path = linked_path

    if out_path.exists():
        size = out_path.stat().st_size
        print(f"构建完成: {out_path} ({size:,} bytes)")
    else:
        print("ERROR: 构建失败")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
