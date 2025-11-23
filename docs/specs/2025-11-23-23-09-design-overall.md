# 整体设计文档：mcp-server-memories-off

**关联文档**:
- [**术语表 (Glossary)**](./2025-11-23-23-09-terms.md)

---

## 1. 项目目标

提供一个轻量级、本地优先的知识管理 MCP (Model Context Protocol) 服务，使 LLM 能够进行长期知识的持续学习、整合和使用。

项目的核心思想是将非结构化文本（如对话、笔记）转化为结构化的知识图谱，包含实体（Entities）、关系（Relations）和观察（Observations），并提供灵活的检索能力。

## 2. 核心原则

- **便携轻量 (Portable & Lightweight)**: 基于本地文件系统，无外部数据库或服务依赖，易于部署和迁移。
- **本地优先 (Local-first)**: 所有数据默认存储在本地，确保用户数据的隐私和所有权，不依赖网络连接。
- **结构化知识 (Structured Knowledge)**: 将零散信息高效组织成知识图谱，便于机器理解和长久利用。
- **灵活检索 (Flexible Retrieval)**: 支持多种方式查询知识图谱，满足不同场景下的信息提取需求。
- **数据可读性 (Human-Readable)**: 知识图谱的核心数据以人类可读的 YAML 格式存储，便于直接查看、编辑和版本控制。

## 3. 技术栈与架构

### 3.1. 技术栈

- **运行时**: Node.js
- **构建/测试/包管理**: Bun
- **语言**: TypeScript
- **核心框架**: `@modelcontextprotocol/sdk`
- **数据校验**: `zod`, `zod-to-json-schema`

### 3.2. 架构概览

该服务是一个通过标准输入/输出（Stdio）与上游（如 LLM 客户端）通信的命令行工具。它遵循 MCP 协议，通过暴露一系列工具（Tools）来操作本地知识库。

### 3.3. 知识库目录结构

所有知识都存储在一个名为 `library` 的根目录中，其结构如下：

```
library/
├── entities/    # 存放所有实体及其观察记录（YAML 文件）
├── meta.md      # 存放知识库的元数据
├── backups/     # 存放知识库的备份压缩包
├── trash/       # 作为删除文件的回收站
└── journeys/    # 记录所有编辑操作的日志（暂未完全实现）
```

## 4. 知识图谱设计

知识图谱由以下核心组件构成：

- **实体 (Entities)**: 知识图谱的“节点”，代表任何可被识别和描述的事物，如人物、地点、概念、项目等。每个实体都是一个独立的 YAML 文件，存储在 `entities/` 目录下。
- **观察 (Observations)**: 关于实体的、带有时间戳的离散信息片段。每次与 LLM 的交互或信息输入都可以形成一条或多条观察。观察记录直接追加在对应实体的 YAML 文件中。
- **关系 (Relations)**: 实体之间的“边”，用于描述它们之间的联系。例如，“张三” `employed_by` “ABC 公司”。关系信息也存储在实体文件中。
- **手册 (Manuals)**: 由人工整理和维护的结构化文档，用于存储那些不适合碎片化存储的、体系化的知识。

## 5. 使用与配置

### 5.1. 快速启动

用户可以通过 `npx` 直接运行服务，无需本地安装：

```bash
npx -y mcp-server-memories-off
```

### 5.2. 环境变量配置

可以通过以下环境变量来配置服务的行为：

- **`MEM_LIBRARIES`**: 指定一个或多个知识库的路径。多个路径用逗号分隔。
  - 示例: `export MEM_LIBRARIES="/path/to/my/library1,/path/to/another/library"`
- **`MEM_LOG_FILE`**: 指定日志文件的输出路径。
  - 示例: `export MEM_LOG_FILE="/path/to/memories.log"`
- **`MEM_JOURNEYS_ENABLED`**: 是否开启编辑日志功能。
  - 示例: `export MEM_JOURNEYS_ENABLED="true"`

## 6. 开发

- **安装依赖**: `bun install`
- **运行测试**: `bun test`
- **构建项目**: `bun run build`