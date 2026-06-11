# Skill 集成指南

本工作流通过引用已有 skill 完成各阶段工作。本文档说明如何安装和配置这些 skill。

## 内置 Skill（无需安装）

以下 skill 随项目自带，开箱即用：

### paper-review-team（多 agent 评审）

**用途**：Stage 7 同行评审的多 agent 增强执行器

**说明**：组建 4 个真正独立的评审 agent 并行评审（主编/方法论专家/领域专家/魔鬼代言人），突破单 agent 串行扮演的"伪独立"。评审维度引用 `paper-workflow/references/peer-review-simulation.md`，不重复定义。

**调用方式**：

```bash
/paper-review-team draft/paper.md
```

---

## 必需 Skill

### 1. deep-research（文献研究）

**用途**：Stage 3 文献研究

**安装**：
```bash
# 通过 42plugin 安装
/42plugin install academic-research-skills
```

**调用方式**：
```bash
/deep-research "[研究主题]"
```

### 2. academic-paper（写作引擎）

**用途**：Stage 5 分节写作

**安装**：同上，academic-research-skills 包含

**调用方式**：
```bash
/academic-paper write --outline draft/paper.md
```

### 3. academic-paper-reviewer（同行评审）

**用途**：Stage 7 同行评审

**安装**：同上

**调用方式**：
```bash
/academic-paper-reviewer draft/paper.md
```

### 4. md-to-docx（文档构建）

**用途**：Stage 9 md→docx 转换

**安装**：本地 skill，已存在于 `.claude/skills/md-to-docx/`

**调用方式**：通过 `scripts/build_docx.py` 委托调用

## 可选 Skill

### 5. humanizer-cn（降 AI 检测）

**用途**：Stage 7-8 降低 AI 生成检测率

**安装**：
```bash
/42plugin install humanizer-cn
```

### 6. color-font-skill（文档配色）

**用途**：Stage 9 文档视觉设计

**安装**：本地 skill

### 7. academic-pipeline（全流程编排）

**用途**：无人值守的全自动写作模式

**安装**：包含在 academic-research-skills 中

## 依赖检查

运行以下命令检查所有依赖是否就绪：

```bash
/paper-workflow doctor
```

输出示例：
```
✓ deep-research     — 已安装 (v2.9.4)
✓ academic-paper    — 已安装 (v3.1.2)
✓ academic-paper-reviewer — 已安装 (v1.9.1)
✓ md-to-docx        — 已安装 (v2.0.0)
✗ humanizer-cn      — 未安装 (可选)
✓ color-font-skill  — 已安装
```

## Python 依赖

构建脚本需要以下 Python 包：

```bash
uv sync  # 安装 pyproject.toml 中的依赖
```

依赖清单：
- `python-docx` — Word 文档操作
- `matplotlib` — 图表生成
- `pillow` — 图片处理

## Node.js 依赖（可选）

如果使用 PPT 生成功能：

```bash
cd slides && npm install  # 安装 pptxgenjs
```
