# 工具状态报告 (2026-01-01)

本文档分析了 `mcp-server-memories-off` 项目中所有已设计的工具，并根据其源代码和自动化测试覆盖情况，评估了它们的开发和验证状态。

---

## 1. 所有已设计的工具列表

以下是根据 `src/v2/tools/` 目录下的代码分析出的所有工具：

### 实体管理 (`entity.ts`)
- `addEntities`: 创建一个新的或多个实体。
- `deleteEntities`: 删除一个或多个实体。
- `readEntities`: 读取一个或多个实体的内容。
- `listEntities`: 根据 glob 模式列出实体。
- `getEntitiesToc`: 获取一个或多个实体的目录（TOC）。
- `renameEntity`: 重命名实体并更新关联。
- `readEntitiesSections`: 读取实体中的特定章节。
- `addEntityContent`: 在实体章节中追加内容。
- `deleteEntityContent`: 从实体章节中删除内容。
- `replaceEntitySection`: 替换实体中的整个章节。
- `mergeEntities`: 将多个源实体合并到一个目标实体。
- `garbageCollectRelations`: (未完成) 清理指向不存在实体的关系。

### 关系管理 (`relation.ts`)
- `createRelations`: 批量添加关系。
- `deleteRelations`: 批量删除关系。

### 检索与查询 (`retrieval.ts`)
- `listEntityTypes`: 列出所有实体类型及其数量。
- `findEntitiesByMetadata`: 根据元数据搜索实体。
- `searchInContents`: 在实体正文内容中搜索。
- `findRelations`: (未完成) 查找关系。
- `searchAnywhere`: (未完成) 在任何地方进行全局搜索。

### 知识库手册 (`manual.ts`)
- `readManual`: 读取知识库的 `meta.md` 手册。
- `editManual`: 编辑 `meta.md` 手册的内容。

### 备份 (`backup.ts`)
- `backupLibrary`: 备份整个知识库。

---

## 2. 已完成开发和验证的工具

以下工具均有对应的自动化测试（主要在 `src/test/e2e/` 和 `src/v2/tools/`），并且测试用例覆盖了其核心功能、成功和失败的场景。这些工具被认为是稳定且可用的。

- **`backupLibrary`**
- **`addEntities`**
- **`deleteEntities`**
- **`readEntities`**
- **`listEntities`**
- **`getEntitiesToc`**
- **`renameEntity`**
- **`readEntitiesSections`**
- **`addEntityContent`**
- **`deleteEntityContent`**
- **`replaceEntitySection`**
- **`mergeEntities`**
- **`readManual`**
- **`editManual`**
- **`createRelations`**
- **`deleteRelations`**
- **`listEntityTypes`**
- **`findEntitiesByMetadata`**
- **`searchInContents`**

---

## 3. 尚未完成开发或验证的工具

以下工具在代码中明确标记为“未实现”，或者缺乏相应的自动化测试来验证其功能。

- **`garbageCollectRelations`**:
  - **状态**: 未实现。
  - **代码位置**: `src/v2/tools/entity.ts`
  - **说明**: 工具的处理器函数直接返回一个“未实现”的消息。

- **`findRelations`** (别名 `find_relations`):
  - **状态**: 未实现。
  - **代码位置**: `src/v2/tools/retrieval.ts`
  - **说明**: 工具的处理器函数返回一个“未完全实现”的占位符消息。Git 历史也表明该功能的实现曾被回滚。

- **`searchAnywhere`** (别名 `search_anywhere`):
  - **状态**: 未实现。
  - **代码位置**: `src/v2/tools/retrieval.ts`
  - **说明**: 工具的处理器函数直接返回一个“未实现”的消息。

---

## 4. 代码分层结构与核心功能

本仓库的代码遵循一个清晰的分层结构，从底层的通用函数到高层的工具接口，逐层构建。

### Level 0: 基础工具与类型定义 (Utilities & Types)
这是最底层，提供全局可用的基础能力。

- src/typings.ts: (仅类型定义) -> types, 功能: 定义了整个项目核心的数据结构和 TypeScript 类型。
- src/utils.ts:
    - globToRegex - (glob: string) -> RegExp, 功能: 将 glob 模式转换为正则表达式。
- src/v2/editor/text.ts:
    - normalize - (text: string) -> string, 功能: 归一化文本（转为小写、去除多余空格）。
    - normalizeReason - (reason?: string) -> string, 功能: 归一化提供的原因字符串，使其适合作为 XML 标签属性。

### Level 1: 核心文件操作层 (File Operations)
这一层封装了对文件系统的直接读写操作，是连接代码与本地文件的桥梁。

- src/v2/editor/file-ops.ts:
    - createFile - (libraryName, fileType, entityName, content) -> void, 功能: 在指定位置创建一个新文件。
    - readFileLines - (libraryName, fileType, entityName) -> string[], 功能: 按行读取指定文件的全部内容。
    - writeFileLines - (libraryName, fileType, entityName, lines) -> void, 功能: 将行数组覆盖写入到指定文件。
    - moveFileToTrash - (libraryName, fileType, entityName) -> void, 功能: 将指定文件移动到知识库的回收站目录。
    - renameFile - (libraryName, fileType, oldName, newName) -> void, 功能: 重命名一个文件。

