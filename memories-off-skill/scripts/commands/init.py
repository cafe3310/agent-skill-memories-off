#!/usr/bin/env python3
import sys
from pathlib import Path
from utility.runtime import ScriptBase
from utility.schema_define import LibraryContext

class InitScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="init",
            description="在指定目录下初始化一个新的 Memories-Off 知识库（meta.md + entities/）。",
            example="memocli init --path ./my_kb --name \"我的知识库\""
        )
        self.parser.add_argument("-n", "--name", required=True, help="知识库显示的名称。")

    def run(self):
        # 注意：init 比较特殊，它的 path 允许不存在，所以手动处理 setup 的一部分逻辑
        self.args = self.parser.parse_args()
        root_path = Path(self.args.path).resolve()
        name = self.args.name
        
        self.add_result(f"正在初始化知识库: {name} (路径: {root_path})")
        
        # 1. 创建目录
        try:
            root_path.mkdir(parents=True, exist_ok=True)
            ctx = LibraryContext(root_path, name)
            ctx.entities_path.mkdir(parents=True, exist_ok=True)
            self.add_result("[+] 已创建实体目录结构。")
        except Exception as e:
            self.error(f"创建目录失败: {e}")

        # 2. 创建 meta.md (若不存在)
        if not ctx.meta_path.exists():
            meta_content = f"""# Knowledge Base Manual (meta.md)

## 1. 概述 (Overview)
这是名为 `{name}` 的知识库手册，遵循 memories-off 规范。

## 2. 核心 Schema (Core Schema)
### 实体类型 (Entity Types):
- 人物
- 概念
- 项目

## 3. 命名与编辑准则
- 实体命名：**文件名即实体名** (例如 `cafe3310.md`)。
- 实体类型：由 `entity type` 元数据指定。
- 关系值规范：使用实体名称（WikiLinks `[[实体名]]` 或显式关系 `relation as ...`）。

"""
            try:
                with open(ctx.meta_path, "w", encoding="utf-8") as f:
                    f.write(meta_content)
                self.add_result("[+] 已创建 meta.md 手册模版。")
            except Exception as e:
                self.add_result(f"[!] 创建 meta.md 失败: {e}")
        else:
            self.add_result("[*] meta.md 已存在，跳过创建。")

        # 3. 初始化 Git (若不存在)
        if not ctx.is_git_repo():
            try:
                ctx.run_git(["init"])
                self.add_result("[+] 已初始化 Git 仓库。")
            except Exception as e:
                self.add_result(f"[!] Git 初始化失败: {e}")
        
        # 4. 执行 Initial Commit
        if ctx.is_git_repo():
            try:
                ctx.run_git(["add", "."])
                commit_msg = f"init: 初始化 {name} 知识库"
                ctx.run_git(["commit", "-m", commit_msg])
                self.add_result(f"[+] 已完成初始提交: {commit_msg}")
            except Exception as e:
                self.add_result(f"[!] 初始提交失败: {e}")
        
        self.add_result("知识库初始化成功！")
        self.finalize(success=True)

if __name__ == "__main__":
    InitScript().run()
