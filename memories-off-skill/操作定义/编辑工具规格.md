# 操作定义: Editing Tools

本文档定义了用于修改实体内部内容的原子化工具规格。

---

## 1. 实体内容编辑 (Content Editing)

### 1.1 `addContentToSection`
- **职能**: 将新的 Markdown 文本追加到指定章节的末尾。
- **输入参数**:
  - `libraryName`: 目标知识库名称。
  - `entityName`: 目标实体名称。
  - `inSection`: 目标章节标题（不含 `#`）。
  - `newContent`: 要追加的内容。
  - `reason`: 修改原因（强制提供）。
- **执行逻辑**:
  - 1. 定位目标实体文件。
  - 2. 在解析的 TOC 中通过 `inSection` 找到对应的 `Section`。
  - 3. 将 `newContent` 追加到该章节内容的最后一行之后，即下一个同级或高级标题之前。
  - 4. 自动更新 `date modified` 元数据。

### 1.2 `replaceSection`
- **职能**: 完全替换现有章节（包括标题和正文）。
- **输入参数**:
  - `libraryName`, `entityName`。
  - `oldHeading`: 现有章节标题。
  - `newHeading`: 新章节标题（如果仅修改内容，可与 `oldHeading` 相同）。
  - `newBodyContent`: 新的章节正文。
  - `reason`: 修改原因（强制提供）。
- **执行逻辑**:
  - 1. 定位 `oldHeading` 对应的 `Section` 物理位置（起始行到结束行）。
  - 2. 用新的标题和内容替换该区域。
  - 3. 若 `newBodyContent` 为空，则视为删除该章节。

## 2. 系统元数据编辑 (System Manual Editing)

### 2.1 `addManualSection`
- **职能**: 在 `meta.md` 末尾追加新章节。
- **参数**: `libraryName`, `sectionTitle`, `newContent`, `reason`。

### 2.2 `replaceManualSection`
- **职能**: 替换 `meta.md` 中的特定章节。
- **参数**: `libraryName`, `sectionTitle`, `newContent`, `reason`。

---

## 3. 操作准则 (Guidelines)

- **非破坏性编辑**: 始终通过 `replaceSection` 而非全量重写来修改大文件，以防丢失未预期的内容。
- **强制审计**: 必须为每一次编辑提供清晰的 `reason`。
- **精确标题匹配**: `inSection` 和 `oldHeading` 必须与文件中存在的标题完全一致（不含 `#`），否则操作失败。
- **原子性**: 每次工具调用应仅完成一个逻辑上的修改动作。
- **XML 反馈**: 报告必须明确指示修改前后的状态差异。
