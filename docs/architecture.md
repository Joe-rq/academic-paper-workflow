# 架构说明

## 设计理念

本项目融合三个来源的优秀实践，构建一个可复用的中文学术论文写作工作流：

| 来源 | 继承内容 |
|------|----------|
| 实际论文项目 | 构建链（md→docx、交叉引用、引文校验） |
| thesis-v2 | 四层元架构（认知边界/意图防护/执行可靠/持续优化） |
| codex-claude-academic-skills | 34问头脑风暴、section rhetorical moves、evidence labeling |

## 核心设计决策

### 1. 引用而非复制

本工作流通过**引用已有 skill** 完成各阶段工作，不重复造轮子：

- `deep-research` → 文献研究
- `academic-paper` → 写作引擎
- `academic-paper-reviewer` → 同行评审
- `md-to-docx` → 文档构建
- `humanizer-cn` → AI 检测降低

### 2. Markdown 作为唯一源文件

论文以 Markdown 格式编写，通过构建脚本转换为 Word/PDF。好处：
- 版本管理友好（diff 可读）
- 写作工具无关（任何编辑器都可编辑）
- 格式与内容分离

### 3. 四层元架构确保质量

```
Layer 1: 认知边界层 → 实体约束防止过度生成
Layer 2: 意图防护层 → 三重防护确保输出质量
Layer 3: 执行可靠层 → 看门狗监控进度
Layer 4: 持续优化层 → 模式积累越用越好
```

### 4. 模板驱动初始化

三种论文类型各有完整模板，一键初始化论文项目。

## 数据流

```
project_context.md          paper-config.json
       ↓                          ↓
   头脑风暴产出               项目元数据
       ↓                          ↓
   ┌──────────────────────────────┐
   │        draft/paper.md        │  ← 唯一源文件
   │     (Markdown 论文主稿)       │
   └──────────────────────────────┘
       ↓              ↓            ↓
   figures/        refs/       slides/
   图表生成        参考文献     答辩PPT
       ↓              ↓            ↓
   ┌──────────────────────────────┐
   │       build pipeline         │
   │  md→docx + crossrefs + TOC   │
   └──────────────────────────────┘
       ↓
   output/*.docx  →  投稿文件
```

## 扩展点

- **新增论文类型**：在 `templates/` 下添加新目录，包含 paper-config.json 和 draft/ 骨架
- **新增写作语步**：在 `references/section-rhetorical-moves/` 下添加新的节指南
- **新增构建脚本**：在 `scripts/` 下添加脚本，在 SKILL.md 中注册新命令
- **集成新 Skill**：在 SKILL.md 的命令表中添加新行
