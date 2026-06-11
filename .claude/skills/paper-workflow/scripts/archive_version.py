"""版本归档：快照当前论文项目到 _archive/ 目录。

用法: python archive_version.py [--config paper-config.json] [--message "版本说明"]
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="版本归档")
    parser.add_argument("--config", type=Path, default=Path("paper-config.json"), help="配置文件")
    parser.add_argument("--message", default="", help="版本说明")
    args = parser.parse_args()

    config_path = args.config.resolve()
    if not config_path.exists():
        print(f"ERROR: 配置文件不存在: {config_path}")
        raise SystemExit(1)

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    version = config.get("version", 1)
    project_dir = config_path.parent
    archive_dir = project_dir / "_archive" / f"v{version}"

    if archive_dir.exists():
        print(f"WARNING: 归档目录已存在: {archive_dir}")
        print("跳过归档。如需覆盖，请先删除旧归档。")
        return

    archive_dir.mkdir(parents=True, exist_ok=True)

    # 归档关键目录
    for subdir in ["draft", "figures", "refs"]:
        src = project_dir / subdir
        if src.exists():
            shutil.copytree(str(src), str(archive_dir / subdir), dirs_exist_ok=True)

    # 归档配置
    shutil.copy2(str(config_path), str(archive_dir / "paper-config.json"))

    # 写入版本说明
    if args.message:
        (archive_dir / "version-notes.md").write_text(
            f"# v{version}\n\n{args.message}\n", encoding="utf-8"
        )

    # 更新版本号
    config["version"] = version + 1
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"已归档: {archive_dir}")
    print(f"版本号: v{version} → v{version + 1}")


if __name__ == "__main__":
    main()
