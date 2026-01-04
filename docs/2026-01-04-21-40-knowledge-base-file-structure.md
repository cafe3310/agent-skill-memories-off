# 知识库文件结构文档

本文档详细描述了 `mcp-server-memories-off` 项目所管理的知识库（Library）在本地文件系统中的标准目录结构和文件格式。

---

## 1. 顶层目录结构

一个知识库（`Library`）是一个独立的顶层文件夹，其内部包含以下标准的目录和文件：

```
[知识库根目录]/
├── meta.md
├── entities/
├── trash/
├── backups/
└── journeys/
```

以下是一个更具体的知识库（名为 `MyNotes`）结构示例：

```
MyNotes/
├── meta.md
├── entities/
│   ├── ConceptA.md
│   ├── PersonB.md
│   └── Meeting-2026-01-04.md
├── trash/
│   └── 2026-01-04-21-45-00_OldConcept.md
├── backups/
│   └── backup_2026-01-04-22-00-00_MyNotes.zip
└── journeys/
```

### 1.1. `meta.md`

- **功能**: 知识库的“手册”文件。
- **描述**: 这是一个强制性的 Markdown 文件，用于存放整个知识库的元数据、描述信息、使用指南或配置。项目提供了 `readManual` 和 `editManual` 工具来读取和修改此文件的内容。

### 1.2. `entities/` 目录

- **功能**: 存放所有知识实体（Entity）文件。
- **描述**: 这是知识库的核心内容目录。每个知识实体都以一个独立的 Markdown 文件（`.md`）形式存储在此处。

- **命名规范 (自动格式化)**:
    - **文件名构成**: 实体文件名由创建时提供的 `entityName` 经过自动格式化处理后，加上 `.md` 后缀组成。
    - **格式化规则**:
        1.  **允许的字符**: 文件名仅允许包含 CJK 字符、英文字母、数字和中横线 (`-`)。
        2.  **非法字符替换**: 任何不在允许范围内的字符（例如空格、中英文标点符号）都会被自动替换为单个中横线 (`-`)。
        3.  **合并中横线**: 连续的多个中横线会被合并为一个。
        4.  **清理首尾**: 文件名头部和尾部的中横线会被移除。
    - **示例**: 如果提供的 `entityName` 是 `Hello, World! (世界你好)`，系统会自动将其格式化为 `Hello-World-世界你好`，最终文件名为 `Hello-World-世界你好.md`。

### 1.3. `trash/` 目录

- **功能**: 回收站。
- **描述**: 当通过 `deleteEntities` 工具删除一个实体时，系统会通过在文件名前附加时间戳（格式为 `YYYY-MM-DD-HH-MM-SS`）的方式重命名文件，然后再将其移入此目录。
- **防重复与排序**: 这种 `[时间戳]_[原文件名].md` 的重命名机制有两个目的：
    1.  **避免冲突**: 即使多次删除同名文件，在回收站中也会保存为带有不同时间戳的独立文件，确保数据不被覆盖。
    2.  **自然排序**: 这种格式使得在文件管理器中，被删除的文件会自然地按照删除时间进行排序。
- **示例**: 删除 `MyConcept.md` 后，它在回收站中可能被保存为 `2026-01-04-21-45-00_MyConcept.md`。

### 1.4. `backups/` 目录

- **功能**: 存放备份文件。
- **描述**: `backupLibrary` 工具会创建整个知识库的压缩备份文件，并存储在此目录中。
- **文件名格式**: 备份文件的命名格式为 `backup_[时间戳]_[知识库名称].zip`。其中时间戳格式为 `YYYY-MM-DD-HH-MM-SS`。
- **示例**: 如果知识库名为 `MyNotes`，备份文件可能为 `backup_2026-01-04-22-00-00_MyNotes.zip`。

### 1.5. `journeys/` 目录

- **功能**: 记录编辑日志（Journal）。
- **描述**: 此目录旨在用于存放文件的编辑历史或日志。尽管在类型定义中存在 `FileTypeJourney`，但相关功能目前尚未完全实现。

---

## 2. 实体文件结构 (`entities/[实体名称].md`)

每个位于 `entities/` 目录下的实体文件都是一个遵循特定结构的 Markdown 文件。

### 2.1. Front Matter (元数据)

- **功能**: 定义实体的结构化元数据。
- **描述**: 每个实体文件的顶部都必须包含一个 [YAML](https://yaml.org/) Front Matter 块，由一对 `---` 分隔。这里存储了实体的核心属性，工具（如 `findEntitiesByMetadata`, `createRelations`）依赖这些元数据进行查询和关联。

- **预设键名**:
    - `entity type`: (代码中定义为 `EntityType`) 实体的类型，值以逗号分隔多个类型。例如：`entity type: Person`, `entity type: Location, Organization`。
    - `date modified`: (代码中定义为 `DateModified`) 实体的修改日期。例如：`date modified: 2024-01-01`。
    - `date created`: (代码中定义为 `DateCreated`) 实体的创建日期。例如：`date created: 2023-12-31`。
    - `aliases`: (代码中定义为 `Aliases`) 实体的别名列表，值以逗号分隔多个别名。例如：`aliases: alias1, alias2`。
    - `relation as`: (代码中定义为 `RelationAs`) 用于定义实体间的关系。其键名通常以 `relation as` 为前缀，后接关系类型；值为关联实体名称。例如：`relation as member: team_name`, `relation as project developer: project_name`。

- **示例**:
  ```yaml
  ---
  entity type: concept, AI Agent
  date modified: 2026-01-04
  date created: 2025-12-25
  aliases: AI, Intelligent Agent
  relation as core concept of: Large Language Model
  status: draft  # 自定义键名示例
  ---
  ```

### 2.2. Body (正文)

- **功能**: 存储实体的非结构化内容。
- **描述**: Front Matter 之后的部分是实体的主体内容，使用标准 Markdown 格式编写。
- **章节 (Sections)**:
    - **组织方式**: 正文内容可以通过 Markdown 标题 (`#`, `##`, `###`, 等) 来组织成逻辑上的章节（`Section`）。**此外，实体内容也可以是纯文本，不包含任何章节结构。** 项目提供了多种工具（如 `getEntitiesToc`, `readEntitiesSections`, `replaceEntitySection`）来读取和操作这些章节。
    - **结构规范**: 对于特定类型的实体，其章节的组织结构（即 TOC 结构）应遵循该知识库根目录下 `meta.md` 文件中的相关规定或模板。这确保了同类型实体拥有一致的内容结构。

- **示例**:

  有 toc 的实体文件示例：

  ```markdown
  # 大型语言模型 (LLM)

  这是一个关于大型语言模型的核心概念实体。

  ## 核心能力

  已知的大型语言模型核心能力包括自然语言理解和生成。我们可以利用这些能力来构建各种应用。

  ## 已知应用

  - 聊天机器人
  - 文本摘要
  - 代码生成
  ```

    无 toc 的实体文件示例：
    
    ```markdown
    这是一个关于人工智能代理的实体文件。人工智能代理是一种能够自主执行任务的软件系统，通常具备学习和适应能力。
    ```
