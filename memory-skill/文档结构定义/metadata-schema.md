# 文档结构定义: Metadata Schema

本文档详细定义了实体 Front Matter 中使用的标准元数据字段（Schema），以确保跨实体的语义一致性。

---

## 1. 核心预设字段 (Core Preset Keys)

下表列出了系统支持的预定义键及其含义：

| 键 (Key) | 描述 | 示例值 |
| :--- | :--- | :--- |
| **`entity type`** | 实体的逻辑分类。支持多个分类，以逗号分隔。 | `Person, Researcher` |
| **`date created`** | 实体文件的最初创建日期。 | `2024-01-01` |
| **`date modified`**| 实体内容的最后修改日期。 | `2024-03-28` |
| **`aliases`** | 实体的替代名称或别名。以逗号分隔。 | `AI, LLM, GPT` |
| **`status`** | 实体的生命周期状态（如 `draft`, `complete`, `deprecated`）。 | `draft` |

## 2. 关系元数据 (Relationship Metadata)

显式语义关系通过特定的 Key 前缀进行定义。

### 2.1 `relation as [type]`
- **职能**: 定义当前实体与目标实体之间的指向关系。
- **格式**: `relation as [谓词]: [目标实体名称]`。
- **示例**:
  - `relation as member of: Ant Group` (表示当前实体是 Ant Group 的成员)。
  - `relation as authored by: John Doe` (表示当前实体由 John Doe 编写)。

## 3. 自定义字段 (Custom Fields)

- **开放性**: 允许用户或 Agent 根据特定知识库的需要添加自定义字段。
- **命名规范**: 建议使用小写字母、数字和下划线，不建议使用特殊字符。
- **索引支持**: 所有自定义字段均可通过 `findEntitiesByMetadata` 工具进行检索。

## 4. 解析与标准化 (Parsing & Normalization)

Agent 在处理 Front Matter 时应遵循以下规则：

### 4.1 键的标准化 (Key Normalization)
- **规则**: 移除 YAML 关键字符号（如 `:`, `-`, `[`, `]`, `{`, `}`, `#`, `&`, `*`, `!`, `|`, `>`, `'`, `"`, `%`, `@`, `` ` ``），将连续空格归一化，并转化为小写。
- **示例**: `  My-Key: ` -> `mykey`。

### 4.2 宽松解析 (Relaxed Parsing)
- 以每行第一个英文冒号 (`:`) 为界分割键值对。
- 若无冒号，则整行作为键，值为空字符串。

### 4.3 合并策略 (Merging Logic)
- **通用原则**: 若键冲突且值不同，新的值应覆盖旧值，或以逗号分隔拼接。
- **特殊字段去重**: 对于 `entity type` 和 `aliases`，合并时必须按逗号分隔，执行全局去重后再重新组合。
- **日期处理**: `date modified` 应始终由最新操作时间覆盖。

## 5. 数据类型规范 (Data Types)

- **String (字符串)**: 默认类型。
- **List (列表)**: 使用英文逗号 (`,`) 分隔的字符串。
- **Date (日期)**: 严格遵循 `YYYY-MM-DD` 格式。

## 6. 存储原则 (Storage Principles)

- **单行存储**: 每个元数据项目必须在一行内完成。
- **不可嵌套**: 禁止在 Front Matter 中使用嵌套的 YAML 结构。
- **同步更新**: 在修改实体内容时，系统通常会自动更新 `date modified` 字段。

