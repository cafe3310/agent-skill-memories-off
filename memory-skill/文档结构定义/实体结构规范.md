# 文档结构定义: Entity Structure

本文档定义了 `memory-skill` 中实体文件的标准 Markdown 结构，旨在确保数据的机器可读性和人类可维护性。

---

## 1. 结构概览 (Structure Overview)

每个实体文件由两个核心部分组成：**Front Matter (元数据区)** 和 **Body (正文内容区)**。

```markdown
---
[Metadata Key]: [Value]
---

# [Heading 1]

[Content Block]

## [Sub-heading]

[Content Block]
```

## 2. Front Matter (元数据区)

### 2.1 规范要求
- **格式**: 必须位于文件最顶部，由一对 `---` 分隔。
- **内容**: 仅限一级键值对，不支持嵌套对象。
- **行布局**: 每个条目必须独立占据一行，格式为 `Key: Value`。

### 2.2 核心元数据 (Core Metadata)
- **`entity type`**: 指定实体的分类（如 `Person`, `Concept`, `Project`）。
- **`date modified`**: 记录实体的最后修改日期（格式：`YYYY-MM-DD`）。
- **`date created`**: 记录实体的创建日期。
- **`aliases`**: 实体的替代名称（别名），以逗号分隔。
- **`relation as [type]`**: 显式定义与另一个实体的关系（详见 [关联定义](../关联定义/relation-types.md)）。

## 3. Body (正文内容区)

### 3.1 章节结构 (Sections & Headings)
- **Heading (标题)**: 仅指 Markdown 的标题行（如 `# Title`）。必须精确定义层级（1-6）。
- **Section (章节)**: 一个逻辑单元，由一个 `Heading` 及其下属的所有文本（`Content`）组成。
- **TOC (目录)**: 整个文件中所有 `Heading` 的有序列表。

### 3.2 内容块 (Content Block)
- **Line (行)**: 内容的最基本单位。
- **Content (文本块)**: 由多行 `Line` 组成的字符串数组。

## 4. 解析协议 (Parsing Protocol)

Agent 在操作文档时应遵循以下逻辑：
- **Locate (定位)**: 首先通过 `ThingLocator` 找到物理文件。
- **Parse (解析)**: 将文件解析为包含元数据、章节及完整行列表的 `Document` 结构。
- **Edit (编辑)**: 优先通过 `Heading` 或 `ContentLocator` 定位精确位置进行增删改，而非全量重写。
