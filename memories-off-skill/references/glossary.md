# 项目术语表 (Glossary)

本文档定义了 `memories-off-skill` 的“通用语言”(Ubiquitous Language)。

## 1. 核心名词 (Nouns)

- **Library (知识库)**: 工作基本单元，一个独立的 Git 仓库，包含 `meta.md` 和 `entities/` 目录。
- **Entity (实体)**: 知识库中的具体事物，对应一个带有 YAML Frontmatter 的 Markdown 文件。
- **Meta (手册)**: 指 `meta.md` 文件，定义库的全局 Schema、规则和谓词。
- **Frontmatter**: 位于文件顶部的元数据块，由一对 `---` 分隔。
- **Heading (标题)**: Markdown 的标题行（如 `# Title`），是章节的唯一标识。
- **Section (章节)**: 一个逻辑单元，由一个 `Heading` 及其下属的所有正文内容组成。
- **TOC (目录)**: 整个文件中所有 `Heading` 的有序列表或树状结构。
- **ThingName**: 事物的逻辑名称，通常指不带后缀的文件名（如 `人物-四盘`）。

## 2. 核心动词 (Verbs)

- **get**: 通过唯一标识符获取单个资源。
- **find**: 基于结构化、确定性条件（如元数据）查找资源。
- **search**: 基于模糊、非结构化模式（如全文、Glob）搜索资源。
- **add**: 向现有章节末尾追加内容。
- **replace**: 原地替换现有章节或元数据项。
- **normalize**: 将字符串（如文件名、标题）按规范执行标准化清洗。
- **commit**: 将已完成的操作作为原子快照提交至 Git。
- **audit**: 检查知识库的一致性，发现孤儿引用或失效链接。
