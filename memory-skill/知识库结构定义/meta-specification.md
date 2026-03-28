# 知识库结构定义: Meta Specification (meta.md)

本文档定义了知识库核心手册 `meta.md` 的内部结构规范。`meta.md` 是 Agent 理解知识库上下文、规则和 Schema 的首要入口。

---

## 1. 核心目标 (Goals)

- **上下文对齐**: 为 Agent 提供关于知识库用途的全局描述。
- **Schema 定义**: 集中定义该库所采用的实体类型、元数据字段及其含义。
- **规则约束**: 规定 Agent 在此库中进行编辑、命名或关联时应遵循的特定指导原则。

## 2. 标准章节结构 (Standard Sections)

建议 `meta.md` 包含以下章节，以确保 Agent 能够系统地获取信息：

### 2.1 `# 全局描述 (Global Description)`
- 简述该知识库的主题（如“个人笔记”、“项目 A 的技术文档”）。
- 明确知识库的受众和主要用途。

### 2.2 `# 实体类型定义 (Entity Types)`
- 详细列出该库中使用的 `entity type` 及其适用场景。
- **示例**:
  - `Person`: 用于记录项目团队成员和合作伙伴。
  - `Meeting`: 用于记录周会、技术评审会。

### 2.3 `# 元数据规范 (Metadata Schema)`
- 如果该库使用了 `memory-skill` 预设字段以外的自定义字段，应在此说明其含义和取值范围。

### 2.4 `# 章节模板 (Section Templates)`
- 为特定类型的实体定义推荐的目录结构（TOC）。
- **示例**: “对于 `Meeting` 类型的实体，应包含 `## 议题`, `## 决策`, `## 待办事项` 三个章节。”

### 2.5 `# 指导原则与约束 (Guidelines & Constraints)`
- 定义特定的命名偏好（如“使用中文作为实体名”）。
- 定义关联偏好（如“人与任务之间必须建立 `assigned to` 关系”）。

## 3. 维护规范 (Maintenance Rules)

- **原子化更新**: 使用 `addManualSection` 或 `replaceManualSection` 进行定向修改，避免全量覆盖。
- **动态演进**: 随着知识库的发展，Agent 应根据用户的最新要求或发现的新模式，建议并更新 `meta.md`。
- **自描述性**: 手册内容应保持简洁、清晰，直接供 LLM 提示词参考。

## 4. 缺失处理 (Missing File Handling)

- 若知识库中不存在 `meta.md`，Agent 应在初次初始化时自动创建一个包含基础框架的默认文件。
- 默认框架应至少包含 `# 全局描述` 标题。
