#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from schema_define import LibraryContext

def init_library(path: str, name: str):
    """
    初始化 memories-off 知识库的主要逻辑。
    """
    root = Path(path).resolve()
    ctx = LibraryContext(root, name)
    
    print(f"[*] 正在初始化知识库: {name} (路径: {root})")
    
    # 1. 创建目录
    ctx.entities_path.mkdir(parents=True, exist_ok=True)
    
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
- 实体文件名：使用 [类型]-[名称] 格式。
- 关系值规范：使用纯文本实体名。
"""
        with open(ctx.meta_path, "w", encoding="utf-8") as f:
            f.write(meta_content)
        print("[+] 已创建 meta.md 手册模版")

    # 3. 初始化 Git (若不存在)
    if not ctx.is_git_repo():
        ctx.run_git(["init"])
        print("[+] 已初始化 Git 仓库")
    
    # 4. 执行 Initial Commit
    ctx.run_git(["add", "."])
    commit_msg = f"init: 初始化 {name} 知识库"
    ctx.run_git(["commit", "-m", commit_msg])
    print(f"[+] 已完成初始提交: {commit_msg}")
    
    print("\n[SUCCESS] 知识库初始化成功！")

def main():
    if "--memo-cli-info" in sys.argv:
        print("Description: 在指定目录下初始化一个新的 Memories-Off 知识库（meta.md + entities/）。")
        print("Example: memocli init --path ./my_kb --name \"我的知识库\"")
        sys.exit(0)

    is_memo_cli = "--memo-cli-call" in sys.argv
    action_name = Path(__file__).stem.replace("_", "-")

    parser = argparse.ArgumentParser(
        prog=f"memocli {action_name}" if is_memo_cli else None,
        description="初始化一个符合 memories-off 规范的 Git 驱动知识库。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"用法示例:\n  {'memocli ' + action_name if is_memo_cli else 'python3 ' + Path(__file__).name} --path ./my_kb --name \"我的知识库\"\n  {'memocli ' + action_name if is_memo_cli else 'python3 ' + Path(__file__).name} -p ./kb -n \"PersonalKB\""
    )
    parser.add_argument("--memo-cli-call", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-p", "--path", required=True, help="知识库的根目录路径。")
    parser.add_argument("-n", "--name", required=True, help="知识库显示的名称。")
    
    args = parser.parse_args()
    
    try:
        init_library(args.path, args.name)
    except Exception as e:
        print(f"[ERROR] 初始化失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
