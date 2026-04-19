#!/usr/bin/env python3
import sys
from pathlib import Path
from utility.schema_define import ScriptBase

class CommitScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="commit",
            description="知识库变更的标准化 Git 提交工具（Audit Log）。",
            example='memocli commit --path . --reason "在此描述您的变更"'
        )
        # 移除 --action 和 --target，仅保留基类中的 --reason (作为 commit message)

    def run(self):
        self.setup()
        
        if self.args.reason == "none":
            self.error("必须提供提交理由 (--reason/-r)。", instruction="请补充理由后重试。")

        ctx = self.ctx
        if not ctx.is_git_repo():
            self.error("该目录不是一个 Git 仓库，请先运行 init 指令。", instruction="运行 memocli init 初始化仓库。")

        # 1. 检查是否有变更需要提交
        try:
            status = ctx.run_git(["status", "--porcelain"])
            if not status:
                self.add_result("工作区干净，没有需要提交的变更。")
                self.finalize(success=True)
                return
        except Exception as e:
            self.error(f"检查 Git 状态失败: {e}")

        # 2. 执行提交 (直接使用 reason 作为 commit message)
        commit_msg = self.args.reason

        try:
            # 暂存所有变更
            ctx.run_git(["add", "."])
            # 执行提交
            output = ctx.run_git(["commit", "-m", commit_msg])
            self.add_result(f"提交成功: {commit_msg}")
            self.add_result(output)
        except Exception as e:
            self.error(f"Git Commit 失败: {e}")

        self.finalize(success=True)

if __name__ == "__main__":
    CommitScript().run()
