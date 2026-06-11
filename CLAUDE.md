# CLAUDE.md

## 项目定位

中文学术论文 AI 辅助写作工作流框架。覆盖期刊论文、毕业论文、征文等场景，从"有想法"到"投稿"的完整生命周期。

## 架构

```
academic-paper-workflow/
├── .claude/skills/
│   ├── paper-workflow/             # 主 Skill（10 阶段工作流）
│   │   ├── SKILL.md                # 工作流定义 + 命令表
│   │   ├── references/             # 知识库（写作指南、模板）
│   │   └── scripts/                # 辅助脚本（构建、校验）
│   └── paper-review-team/          # 多 agent 评审团队（Stage 7 增强）
├── templates/                      # 论文项目模板（3 种类型）
└── docs/                           # 架构文档
```

## 工作流阶段

```
init → brainstorm → research → outline → write → figures → review → revise → build → archive
```

## git 规范

- commit message 必须使用**中文**
- 媒体文件（mp3/mp4/png/docx/pptx 等）在 `.gitignore` 排除

## Python 开发规范

- 使用 `uv` 进行包管理，禁止 pip/poetry
- 项目内 `.venv` 虚拟环境

## 技能集成

本工作流通过引用已有 skill 完成各阶段工作，不重复造轮子：

| Skill | 用途 | 阶段 |
|-------|------|------|
| `deep-research` | 文献研究 | Stage 3 |
| `academic-paper` | 写作引擎 | Stage 5 |
| `academic-paper-reviewer` | 同行评审 | Stage 7 |
| `md-to-docx` | md→docx 构建 | Stage 9 |
| `humanizer-cn` | 降 AI 检测 | Stage 7-8 |

> 另有内置 skill `paper-review-team`（多 agent 同行评审，Stage 7 增强），无需安装，调用 `/paper-review-team`。