### Level 2: 抽象编辑与检索层 (Editing & Retrieval Logic)
基于核心文件操作，这一层实现了更复杂的、面向业务的逻辑。

- src/v2/editor/front-matter.ts:
    - readFrontMatterLines - (libraryName, fileType, entityName) -> string[] | null, 功能: 读取文件头部定义的 Front Matter。
    - writeFrontMatterLines - (libraryName, fileType, entityName, frontMatter) -> void, 功能: 将 Front Matter 数据写入文件（会覆盖原有数据）。
    - mergeFrontmatter - (target[], source[]) -> string[], 功能: 合并两个 Front Matter 数组，处理重复项。
- src/v2/editor/toc.ts:
    - getTocList - (libraryName, fileType, entityName) -> TocItem[], 功能: 解析文件内容，返回一个包含所有标题（H1-H6）的目录结构列表。
- src/v2/editor/editing.ts:
    - splitFileIntoSections - (libraryName, fileType, entityName) -> Section[], 功能: 将整个文件按 Markdown 标题拆分为多个章节对象。
    - add - (libraryName, fileType, entityName, contentLines) -> void, 功能: 在文件末尾追加新的内容行。
    - replace - (libraryName, fileType, entityName, block, newContent) -> void, 功能: 在文件中查找并替换一个精确匹配的内容块。
    - addInToc - (libraryName, fileType, entityName, toc, newContent) -> void, 功能: 在指定的章节末尾追加内容。
    - deleteInToc - (libraryName, fileType, entityName, toc, contentToDelete) -> void, 功能: 从指定的章节中精确删除一段内容。
    - replaceSection - (libraryName, fileType, entityName, oldHeading, newHeading, newBody) -> void, 功能: 完整替换一个章节，可同时更新标题和正文。
    - readSectionContent - (libraryName, fileType, entityName, toc) -> string[] | null, 功能: 读取指定章节的正文内容。
- src/v2/retrieval/retrieval.ts:
    - findEntityByNameGlob - (libraryName, globPattern) -> string[], 功能: 根据文件名 glob 模式查找实体。
    - findEntityByFrontMatterRegex - (libraryName, fileNamePattern, frontMatterPattern) -> object[], 功能: 使用正则表达式在文件的 Front Matter 中进行搜索。
    - findEntityByNonFrontMatterRegex - (libraryName, fileNamePattern, nonFrontMatterPattern) -> object[], 功能: 使用正则表达式在文件的正文内容中进行搜索。
    - findEntitiesByMetadataQuery - (libraryName, query) -> object, 功能: 根据多个元数据键值对进行组合查询。
    - listAllEntityTypesWithCounts - (libraryName) -> object[], 功能: 统计并列出知识库中所有实体类型及其数量。

### Level 3: 高阶工具接口层 (Tooling Interface)
这是暴露给大型语言模型（LLM）的直接接口。这一层的每个模块都定义了一个或多个“工具”。

- backupLibrary - ({libraryName}) -> string, 功能: 将指定的知识库完整地压缩备份。
- addEntities - ({libraryName, entity, reason?}) -> string, 功能: 批量创建新的知识实体文档。
- deleteEntities - ({libraryName, entityNames, reason?}) -> string, 功能: 软删除一个或多个知识实体。
- readEntities - ({libraryName, entityNames, reason?}) -> string, 功能: 读取一个或多个知识实体的完整内容。
- listEntities - ({libraryName, entityNameGlobs, reason?}) -> string, 功能: 使用 glob 模式列出实体名称。
- getEntitiesToc - ({libraryName, entityNames, reason?}) -> string, 功能: 获取一个或多个实体文档的目录 (TOC)。
- renameEntity - ({libraryName, oldName, newName, reason?}) -> string, 功能: 重命名实体并自动更新所有指向它的链接。
- readEntitiesSections - ({libraryName, entityNames, sectionGlobs, reason?}) -> string, 功能: 精确读取实体中特定章节的内容。
- addEntityContent - ({libraryName, entityName, inSection, newContent, reason?}) -> string, 功能: 在实体指定章节末尾追加内容。
- deleteEntityContent - ({libraryName, entityName, inSection, contentToDelete, reason?}) -> string, 功能: 从实体指定章节中精确删除一段内容。
- replaceEntitySection - ({libraryName, entityName, oldHeading, newHeading, newBodyContent, reason?}) -> string, 功能: 重写知识实体的指定章节。
- mergeEntities - ({libraryName, sourceNames, targetName, reason?}) -> string, 功能: 将多个源实体的内容和元数据合并到一个目标实体中。
- createRelations - ({libraryName, relations, reason?}) -> string, 功能: 在实体 Front Matter 中批量添加关系。
- deleteRelations - ({libraryName, relations, reason?}) -> string, 功能: 从实体 Front Matter 中批量删除关系。
- readManual - ({libraryName, reason?}) -> string, 功能: 读取知识库的 meta.md 手册。
- editManual - ({libraryName, oldLines, newLines, reason?}) -> string, 功能: 编辑或增删 meta.md 的内容。
- listEntityTypes - ({libraryName, reason?}) -> string, 功能: 列出知识库中所有唯一的实体类型及其数量。
- findEntitiesByMetadata - ({libraryName, metadataQuery, reason?}) -> string, 功能: 根据元数据键值对搜索实体。
- searchInContents - ({libraryName, contentGlob, reason?}) -> string, 功能: 在实体正文中进行 glob 模式匹配。
- (未实现) garbageCollectRelations - ({libraryName, dryRun?, reason?}) -> string, 功能: 查找并清理知识库中指向不存在知识实体的“断裂链接”。
- (未实现) findRelations - ({libraryName, toEntity?, relationType?}) -> string, 功能: 在知识库中查找关系。
- (未实现) searchAnywhere - ({libraryName, pattern}) -> string, 功能: 在文件名、元数据和正文中进行全局搜索。

