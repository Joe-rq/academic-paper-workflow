"""论文图表生成模板。

使用 matplotlib 生成论文配图，支持中文字体、300dpi 输出。
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# 中文字体配置
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

OUTPUT_DIR = Path(__file__).parent
DPI = 300
FIGSIZE = (10, 6.67)  # 1800x1200 @ 150dpi, 输出 300dpi → 3000x2000px


def generate_sample_figure():
    """生成样例柱状图，实际使用时替换数据和标签。"""
    categories = ["类别A", "类别B", "类别C", "类别D"]
    before = [60, 45, 55, 40]
    after = [85, 78, 82, 75]

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.bar(x - width / 2, before, width, label="课前", color="#6C8EBF", edgecolor="white")
    ax.bar(x + width / 2, after, width, label="课后", color="#82B366", edgecolor="white")

    ax.set_ylabel("得分（分）", fontsize=12)
    ax.set_title("图1  学生课前课后能力对比", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11)
    ax.legend(fontsize=11)
    ax.set_ylim(0, 100)

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    fig.tight_layout()
    out_path = OUTPUT_DIR / "fig1_sample.png"
    fig.savefig(str(out_path), dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"已生成: {out_path}")


if __name__ == "__main__":
    generate_sample_figure()
