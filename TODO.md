# 项目待办事项 (TODO.md)

本项目采用 `doc-todo-log-loop` 工作流。所有开发任务必须经用户指派后方可执行。

---

## 阶段 1: Agent Skill 风格实现 (当前优先级)

### 1.1 基础架构搭建
- [ ] 1.1.1 初始化新的项目结构 (package.json, tsconfig.json, 基础目录)
- [ ] 1.1.2 实现核心类型定义 (基于 `legacy-v3-dev/src/v2/editor/types.ts` 和优化建议)
- [ ] 1.1.3 实现底层文件操作封装 (`file-ops.ts`)

### 1.2 核心编辑器 (Editor) 开发
- [ ] 1.2.1 实现 Markdown 解析与 TOC 生成逻辑
- [ ] 1.2.2 实现 Frontmatter 处理逻辑
- [ ] 1.2.3 实现基于 Locator 的章节编辑逻辑 (Add/Replace Section)

### 1.3 工具集 (Tools) 实现
- [ ] 1.3.1 实现“库观察”类工具 (loadManual, getLibraryStats)
- [ ] 1.3.2 实现“实体检索”类工具 (searchEntitiesByName, findEntitiesByMetadata)
- [ ] 1.3.3 实现“实体阅读”类工具 (loadEntities, loadEntitiesSections)

### 1.4 关系管理 (Relations)
- [ ] 1.4.1 实现实体间关系的创建与删除逻辑

---

## 阶段 2: CLI 优化与 Token 压缩 (待办)

- [ ] 2.1 设计并实现精简版 CLI 输出格式
- [ ] 2.2 重构工具集以支持 CLI 调用模式
- [ ] 2.3 进行 Token 消耗对比测试与优化

---

## 已完成任务 (Done)
- [x] 2026-03-28 项目结构重组，旧代码归档至 `legacy-v3-dev/`
- [x] 2026-03-28 更新项目章程 (`AGENTS.md`, `GEMINI.md`)，确立新开发战略