### Level 4: 应用入口与服务运行时 (Application Entrypoint)
这是最顶层，负责整合所有工具，启动和管理整个 MCP 服务。
- src/v2/runtime.ts:
    - getLibraryDirPath - (libraryName) -> string, 功能: 获取指定知识库的根目录路径。
    - getEntityDirPath - (libraryName) -> string, 功能: 获取指定知识库的 entities 目录路径。
- src/v2/index.ts:
    - v2tools - (常量) -> McpHandlerDefinition[], 功能: 从所有 tools 文件中收集工具定义，并聚合成一个数组导出。
- src/index.ts:
    - createMcpServer - ({handlers, name, version, ...}) -> void, 功能: (来自 @modelcontextprotocol/sdk) 创建并启动 MCP 服务实例。

---

## 5. 关键数据结构 (来自 typings.ts 及相关文件)

以下是项目中定义的一些核心数据结构，它们用于在不同层级之间传递和处理信息。

- **`FileType` (enum)**:
  - **功能**: 定义了知识库中不同类型的文件。
  - **值**: `FileTypeEntity` (实体文件), `FileTypeJourney` (日志文件), `FileTypeMeta` (元数据文件)。

- **命名与路径相关类型**:
  - **`ThingName`**: 事物的名称，如实体名，不含文件后缀。
  - **`LibraryName`**: 知识库的名称。
  - **`FileRelativePath`**: 文件相对于知识库根目录的路径。
  - **`FileAbsolutePath`**: 文件的绝对路径。
  - **`FolderAbsolutePath`**: 文件夹的绝对路径。

- **内容表示相关类型**:
  - **`ContentGlobLine`**: 用于模糊匹配内容的 glob 模式字符串。
  - **`ContentExactLine`**: 用于精确匹配内容的单行字符串。
  - **`LineNumber`**: 文件中的行号，从 1 开始计数。
  - **`FileWholeLines`**: 代表整个文件内容的字符串数组，每个元素是一行。
  - **`ContentLocator`**: 用于定位文件中特定内容块的结构，可以是基于行号范围或精确内容匹配。

- **目录 (TOC) 相关类型**:
  - **`TocGlob`**: 用于模糊匹配章节标题的 glob 模式字符串。
  - **`TocExactLine`**: 用于精确匹配章节标题行的字符串。
  - **`TocLevel`**: TOC 项的标题级别 (如 H1-H6)。
  - **`TocItem`**: 描述单个目录项的结构，包含 `level` (标题级别), `lineNumber` (行号), 和 `tocLineContent` (标题行原始内容)。
  - **`TocList`**: `TocItem` 的数组，代表一个文件的完整目录结构。

- **Front Matter 相关类型**:
  - **`FrontMatterLine`**: 代表 Front Matter 中的单行字符串，格式为 `key: value`。
  - **`FrontMatterItem`**: 结构化的 Front Matter 项，包含 `name` (键) 和 `value` (值)。
  - **`FrontMatterPresetKeys` (enum)**: 定义了系统中预设的 Front Matter 键名，如 `entity type`, `date modified`, `relation as` 等，以保证一致性。

- **文档结构化表示类型 (来自 src/v2/editor/editing.ts)**:
  - **`Section`**:
    - **功能**: 表示文档的一个逻辑章节，包含章节的目录项 (`tocItem`) 和该章节对应的所有内容行 (`content`)。它是 `splitFileIntoSections` 函数的输出类型，在内部编辑逻辑中广泛使用。

- **工具定义类型**:
  - **`McpHandlerDefinition<Args, Name>`**:
    - **功能**: 这是定义一个高阶工具（Level 3）的核心类型。
    - **结构**: 它包含两部分：
      1.  `toolType`: 描述工具的元信息，包括 `name` (工具名), `description` (功能描述), 和 `inputSchema` (使用 `zod` 定义的输入参数模式)。
      2.  `handler`: 一个函数，负责接收解析后的输入参数并执行工具的实际逻辑。
