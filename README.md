# memories-off

## 愿景

提供一个极简、结构化的本地知识管理方案，让你的 Agent 具备长期记忆，且文档对人类阅读和编辑也足够友好。

通过一套标准化的 Markdown 实体规范和配套的自动化脚本，`memories-off` 允许 Agent 像管理代码仓库一样管理你的个人知识。它能从日常对话、文档、项目中提取知识点，并以 Git 驱动的方式维护一个可审计、可回滚的本地知识库。

> 目前这个 project 从早期的 MCP Server 更换为 Agent Skill（包含 python script） 架构，如果仍需使用旧版 MCP 服务，可以 checkout `v2` 分支。
> 旧版本的文档和构建方式请参考该 tag 下的 `README.md`。

这个项目的初始版本基于 [Anthropic 的 memory mcp](https://github.com/modelcontextprotocol/servers/blob/main/src/memory/README.md)。

## 特性目标

- **便携轻量，本地优先**：基于本地文件，不需要部署或使用大规模在线服务，不与任何模型、服务或架构绑定。
- **结构化知识**：通过 LLM 能力，将你丢给它的任何文本中的信息，转化为实体、关系、观察，构建个人知识图谱。
- **灵活检索**：支持通过实体名、类型、观察内容的关键词检索，让 LLM 获取长期记忆并在对话中直接使用。
- **数据可读性与备份**：原始数据保持可读，提供简单的备份功能。

目标不会包括：

- **大规模知识**：保持轻量级，适合个人或小型项目使用。
- **复杂关系**：不用把小工具整成 SQL。
- **在线服务**：不考虑联网，数据存储在本地文件中。
- **多用户协作**：不会考虑。
- **权限**：不会考虑。
- **多语言**：只考虑中文。

## 应用例子

### 个人使用

- **提取知识**：将文档、日常对话或大段聊天记录发给 LLM，自动提取关键知识点、人物、项目信息、协作关系、个人风格等，构建你的专属知识库。
- **个性化内容生成**：借助知识图谱，LLM 能更好地理解你的思考习惯和人际网络，有针对性地模仿你的表达，生成符合你个性风格的沟通、总结或项目文档。

### 项目使用

- **项目知识库**：小团队可用作项目级别的知识库，持续积累和管理知识，比如联合支付能力 MCP 服务，记录用户购物偏好、行为习惯等。
- **优化 Agent 服务质量**：让你的 Agent 记住更多历史数据与业务诉求，动态调整流程或输出，如记住并优化利用支付能力 MCP 服务推销时的有效策略，提高应用场景中的转化率与满意度。

## 快速开始

### 如果你已经有 Coding Agent

可以告诉它「Clone 这个仓库 https://github.com/cafe3310/agent-skill-memories-off/ 到临时目录，阅读其 README.md，将其 memories-off-skill 目录改名为 memories-off 并复制到我们的 Agent Skill 目录，然后执行复制后目录其内部的 scripts/install.py 以安装 CLI 工具」。

### 安装 Skill 与 CLI

本项目目前以 Agent Skill 的形式提供服务，包含一个 cli 工具 `memocli`，它是对内部 Python 脚本的封装。

1. 将本项目链接或复制到您的 Agent Skill 目录中（例如 `~/.agents/skills/memories-off-skill`）。
2. **安装命令行工具 `memocli`**。
   你可以让 Agent 帮你安装。说「帮我安装 memories-off-skill 的命令行工具 `memocli`」即可。
   或者手动在终端安装：
   ```bash
   cd memories-off-skill
   python3 scripts/install.py
   ```
   安装脚本 `install.py` 会自动探测路径并将 `memocli` 包装器安装到您的系统 `PATH` 中。

### 使用 memocli 管理知识库

`memocli` 是对 Skill 内部底层 Python 脚本的封装。

- **查看库状态**：直接运行 `memocli stats`（在库根目录下无需指定 `--path`）。
- **初始化知识库**：`memocli init --path ./my_knowledge`。
- **创建新实体**：`memocli create_entity --name "五一计划" --type "计划" --reason "准备假期"`。
- **获取帮助**：
  - `memocli --help`：查看所有可用子命令及其一句话描述。
  - `memocli <subcommand> --help`：查看特定命令的详细参数和示例。

### Agent 集成建议

你可以参考 `prompts/个人助手.md` 中的示例提示词，或根据需要自定义提示词来指导 Agent 如何使用 `memories-off`。

在系统提示词（System Prompt）中，建议明确指示 Agent：
- 优先使用 `memocli` 进行所有知识库操作。
- 告诉 Agent，如果它正在知识库根目录工作，可以不必提供 `--path` 参数。

## 设计与工具

### 知识库结构

- `meta.md`：核心规章，定义实体类型（Schema）与关系谓词。
- `entities/`：存放所有 `.md` 格式的知识实体。
- Git 审计：所有由脚本触发的修改都会产生一条带有 `reason` 的 Git Commit，确保变更可追溯。

#### 知识库例子

为了方便快速理解，这里展示一个名为 `cafe3310-family` 的知识库结构，包含了主人及其猫咪的实体：

```text
cafe3310-family/
├── .git/                   # 版本控制
├── meta.md                 # 知识库手册
└── entities/               # 实体目录
    ├── 人类-cafe3310.md    # 实体：cafe3310 (主人)
    ├── 猫-咩咩.md          # 实体：咩咩 (猫咪)
    └── 猫-啾啾.md          # 实体：啾啾 (猫咪)
```

在这个例子中，展示了家庭成员的构成：

- **cafe3310**: 知识库的主人，是一位热爱生活的人类。
- **咩咩**: 一只可爱的三花猫，性格温顺。
- **啾啾**: 同样是可爱的三花猫。她性格活泼，非常讨人喜欢，甚至还有自己的专属微信表情包「三花猫啾啾」，超级可爱！

##### 文件内容示例

以下是上述实体的 Markdown 文件内容示例：

**`entities/人类-cafe3310.md`**
```markdown
---
entity type: 人类
date created: 2026-04-03
relation as owner of: 猫-咩咩, 猫-啾啾
---

## cafe3310

养猫的，也整各种花活。
Github: @cafe3310
Twitter: @rh3cat

```

**`entities/猫-咩咩.md`**
```markdown
---
entity type: 猫
date created: 2026-04-03
relation as pet of: 人类-cafe3310
---

## 咩咩

cafe3310 家两只超可爱三花猫里的姐姐。
黏人，不过也一肚子坏水。
```

**`entities/猫-啾啾.md`**
```markdown
---
entity type: 猫
date created: 2026-04-03
relation as pet of: 人类-cafe3310
---

## 啾啾

cafe3310 家两只超可爱三花猫里的妹妹。
性格活泼，没什么心眼。

## 明星特质

有自己的专属微信表情包「三花猫啾啾」。
```

### 常用指令示例

你可以像这样指挥你的 Agent：
你可以像这样对你的 Agent 发出指令：

- 加载 memories-off 技能，并在当前目录初始化一个名为‘我的生活’的知识库。
- 先看下我的知识库里现在都有什么（Agent 会运行 `stats.py`），搜索关于‘理财’的笔记。
- 把刚才关于五一出行的讨论记录下来，建立一个「计划」类型的实体，并关联到「cafe3310」。
- 审计一下库里的引用有没有断掉的；把「张三」和「张小三」这两个实体合并了。
- 我已经手动改了 `meta.md`，你帮我提交一下，理由是「更新了人物关系定义」。
