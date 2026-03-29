# 文档: 新版 Agent Skill 与 memocli 设计说明

## 1. 背景与改造目标
基于“极致压缩”和“Agent 友好”的原则，`memories-off` 从复杂的 MCP Server 架构转型为轻量级的 **Agent Skill** 风格工具集。其核心目标是让 Agent 在命令行环境下以最低的输入成本实现高效、安全的库管理。

## 2. 核心架构：memocli
`memocli` 是本工具的统一命令行入口。它是一个运行在 Bash 下的包装器，但通过 `install.py` 安装器自动生成：
- **安装逻辑**: 安装器会自动探测 Skill 的物理路径，并根据子命令的 `memo-cli-info` 协议自动生成带有描述信息的全局帮助列表。
- **参数自识别**: 当在知识库根目录下执行任务时，`memocli` 能自动识别 `meta.md` 并自动注入当前路径 (`--path .`)，无需 Agent 手动提供。
- **报错自适应**: 当子命令报错或显示帮助时，输出信息会从底层的 `.py` 脚本名自动切换为 `memocli` 风格。

## 3. 功能特性
- **Git 审计**: 所有由脚本发起的实体增删改，都通过 `commit.py` 记录。每条记忆都有完整的 Git 审计日志和变更原因。
- **检索逻辑 (Grep-First)**: 系统规范建议并强制 Agent 首先使用全文关键词搜索 (`grep_search`) 库内正文，确保不因文件名不符而漏掉知识点。
- **缓冲更新 (Buffer-Update)**: 为保障数据安全，修改操作推荐使用 `append_update` 子命令追加更新块，而不是直接重写已有章节。

## 4. 调用示例
Agent 可以通过以下简洁指令操作库：
- `memocli stats`：了解库内有多少实体、哪些类型。
- `memocli init --path .`：在当前目录初始化一个库。
- `memocli create_entity --name "张三" --type "人物" --reason "新的合作伙伴"`。
- `memocli append_update --entity "张三" --content "今天下午见了一面。" --reason "更新记录"`。

## 5. 优势总结
- **低 Token 消耗**: `memocli` 的子命令列表简洁明了，Agent 只需看一眼帮助就能理解所有子命令的用途。
- **无感路径注入**: 通过智能路径探测，Agent 可以更自然地在 Shell 环境下操作库。
- **极致便携**: 除了 Python 3 环境，没有任何其他外部依赖。
