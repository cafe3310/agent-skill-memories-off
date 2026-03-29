---
entity type: 概念, 技术方案
date created: 2026-03-28
date modified: 2026-03-28
aliases: memories-off, 长期记忆工具
status: 草稿
relation as 负责人: Person-四盘
relation as 关联: doc-todo-log-loop
---

# 概念定义 (Definition)
`Memory Skill` 是一种基于本地 Markdown 实体的 Agent 技能。它旨在通过一套标准化的工具集，赋予大语言模型 (LLM) 获取和维护结构化“长期记忆”的能力。

# 核心原则 (Principles)
- **便携轻量**: 本地优先，无数据库依赖。
- **结构化知识**: 通过 Front Matter 和 Heading 树实现机器解析。
- **通用语言**: 统一使用 `Heading`, `Section`, `Content`, `TOC` 等术语。

# 相关实体 (Relations)
- **创始人**: [[Person-四盘]]
- **存储方案**: 基于文件系统。
