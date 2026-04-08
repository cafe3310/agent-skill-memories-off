#!/usr/bin/env python3
import sys
from pathlib import Path
from schema_define import ScriptBase

class CommitScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="commit",
            description="知识库变更的标准化 Git 提交工具（Audit Log）。",
            example="memocli commit --path . --action edit --target 人物-cafe3310 --reason \"更新了技能列表\""
        )
        self.parser.add_argument("-a", "--action", required=True, 
                            choices=["create", "edit", "rename", "delete", "fix", "init", "merge", "consolidate"], 
                            help="执行的操作类型。")
        self.parser.add_argument("-t", "--target", required=True, help="受影响的实体名或文件名。")

    def run(self):
        self.setup()
        
        if self.args.reason == "none":
            self.error("必须提供提交理由 (--reason/-r)。", instruction="请补充理由后重试。")

        ctx = self.ctx
        if not ctx.is_git_repo():
            self.error("该目录不是一个 Git 仓库，请先运行 init 指令。", instruction="运行 memocli init 初始化仓库。")

        self.add_result(f"准备提交变更: [{self.args.action}] {self.args.target}")

        # 1. 检查是否有变更需要提交
        try:
            status = ctx.run_git(["status", "--porcelain"])
            if not status:
                self.add_result("工作区干净，没有需要提交的变更。")
                self.finalize(success=True)
                return
        except Exception as e:
            self.error(f"检查 Git 状态失败: {e}")

        # 2. 构造 Commit Message
        commit_msg = f"{self.args.action} {self.args.target}: {self.args.reason}"

        # 3. 执行提交
        try:
            # 暂存变更
            ctx.run_git(["add", "."])
            # 执行提交
            result = ctx.run_git(["commit", "-m", commit_msg])
            self.add_result("变更已成功提交！")
            self.add_result(f"Git 输出: {result.splitlines()[0] if result else 'Success'}")
        except Exception as e:
            self.error(f"Git 提交失败: {e}", instruction="请检查 Git 配置或解决冲突。")

        self.finalize(success=True)

if __name__ == "__main__":
    CommitScript().run()
