# memories-off

## 愿景

提供一个极简、结构化的本地知识管理方案，让你的 Agent 具备长期记忆，且文档对人类阅读和编辑也足够友好。

通过一套标准化的 Markdown 实体规范和配套的自动化脚本，`memories-off` 允许 Agent 像管理代码仓库一样管理你的个人知识。它能从日常对话、文档、项目中提取知识点，并以 Git 驱动的方式维护一个可审计、可回滚的本地知识库。

> 目前这个 project 从早期的 MCP Server 更换为 Agent Skill（包含 python script） 架构，如果仍需使用旧版 MCP 服务，可以 checkout `v2` 分支。

这个项目的初始版本基于 [Anthropic 的 memory mcp](https://github.com/modelcontextprotocol/servers/blob/main/src/memory/README.md)。

## 特性目标

- **便携轻量，本地优先**：基于本地文件，不需要部署。
- **结构化知识**：将碎片化信息转化为实体、关系，构建个人知识图谱。
- **一站式探索**：通过 `explore` 命令快速获取全库架构、手册规范及统计分布。
- **强制审计**：Git 驱动的所有变更均包含 `reason`。
- **排版合规**：强制执行 H1（实体名）与 H2（业务章节）的层级规范。

## 快速开始

### 自动安装 (通过 Agent)

如果您使用的是支持自动执行的 Coding Agent (例如 Gemini CLI, Claude 等)，您可以直接对它说：
「执行 memories-off-skill 内部的 scripts/install.py 以安装 CLI 工具。」

### 使用 memocli 管理知识库

`memocli` 是对 Skill 内部 Python 脚本的封装。

- **全景探索 (首选)**：直接运行 `memocli explore`。它会为你返回 `meta.md` 全文、架构骨架预览、全量类型与关系分布、以及所有子命令的最新帮助。
- **初始化知识库**：`memocli init --path ./my_knowledge`。
- **创建新实体**：`memocli create-entity --name "五一计划" --type "项目" --reason "准备假期"`。
- **获取帮助**：
  - `memocli --help`：查看所有可用子命令。
  - `memocli <subcommand> --help`：查看特定命令的详细参数。

## 设计与工具

### 知识库结构

- `meta.md`：核心规章，定义实体类型（Schema）与关系谓词，并通过 WikiLinks 建立架构基石。
- `entities/`：存放所有 `.md` 格式的知识实体。
- Git 审计：所有通过脚本触发的修改都会产生一条带有 `reason` 的 Git Commit。

#### 知识库例子

```text
cafe3310-family/
├── .git/                   # 版本控制
├── meta.md                 # 知识库手册
└── entities/               # 实体目录
    ├── 人类-cafe3310.md    # 实体：cafe3310 (主人)
    ├── 猫-咩咩.md          # 实体：咩咩 (猫咪)
    └── 猫-啾啾.md          # 实体：啾啾 (猫咪)
```

##### 文件内容示例 (遵循 H1/H2 规范)

**`entities/人类-cafe3310.md`**
```markdown
---
entity type: 人类
date created: 2026-04-03 12:00:00
date modified: 2026-04-20 00:30:00
relation as 饲养: 猫-咩咩, 猫-啾啾
---

# 人类-cafe3310

## 基础介绍
养猫的，也整各种花活。
Github: @cafe3310
Twitter: @rh3cat
```

**`entities/猫-咩咩.md`**
```markdown
---
entity type: 猫
date created: 2026-04-03 12:00:00
relation as 宠物于: 人类-cafe3310
---

# 猫-咩咩

## 性格特点
cafe3310 家两只超可爱三花猫里的姐姐。
黏人，不过也一肚子坏水。
```

### 常用指令示例

- **探索**: 先看下我的知识库里现在都有什么：`memocli explore`。
- **检索**: 搜索关于‘理财’的笔记：`memocli search-entities "理财" --content`。
- **追加 (推荐 STDIN 模式)**: 
  - 为了避开复杂的 Shell 转义（引号、多行等），推荐让 Agent 使用管道传输内容：
  - `echo "## 补充内容\n- 关键点 A\n- 关键点 B" | memocli append-update --entity "五一计划" --content-stdin --reason "讨论补充"`
- **治理**: 审计并自动修复库里的标题层级：`memocli doctor --rule-normalize-headers --fix --reason "标准化层级"`。
- **审计**: 提交手动修改：`memocli commit --reason "更新了人物关系定义"`。
