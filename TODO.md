# 项目待办事项 (TODO.md)

本项目采用 `doc-todo-log-loop` 工作流。所有开发任务必须经用户指派后方可执行。
最新详细待办请参考：[[2026-04-12-15-25-计划-全量待办任务汇总]]

---

## 核心任务流 (Roadmap) - 2026-04-12 更新

### 1. [紧急/高优先] 规范与行为同步
- [ ] **更新 Agent 行为准则 (`SKILL.md`)**：同步“缓冲更新 (Consolidate)”机制，替换旧的编辑模式。
- [ ] **执行实体命名标准化迁移**：运行 `migration-naming-v2` 彻底清理历史文件命名。

### 2. [核心/待办] 检索与性能补全
- [ ] **实现 `batch_ops.py`**：支持原子操作批量执行与单次提交。
- [ ] **补全检索工具**：`findEntitiesByMetadata`, `searchEntitiesGlobally`。
- [ ] **实现系统维护工具**：`backupLibrary`, `garbageCollectRelations`。

### 3. [工程/优化] 体验增强
- [ ] 生成 ZSH/Bash 动态补全脚本。
- [ ] 进行全量协议适配后的 Token 压缩压力测试。

---

## 已完成任务 (Done)
- [x] 2026-04-12 **[架构全量适配]** 17 个核心脚本完成 `ScriptBase` (XML 协议) 适配。
- [x] 2026-04-12 **[编辑闭环]** 完成 `consolidate_updates.py` (梦境整理) 实现。
- [x] 2026-04-12 **[迁移就绪]** 完成 `migration_naming_v2.py` (带链接修复) 实现。
- [x] 2026-04-10 完成 `memocli` 枚举参数与全局帮助增强设计。
- [x] 2026-03-29 实现 `memocli` 安装与功能转发机制。
- [x] 2026-03-28 项目结构重组，旧代码归档至 `legacy-v3-dev/`
