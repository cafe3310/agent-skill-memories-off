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

---

## 2. Agent 工作流与命令探索 (Agent Workflow)

作为 Agent，你**不需要**去阅读冗长的底层工具实现细节或规格文档。本 Skill 提供了自包含的命令行包装器 `memocli`。

### 2.1 任务初始化 (Explore First)
在处理任何与本知识库相关的任务前，**必须首先运行以下命令**获取全局上下文：
```bash
memocli explore
```
该命令会返回结构化的 XML 报告，包括：
- 知识库的全局描述和手册 (`meta.md`)。
- 架构实体预览。
- 当前所有可用的 `memocli` 子命令列表及简要说明。

### 2.2 了解命令用法 (Help System)
当你需要使用某个具体的子命令（如 `search-entities`, `append-update`）但不确定其参数时，**请直接在终端运行该命令的帮助**：
```bash
memocli <subcommand> --help
```
终端输出会告诉你最新的参数、选项以及调用示例，请**严格按照 `--help` 提示的格式调用**。

---

## 3. Agent 最佳实践与约束 (Best Practices)

在使用 `memocli` 时，请严格遵守以下实践，以确保图谱的健康和数据的安全：

1. **缓冲编辑优先**: 在编辑已有实体内容时，严禁使用 Agent 自带的行定位编辑工具、也尤其禁止使用整体文件 Write。**必须优先通过 `memocli append-update` 以追加更新块的形式进行非破坏性修改**。
2. **多行写入使用 STDIN 模式**: 当你需要通过 `create-entity` 或 `append-update` 写入包含多行、引号、特殊符号、WikiLinks 等复杂内容时，不建议使用 `-c "..."` 传参，这极易导致 Shell 转义失败。建议使用管道（STDIN）模式。例如：
   ```bash
   echo "## 章节标题
   - 内容1
   - 内容2 [[链接]]" | memocli append-update --entity "实体名" --content-stdin --reason "更新理由"
   ```
3. **模糊检索优先 (Content-Grep First)**: 了解细节信息时，应使用 `memocli search-entities`。建议配合 `--type` (过滤类型) 和 `--rel` (过滤关系) 提升检索精度。
4. **标题层级规范**: 实体正文必须遵循严格的标题层级：文件顶部第一行固定为 H1 (`# 实体名`)，正文内部所有的业务章节标题必须统一标准化为 H2 (`## 章节名`)。禁止使用 H3 及更深层级。
5. **优先用 Plain Text**: 实体正文应当简洁。避免使用 Markdown 加粗 (`**`)、斜体 (`*`) 等修饰性格式。允许使用 H2 标题、无序列表 (`-`) 和 WikiLinks (`[[ ]]`)。
6. **强制审计 (Audit)**: 所有修改操作必须提供简短的 `--reason` 参数以供 Git 记录。
7. **本地优先**: 所有操作均基于本地文件系统，且当前路径若为知识库根目录，`memocli` 会自动推断 `--path .`。

---

## 4. 术语定义 (Glossary)

为了与用户和其他系统保持语义对齐，请严格遵守本项目定义的通用语言。
详细定义请参阅：[**项目术语表 (Glossary)**](./references/glossary.md)。

---

## 5. 底层设计文档 (Design Documents)

`design-doc/` 是此 Agent 的底层设计文档。你一般不需要阅读。仅当用户要求你修改本 Skill 的底层实现细节时，才需要参考其中的内容。
