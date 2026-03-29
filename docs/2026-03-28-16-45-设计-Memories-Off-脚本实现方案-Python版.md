# 2026-03-28-16-45-设计-Memories-Off-脚本实现方案-Python版

## 1. 背景 (Background)
为了提升 `memories-off-skill` 在本地环境下的可执行性和确定性，需要开发一套配套的自动化脚本。相比 Node.js，Python 在处理本地文件系统、路径逻辑以及轻量级工具封装方面具有更精简的语法和更低的依赖成本。

## 2. 设计原则 (Design Principles)
- **Pythonic & Minimal**: 仅使用 Python 标准库（`pathlib`, `argparse`, `dataclasses`, `re`, `subprocess`），不引入第三方依赖。
- **原子化开发 (Single-Script Iteration)**: 每次仅编写一个功能脚本，完成后立即在 `memories-off-skill/SKILL.md` 对应位置添加“该功能可以用 `xxx.py` 实现”的标注。
- **Schema 驱动 (Schema-Driven)**: 核心实体定义（Entity）、解析逻辑（Parser）和库配置（LibraryConfig）统一集中在 `schema_define.py` 中，供各脚本复用。
- **完备的帮助信息 (Self-Documenting)**: 每个脚本必须通过 `argparse` 提供详尽的 `--help` 文档，包括参数描述、用法示例及返回报告说明。

## 3. 核心架构：共享逻辑 (`schema_define.py`)
- **`Entity` Data Class**: 存储实体名、类型、完整路径、解析后的 Frontmatter 字典及 Body 内容。
- **`MetadataParser`**: 实现标准的 YAML Frontmatter 提取、标准化（Normalization）及去重合并逻辑。
- **`GitInterface`**: 封装底层的 Git 调用逻辑（add, commit, mv, log），并格式化输出。

## 4. 脚本开发清单与顺序 (Script Inventory)

### 4.1 基础构建 (Foundation)
1. **`schema_define.py`**: 提供全套数据类与解析器基石。
2. **`init.py`**: 知识库初始化。
   - **功能**: 执行 `git init`，创建 `entities/` 和 `trash/`，初始化 `meta.md` 并执行 Initial Commit。
   - **更新**: `SKILL.md` 仓库布局部分。

### 4.2 观察与管理 (Observation & Management)
3. **`stats.py`**: 仓库概要统计。
   - **功能**: 统计实体总数、类型频率分布、Schema 摘要及近期活跃记录。
   - **更新**: `SKILL.md` 观察工具规格部分。
4. **`commit.py`**: 原子变更提交。
   - **功能**: 校验变更、自动暂存并按 `[Action] [Target]: [Reason]` 规范提交。
   - **更新**: `SKILL.md` 审计日志规范部分。

### 4.3 维护与同步 (Maintenance)
5. **`audit_fix.py`**: 引用一致性审计与修复。
   - **功能**: 发现孤儿关系、失效 WikiLinks，并提供自动修复模式。
   - **更新**: `SKILL.md` 维护与章节逻辑部分。
6. **`rename.py`**: 实体迁移与全局引用同步。
   - **功能**: 安全执行 `git mv` 并全量更新库内所有指向该实体的引用。
   - **更新**: `SKILL.md` 管理工具规格部分。

## 5. 开发流程 (Workflow)
1. **Plan**: 确定当前要编写的脚本参数与逻辑。
2. **Act**: 编写 Python 代码，确保 `--help` 信息详尽。
3. **Validate**: 在模板库上运行并验证输出报告。
4. **Doc**: 手术式精准更新 `SKILL.md`。
5. **Log**: 记录开发日志并请求用户确认。
