#!/usr/bin/env python3
import argparse
import sys
import os
from pathlib import Path
from schema_define import LibraryContext

def commit_changes(path: str, action: str, target: str, reason: str):
    """
    执行符合 memories-off 规范的 Git 提交。
    """
    root = Path(path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"路径不存在: {root}")
    
    ctx = LibraryContext(root, "Target Library")
    
    if not ctx.is_git_repo():
        print(f"[ERROR] 该目录不是一个 Git 仓库，请先运行 init.py", file=sys.stderr)
        sys.exit(1)

    # 1. 检查是否有变更需要提交
    status = ctx.run_git(["status", "--porcelain"])
    if not status:
        print("[*] 工作区干净，没有需要提交的变更。")
        return

    # 2. 构造 Commit Message
    # 格式: [Action] [Target]: [Reason]
    commit_msg = f"{action} {target}: {reason}"
    
    print(f"[*] 正在提交变更...")
    print(f"    Action: {action}")
    print(f"    Target: {target}")
    print(f"    Reason: {reason}")

    try:
        # 3. 暂存变更 (add)
        ctx.run_git(["add", "."])
        
        # 4. 执行提交 (commit)
        result = ctx.run_git(["commit", "-m", commit_msg])
        
        print("\n[SUCCESS] 变更已成功提交！")
        print(f"Git 输出: {result.splitlines()[0] if result else 'Success'}")
        
        # 返回 XML 报告
        print(f"\n<commit_report status=\"success\">")
        print(f"  <message>{commit_msg}</message>")
        print(f"</commit_report>")
        
    except Exception as e:
        print(f"[ERROR] 提交失败: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    if "--memo-cli-info" in sys.argv:
        print("Description: 知识库变更的标准化 Git 提交工具（Audit Log）。")
        print("Example: memocli commit --path . --action edit --target 人物-cafe3310 --reason \"更新了技能列表\"")
        sys.exit(0)

    is_memo_cli = "--memo-cli-call" in sys.argv
    action_name = Path(__file__).stem.replace("_", "-")

    parser = argparse.ArgumentParser(
        prog=f"memocli {action_name}" if is_memo_cli else None,
        description="封装 Git 提交逻辑，生成符合 memories-off 规范的审计消息。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"用法示例:\n  {'memocli ' + action_name if is_memo_cli else 'python3 ' + Path(__file__).name} --path . --action edit --target 人物-cafe3310 --reason \"更新了技能列表\"\n  {'memocli ' + action_name if is_memo_cli else 'python3 ' + Path(__file__).name} -p ./kb -a create -t 宠物-咪咪 -r \"新增猫咪档案\""
    )
    parser.add_argument("--memo-cli-call", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-p", "--path", required=True, help="知识库的根目录路径。")
    parser.add_argument("-a", "--action", required=True, choices=["create", "edit", "rename", "delete", "fix", "init"], 
                        help="执行的操作类型。")
    parser.add_argument("-t", "--target", required=True, help="受影响的实体名或文件名。")
    parser.add_argument("-r", "--reason", required=True, help="执行该操作的原因。")
    
    args = parser.parse_args()
    
    try:
        commit_changes(args.path, args.action, args.target, args.reason)
    except Exception as e:
        print(f"[ERROR] 执行失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
