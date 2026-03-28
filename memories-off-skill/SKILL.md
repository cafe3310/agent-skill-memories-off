---
name: memories-off
description: 管理基于 Markdown 实体的本地知识库。提供库观察、实体检索、按需加载章节、精确编辑及显式关系管理能力。支持长期记忆与持续学习。
author: github/cafe3310
license: Apache-2.0
---

# Agent Skill: memories-off (技能说明)

## 1. 概述 (Overview)

`memories-off` 是一个专门用于管理本地结构化知识库的 Agent Skill。它允许 LLM 将非结构化的对话、笔记、项目文档等，转化为由实体、关系和观察组成的知识图谱，并提供高效的检索和编辑能力。

该 Skill 旨在支持 LLM 实现“长期记忆”和“持续学习”，并基于 Markdown 文件提供本地优先的数据存储方案。

## 2. 核心能力 (Core Capabilities)

- **库观察 (Observation)**: 了解知识库的全局状态、统计信息和元数据手册（`meta.md`）。
- **实体检索 (Retrieval)**: 通过名称、元数据（Frontmatter）或正文内容（Full-text）查找特定实体。
- **实体阅读 (Reading)**: 读取实体的全文、目录（TOC）或特定章节。
- **内容编辑 (Editing)**: 在保持文档结构完整的情况下，精确追加或替换实体中的章节。
- **实体管理 (Management)**: 创建、重命名、合并和安全删除（移动至回收站）实体文件。
- **关系管理 (Relations)**: 在实体之间建立和删除显式的语义关系。
- **审计追溯 (Audit)**: 所有修改操作均会记录在全局审计日志（`journey.md`）中。

## 3. 使用场景 (Usage Scenarios)

- **知识积累**: 在对话过程中提取关键信息并记录到相应的实体中。
- **项目管理**: 追踪项目中的角色、目标、里程碑及其关联。
- **个性化建议**: 基于长期积累的知识库为用户提供定制化的反馈。
- **复杂查询**: 跨多个实体查找特定主题的信息，并进行综合分析。

## 4. 关键规范 (Key Specifications)

本 Skill 的详细逻辑由以下子目录中的文档定义，建议按顺序阅读：

### 3.1 基础结构 (Architecture)
- [**仓库布局规范**](./知识库结构定义/仓库布局规范.md): 定义文件夹结构和核心文件职责。
- [**手册结构规范**](./知识库结构定义/手册结构规范.md): 定义 `meta.md` 的内部组织方式。
- [**审计日志规范**](./审计与日志定义/审计日志规范.md): 定义 `journey.md` 的顺序追加逻辑。

### 3.2 文档逻辑 (Document Logic)
- [**实体结构规范**](./文档结构定义/实体结构规范.md): 定义 Markdown 文件的物理布局。
- [**元数据规范**](./文档结构定义/元数据规范.md): 定义 Frontmatter 的字段、解析与合并规则。
- [**章节逻辑规范**](./文档结构定义/章节逻辑规范.md): 定义 Heading、Section 与定位协议。

### 3.3 关联逻辑 (Relation Logic)
- [**显式关系规范**](./关联定义/显式关系规范.md): 定义基于元数据的强语义关联。
- [**隐式链接规范**](./关联定义/隐式链接规范.md): 定义基于 WikiLinks 的引用逻辑。

### 3.4 工具规格 (Action Tools)
- [**观察工具规格**](./操作定义/观察工具规格.md): stats, load manual 等。
- [**检索工具规格**](./操作定义/检索工具规格.md): search, find, load entities 等。
- [**编辑工具规格**](./操作定义/编辑工具规格.md): add/replace section 等。
- [**管理工具规格**](./操作定义/管理工具规格.md): create, rename, merge, trash, relation 等。

## 5. 约束与原则 (Constraints & Principles)

- **本地优先 (Local-First)**: 所有操作均基于本地文件系统。
- **XML 报告 (XML Reporting)**: 所有工具均返回结构化的 XML 报告，便于 Agent 解析。
- **强制审计 (Audit)**: 所有修改操作必须提供 `reason` 并记录到 `journey.md`。
- **通用语言 (Glossary)**: 严格遵守 [项目术语表](../docs/2026-01-03-15-39-glossary.md) 的定义。
