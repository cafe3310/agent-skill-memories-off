# 批量操作与 Token 节约指南 (Batch Operations & Token Optimization)

作为 Agent，你的上下文窗口（Token）是非常宝贵的资源。频繁地进行单步查询或全量读取不仅速度慢，还会迅速消耗 Token。

你被鼓励采用批量化的操作方式来最大化效率，减少不必要的重复调用。你的预设知识和 agent 设计提供给你的批量操作能力都可以被充分利用。

本文档也收集了一些在 `memories-off` 知识库中进行批量操作和节约 Token 的最佳实践。

---

## 1. 检索与加载：由面到点 (Retrieve & Load)

### 1.1 极简检索 (`--names-only`)
当你只需要知道“知识库里有没有相关的实体”，或者只想获取一个实体名列表时，使用 `--names-only` 标志，命令只会返回干练的名称列表。
```bash
memocli search-entities "项目" --type "Project" --names-only
```

### 1.2 批量加载 (`load-entities`)
当你通过检索或 `explore` 获得了几个关键实体的名称，并且确实需要读取它们的详细内容时，**不要**多次调用 `read_file`。
使用 `load-entities` 一次性精确加载多个实体，它会将结果打包在一个 XML 结构中返回。
```bash
memocli load-entities -n "实体A, 实体B, 实体C"
```
*提示：它甚至支持传入别名，系统会自动找回对应的标准实体。*

## 2. 结构化编辑：单次调用，多重修改 (Structured Editing)

### 2.1 批量创建关系 (`manage-relations`)
如果你需要为一个实体同时添加多个出站和入站关系，**不要**分多次调用命令。`manage-relations` 支持重复使用参数来一次性提交全部关系变更。
```bash
memocli manage-relations --source "中心实体" \
  --add-rel-out "属于: 部门A, 部门B" \
  --add-rel-out "参与: 项目X" \
  --add-rel-in "汇报给: 员工Y" \
  --reason "初始化中心实体的社交网络"
```

### 2.2 创建实体时直接完善属性 (`create-entity`)
在创建一个新实体时，尽量一次性通过参数把已知的信息全塞进去（正文、别名、关系），而不是先创建空文件再慢慢改。
```bash
echo "## 背景信息\n这是正文内容..." | memocli create-entity \
  --name "新项目" \
  --type "Project" \
  --aliases "项目X, ProjectX" \
  --add-rel-out "负责人: 张三" \
  --content-stdin \
  --reason "立项"
```

## 3. 全局观测：一站式获取上下文 (Global Observation)

### 3.1 活用 `explore`
当你初次接触一个知识库，或者需要了解整体架构时，`memocli explore` 是最具 Token 效率的命令。
它一次性返回了手册 (`meta.md`)、核心实体骨架、类型分布和所有命令的 `help`，避免了你反复调用 `ls`, `cat`, `grep` 去零散地拼凑库的结构。

### 3.2 活用 `get-relations`
与其用正则去暴力搜索所有文件来看看谁引用了“实体A”，不如直接使用 `memocli get-relations --entity "实体A"`。
它会高效扫描全库，直接返回该实体的“所有出站关系”和“所有指向它的入站关系”，这是了解图谱拓扑最经济的方法。

## 4. 自动化环境中的 Bash 循环
如果你（Agent）在分析了大量语料后，需要一次性创建几十个实体，你可以直接编写一个 Bash `for` 循环或一次性输出包含多条 `memocli` 命令的脚本文件来执行，只要确保每一条指令都正确传入了 `--reason` 即可。这比你逐个与用户确认或分多轮对话调用工具要高效得多。
