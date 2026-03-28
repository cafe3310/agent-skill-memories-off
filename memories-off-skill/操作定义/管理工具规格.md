# 操作定义: Management Tools

本文档定义了用于管理知识实体、关系及系统级任务的工具规格。

---

## 1. 实体文件管理 (Entity Management)

### 1.1 `createEntities`
- **职能**: 创建一个或多个全新的实体文件。若已存在同名实体，操作将失败。
- **输入**: `libraryName`, `entities` (名称和内容对象列表), `reason`。
- **执行**:
  - 1. 标准化实体名称。
  - 2. 在 `entities/` 目录创建 `.md` 文件。
  - 3. 自动注入基础 Front Matter (`date created`)。

### 1.2 `renameEntity`
- **职能**: 重命名实体文件，并自动同步更新所有关联（WikiLinks）。
- **输入**: `libraryName`, `oldName`, `newName`, `reason`。
- **执行**:
  - 1. 文件系统重命名。
  - 2. 扫描所有文件中的 `[[oldName]]` 并更新为 `[[newName]]`（详见 [关联定义](../关联定义/link-logic.md)）。

### 1.3 `mergeEntities`
- **职能**: 将多个源实体内容合并到目标实体，并删除源文件。
- **输入**: `libraryName`, `sourceNames`, `targetName`, `reason`。
- **执行**:
  - 1. 将源实体的内容按章节追加到目标实体末尾。
  - 2. 自动更新源实体的引用指向目标实体。

### 1.4 `trashEntities`
- **职能**: 将实体移动到 `trash/` 目录。
- **输入**: `libraryName`, `entityNames`, `reason`。
- **执行**: 重命名为 `YYYY-MM-DD-HH-MM-SS_[OriginalName].md` 并移位。

## 2. 关系管理 (Relation Management)

### 2.1 `createRelations` / `deleteRelations`
- **职能**: 在实体 Front Matter 中批量建立或删除语义关系。
- **输入**: `libraryName`, `relations` (source, type, target 三元组列表), `reason`。
- **执行**: 修改目标实体的 `relation as [type]` 元数据项。

### 2.2 `getRelatedEntities`
- **职能**: 查询与特定实体相连的其他实体及其关系类型。
- **参数**: `libraryName`, `entityName`, `direction` (incoming/outgoing/both), `relationType` (可选过滤)。

## 3. 系统维护 (System Maintenance)

### 3.1 `backupLibrary`
- **职能**: 创建当前知识库的完整快照压缩包。
- **输入**: `libraryName`。
- **输出**: 备份文件的绝对路径。

### 3.2 `garbageCollectRelations`
- **职能**: 清理指向已不存在（且不在回收站中）实体的无效关系条目。

---

## 4. 操作准则 (Guidelines)

- **数据安全性**: 凡涉及删除的操作，必须优先通过 `trashEntities` 实现软删除。
- **一致性**: `renameEntity` 是一个重型操作，应确保在完成所有文件更新后才返回成功报告。
- **关联敏感**: 在进行合并或删除前，应先通过 `getRelatedEntities` 评估对图谱的影响。
