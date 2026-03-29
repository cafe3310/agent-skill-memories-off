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
- **审计追溯 (Audit)**: 所有修改操作均以 Git Commit 的形式记录，确保变更的可追溯性和安全性。
- **非破坏编辑 (Non-destructive Editing)**: 通过“缓冲-更新”机制，确保编辑操作以追加「编辑 block」的形式出现在已有文档尾部，待定期用户确认后再合并到目标章节，最大程度避免内容丢失风险。

## 3. 使用场景 (Usage Scenarios)

- **知识积累**: 在对话过程中提取关键信息并记录到相应的实体中。
- **项目管理**: 追踪项目中的角色、目标、里程碑及其关联。
- **个性化建议**: 基于长期积累的知识库为用户提供定制化的反馈。
- **复杂查询**: 跨多个实体查找特定主题的信息，并进行综合分析。

## 3. 安装与命令行工具 (Installation & CLI)

本 Skill 提供了一个强大的命令行包装器 `memocli`，它是操作 `memories-off` 知识库的统一入口。

### 3.1 安装方式
运行 `python3 scripts/install.py`。该安装器会自动执行以下任务：
- **路径探测**：自动确定 Skill 的绝对路径并注入包装器。
- **权限管理**：尝试安装到 `/usr/local/bin` 或 `~/.local/bin`，并自动设置可执行权限。
- **元数据发现**：在安装阶段通过协议自动发现所有子命令的描述，生成静态帮助列表以确保运行时的高响应速度。

### 3.2 智能特性 (Smart Features)
- **智能路径注入**：在知识库根目录（包含 `meta.md`）下执行时，若省略 `--path` 或 `-p` 参数，`memocli` 会自动追加 `--path .`，极大简化了 Agent 的调用逻辑。
- **自适应帮助系统**：
    - `memocli --help`：全局帮助顶部会显示本 Skill 的名称及 `SKILL.md` 的完整物理路径，方便追溯规范定义。
    - `memocli <subcommand> --help`：自动在底层帮助前插入包装器提示，并动态调整示例代码。
- **提示一致性**：通过 `prog` 参数适配，所有报错和用法提示均显示为 `memocli <subcommand>`，不再暴露底层的 `.py` 文件名。

### 3.3 协议规范 (memocli Protocol)
为了保持工具链的可扩展性，所有位于 `scripts/` 下的业务脚本均遵循以下协议：
- `--memo-cli-info`：返回 `Description`（一句话说明）和 `Example`（调用示例）。
- `--memo-cli-call`：标识位。当存在时，脚本应调整其 `argparse` 的 `prog` 名称和用法示例以匹配 `memocli` 格式。

## 4. 关键规范 (Key Specifications)

本 Skill 的详细逻辑由以下子目录中的文档定义，建议按顺序阅读：

### 3.1 基础结构 (Architecture)
- [**仓库布局规范**](./知识库结构定义/仓库布局规范.md): 定义文件夹结构和核心文件职责。
- [**手册结构规范**](./知识库结构定义/手册结构规范.md): 定义 `meta.md` 的内部组织方式。
- [**审计日志规范**](./审计与日志定义/审计日志规范.md): 定义 Git 驱动的提交规范。

### 3.2 文档逻辑 (Document Logic)
- [**实体结构规范**](./文档结构定义/实体结构规范.md): 定义 Markdown 文件的物理布局。
- [**元数据规范**](./文档结构定义/元数据规范.md): 定义 Frontmatter 的字段、解析与合并规则。
- [**章节逻辑规范**](./文档结构定义/章节逻辑规范.md): 定义 Heading、Section 与定位协议。

### 3.3 关联逻辑 (Relation Logic)
- [**显式关系规范**](./关联定义/显式关系规范.md): 定义基于元数据的强语义关联。
- [**隐式链接规范**](./关联定义/隐式链接规范.md): 定义基于 WikiLinks 的引用逻辑。

### 3.4 工具规格 (Action Tools)

要对本 Skill 控制的知识库进行任何操作，你都应该优先了解以下可用的工具规格文档，并根据他们的建议执行任务。
即使有一些任务看起来用你自带的工具更简单，也不要偷懒，必须优先使用正确的下列工具 - 尤其是「编辑工具」。

- [观察工具规格](./操作定义/观察工具规格.md): stats, load manual 等。
- [检索工具规格](./操作定义/检索工具规格.md): search, find, load entities 等。
- [编辑工具规格](./操作定义/编辑工具规格.md): add/replace section, add content, edit content 等。
- [管理工具规格](./操作定义/管理工具规格.md): create, rename, merge, trash, relation 等。

### 3.5 示例资源 (Example Resources)
- [模板知识库 (Template Library)](./assets/template-library/): 提供符合全套规范的目录结构、`meta.md` 手册及各种实体类型的 Markdown 示例。Agent 应参考此结构进行库初始化或内容格式化。


## 5. 约束与原则 (Constraints & Principles)

- 严禁在不了解 `memocli` 可用子命令的情况下直接读取库内文档或执行复杂任务，新环境或新任务中，应首先运行 `memocli --help`。
- **模糊检索优先 (Content-Grep First)**: 了解已有信息时，可以对 `entities/` 目录进行全文检索，如 `grep -ie <keywords_regex> -C2` ，寻找隐藏在实体正文中的碎片化信息。
- **缓冲编辑优先**: 在编辑已有实体内容时，严禁使用 Agent 自带的行定位编辑工具、也尤其禁止使用整体文件 Write。必须优先通过 `appendUpdateBlock` 以追加更新块的形式进行非破坏性修改。
- **优先用 Plain Text**: 实体正文应当避免使用格式。严禁使用 Markdown 加粗 (`**`)、斜体 (`*`) 等修饰性格式，也严禁使用 backticks 等代码块格式。仅允许使用 Heading (#，而且仅允许一级 Heading)、无序列表 (-) 和 WikiLinks ([[ ]]) 来组织内容。
- **本地优先 (Local-First)**: 所有操作均基于本地文件系统。
- **XML 报告 (XML Reporting)**: 所有工具均返回结构化的 XML 报告，便于 Agent 解析。
- **强制审计 (Audit)**: 所有修改操作必须提供 `reason` 以 Git 记录。
- **通用语言 (Glossary)**: 严格遵守 [项目术语表](./references/glossary.md) 的定义。
