# 文档结构定义: Section Logic

本文档详细定义了 `memory-skill` 中实体正文的章节组织逻辑及定位规则。

---

## 1. 核心层级 (Core Hierarchy)

在 `memory-skill` 中，实体正文被视为一组有序的 **Section (章节)**。

### 1.1 Heading (标题)
- **定义**: 仅指 Markdown 的标题行（如 `# Title`）。
- **属性**:
  - `level`: 1-6 级标题。
  - `text`: 标题的文本内容（不含 `#`）。
  - `lineNumber`: 标题在文件中的物理行号（从 1 开始）。

### 1.2 Section (章节)
- **定义**: 由一个 `Heading` 及其下属的所有内容（直到下一个同级或高级标题出现）组成的逻辑块。
- **组成**: `Section = Heading + Content`。
- **注意**: 文档顶部的无标题文本（Intro）也被视为一个特殊的 `Section`（其 `heading` 为 `null`）。

### 1.3 TOC (目录)
- **定义**: 整个文件中所有 `Heading` 的扁平化有序列表。
- **职能**: 用于快速概览文档结构并实现跨章节跳转。

## 2. 定位协议 (Location Protocol)

为了实现精确的非破坏性编辑，系统采用多重定位机制。

### 2.1 ContentLocator
- **Lines 定位**: 基于文本行的精确内容匹配。
- **NumbersAndLines 定位**: 结合物理行号与内容特征的混合定位（最稳健）。

### 2.2 HeadingGlob (模糊匹配)
- **定义**: 不支持 `*` 通配符，仅支持子字符串匹配。
- **原则**: 用于检索，但在执行编辑操作前，必须转换为精确的 `HeadingExact` 或行号。

## 3. 编辑行为准则 (Editing Rules)

- **Add (追加)**: 将新内容插入到 `Section` 的 `Content` 末尾，即下一个 `Heading` 之前。
- **Replace (替换)**: 移除旧的 `Section`（含标题和内容），并在原位插入新的 `Section`。
- **Insert (插入)**: 在指定行号或指定内容块之后插入新内容。

## 4. 解析约束 (Parsing Constraints)

- **唯一性**: 建议在一个文档内保持同级标题的唯一性，以避免定位歧义。
- **层级一致性**: 维护良好的 Markdown 标题层级，避免跳级（例如从 `#` 直接跳到 `###`）。
- **非破坏性**: 编辑操作应仅修改目标行，不得擅自格式化或重排文档的其他部分。
