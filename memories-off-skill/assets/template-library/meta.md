# Knowledge Base Manual (meta.md)

## 1. 概述 (Overview)
这是一个遵循 `memories-off` 规范的模板知识库，用于演示标准结构、元数据 schema 和编辑准则。

## 2. 核心 Schema (Core Schema)
### Entity Types:
- `Person`: 用于记录人物信息、偏好及与其相关的事件。
- `Concept`: 用于记录抽象概念、定义及逻辑推演。
- `Project`: 用于追踪项目进度、目标和决策。
- `Journal`: 记录按时间顺序排列的事件或思考。

### Metadata Keys:
- `entity type`: 必须项。
- `date created`, `date modified`: 自动维护项。
- `status`: 生命周期（`draft`, `stable`, `archived`）。
- `aliases`: 别名，逗号分隔。

## 3. 关系定义 (Relations)
### 常用谓词 (Common Predicates):
- `member of`: 指向组织或团队。
- `instance of`: 指向其所属的父类或抽象概念。
- `interested in`: 兴趣领域。
- `managed by`: 指向负责人。

## 4. 命名与编辑准则
- 实体文件名：使用 `[Type]-[Name]` 或 `[Name]`，字符仅限 CJK、英文字母、数字和中横线。
- 章节引用：使用 `# 标题内容`，编辑时必须精确匹配。
