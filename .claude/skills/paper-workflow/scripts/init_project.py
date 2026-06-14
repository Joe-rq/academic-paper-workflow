"""初始化论文项目：从模板创建项目目录和配置文件。

用法: python init_project.py --name "论文标题" [--type journal-paper] [--author 作者] [--journal 期刊] [--words 8000] [--output-dir ./]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


def slugify(text: str) -> str:
    """中文标题转简短英文 slug。"""
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    return text[:64] if text else "paper-project"


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化论文项目")
    parser.add_argument("--name", required=True, help="论文标题")
    parser.add_argument("--type", default="journal-paper", choices=["journal-paper", "thesis", "essay"])
    parser.add_argument("--author", default="")
    parser.add_argument("--journal", default="")
    parser.add_argument("--words", type=int, default=8000)
    parser.add_argument("--output-dir", default=".", help="输出目录")
    args = parser.parse_args()

    # 定位模板目录
    script_dir = Path(__file__).resolve().parent
    template_dir = script_dir.parent.parent.parent.parent / "templates" / args.type
    if not template_dir.exists():
        print(f"ERROR: 模板不存在: {template_dir}")
        raise SystemExit(1)

    # 目标目录
    output = Path(args.output_dir).resolve()
    if args.output_dir == ".":
        output = output / slugify(args.name)
    output.mkdir(parents=True, exist_ok=True)

    # 复制模板
    for item in template_dir.rglob("*"):
        if item.is_dir():
            (output / item.relative_to(template_dir)).mkdir(exist_ok=True)
        else:
            dest = output / item.relative_to(template_dir)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(item), str(dest))

    # 生成 paper-config.json
    config_path = output / "paper-config.json"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")

    config.update({
        "title": args.name,
        "author": args.author,
        "target": args.journal,
        "type": args.type,
        "word_count": args.words,
        "version": 1,
        "current_stage": "init",
        "stages": {"init": {"status": "done", "at": now, "executor": "internal"}},
    })
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    # 确保必要目录存在
    for d in ["draft", "refs", "figures", "output", "_archive"]:
        (output / d).mkdir(exist_ok=True)

    print(f"项目已创建: {output}")
    print(f"配置文件: {config_path}")
    print(f"下一步: cd {output} && /paper-workflow brainstorm")


if __name__ == "__main__":
    main()
