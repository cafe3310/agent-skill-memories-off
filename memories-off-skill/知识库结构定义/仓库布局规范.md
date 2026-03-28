# 知识库结构定义: Library Layout

本文档定义了 `memory-skill` 所管理的知识库（Library）在本地文件系统中的标准目录结构和文件职责。

---

## 1. 顶层结构 (Top-level Structure)

一个知识库（Library）是一个独立的文件夹，其内部包含以下标准子目录和核心文件：

```text
[Library Root]/
├── meta.md         # 知识库手册 (Manual)
├── entities/       # 实体目录 (Entities)
├── trash/          # 回收站 (Trash)
├── backups/        # 备份目录 (Backups)
└── journeys/       # (可选) 编辑日志 (Journeys)
```

## 2. 核心组件说明 (Core Components)

### 2.1 知识库手册 (`meta.md`)
- **职能**: 存储知识库的全局元数据、规则、指导原则和 Schema 定义。
- **重要性**: 是 Agent 理解当前知识库上下文的首要入口。
- **操作原则**: 
  - 通过 `loadManual` 获取内容。
  - 通过 `addManualSection` 或 `replaceManualSection` 进行更新。

### 2.2 实体目录 (`entities/`)
- **职能**: 存放所有具体的知识实体。
- **格式**: 每个实体对应一个以 `.md` 结尾的 Markdown 文件。
- **命名规范 (ThingName Standard)**: 
  - **允许字符**: 仅允许 CJK 字符、英文字母、数字和中横线 (`-`)。
  - **标准化逻辑**:
    1. 非法字符（如空格、点、逗号等）统一替换为单个 `-`。
    2. 连续的 `-` 合并为单个 `-`。
    3. 移除首尾的 `-`。
  - **示例**: `Hello, World! (世界)` -> `Hello-World-世界`。
  - 文件名应具有唯一性，代表一个 `ThingName`。

### 2.3 回收站 (`trash/`)
- **职能**: 存放被软删除的实体文件。
- **重命名逻辑**: 移入时附加时间戳前缀，格式为 `YYYY-MM-DD-HH-MM-SS_[OriginalName].md`。
- **目的**: 确保数据安全，防止因误操作导致永久丢失。

### 2.4 备份目录 (`backups/`)
- **职能**: 存放知识库的完整快照。
- **格式**: 压缩包格式（如 `.zip`），命名包含时间戳和知识库名称。

### 2.5 编辑日志 (`journeys/`)
- **职能**: 记录文件的变更轨迹和编辑历史。
- **状态**: 当前为可选模块，由系统按需自动管理。

## 3. 标识符定义 (Identifiers)

- **LibraryName**: 知识库的唯一显示名称，映射到文件夹名。
- **ThingName**: 实体或记录的逻辑名称（不含后缀）。
- **FileRelativePath**: 相对于 `[Library Root]` 的路径（如 `entities/User-Profile.md`）。
- **ThingLocator**: 在系统中唯一定位一个事物的组合键，包含 `LibraryName`、`FileType`（Entity/Meta/Journey）和 `ThingName`。
