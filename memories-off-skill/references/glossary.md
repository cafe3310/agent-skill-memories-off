# 项目术语表 (Glossary)

本文档定义了 `memories-off` 的“通用语言”(Ubiquitous Language)。

## 1. 核心名词 (Nouns)

- **Library (知识库)**: 工作基本单元，一个独立的 Git 仓库，包含 `meta.md` 和 `entities/` 目录。
- **Entity (实体)**: 知识库中的具体事物，对应一个带有 YAML Frontmatter 的 Markdown 文件。
- **Meta (手册)**: 指 `meta.md` 文件，定义库的全局 Schema、规则和谓词。
- **Frontmatter**: 位于文件顶部的元数据块，由一对 `---` 分隔。
- **Heading (标题)**: Markdown 的标题行。遵循统一规范：H1 为实体名，H2 为业务章节。
- **Section (章节)**: 一个逻辑单元，由一个 H2 标题及其下属的所有内容组成。
- **TOC (目录)**: 文档中所有 Heading 的有序列表。
- **Entity Name (Slug)**: 实体的唯一标识名，对应不带后缀的文件名。

## 2. 核心动词 (Verbs)

- **Explore (探索)**: 一站式获取知识库手册、核心骨架及全局统计信息。
- **Doctor (治理)**: 扫描并自动修复知识库中的合规性问题（命名、标题、断链等）。
- **Search (检索)**: 基于模式（正则表达式）在全库范围内查找实体。支持属性过滤。
- **Append (追加)**: 向实体末尾以 `UPDATE_BLOCK` 缓冲块的形式添加新发现。
- **Normalize (标准化)**: 将实体名、标题、关系谓词按物理磁盘与逻辑规范执行清洗。
- **Commit (提交)**: 将操作快照存入 Git，形成审计追踪。
