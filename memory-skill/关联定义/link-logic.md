# 关联定义: Link Logic

本文档定义了 `memory-skill` 中基于 WikiLinks 的隐式链接逻辑及维护机制。

---

## 1. WikiLinks 定义 (Implicit Links)

WikiLinks 是指在实体正文中通过 `[[目标实体名称]]` 语法引用的隐式关联。

### 1.1 语法规则
- **格式**: `[[ThingName]]`。
- **解析**: 系统将 `[[ThingName]]` 解析为指向该知识库中 `entities/ThingName.md` 文件的链接。
- **显示**: 在渲染或阅读时，通常仅显示 `ThingName` 文本，而不显示 `[[ ]]`。

## 2. 链接发现 (Link Discovery)

- **扫描机制**: 当 Agent 需要分析实体的关联网络时，应对正文内容进行正则匹配以发现所有 WikiLinks。
- **双向分析**:
  - **Out-links**: 当前实体通过 WikiLinks 引用的实体。
  - **In-links (Backlinks)**: 哪些其他实体引用了当前实体。

## 3. 重命名同步 (Rename Synchronization)

这是 `memory-skill` 的核心维护逻辑之一，旨在防止出现断链（Broken Links）。

### 3.1 自动扫描与更新
- **触发**: 当执行 `renameEntity` 操作时。
- **范围**: 整个知识库的所有实体文件（包括 `meta.md`）。
- **逻辑**:
  - 搜索所有正文中的 `[[OldName]]`。
  - 自动将其替换为 `[[NewName]]`。
  - 记录并向用户报告受影响的文件数量。

## 4. 链接有效性 (Link Validity)

- **校验**: 在解析时，应检查 WikiLinks 指向的实体文件是否真实存在于 `entities/` 目录中。
- **断链处理**: 发现断链时，Agent 应在报告中指出，并建议用户修正。

## 5. 与显式关系的区别 (Comparison with Explicit Relations)

| 特性 | WikiLinks (隐式) | `relation as` (显式) |
| :--- | :--- | :--- |
| **存储位置** | Body (正文) | Front Matter (元数据) |
| **语义强度** | 弱 (仅表示存在提及) | 强 (定义了具体的语义联系) |
| **适用场景** | 叙述性文本、补充说明 | 结构化图谱、业务逻辑关联 |
| **可搜索性** | 基于文本全局搜索 | 基于元数据精确检索 |
