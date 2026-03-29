#!/usr/bin/env python3
import argparse
import sys
import re
from pathlib import Path
from datetime import datetime
from schema_define import LibraryContext, MetadataParser
import subprocess

def rename_type(path: str, old_type: str, new_type: str, reason: str):
    """
    全库重命名一个实体类型，并同步更新元数据文件。
    """
    root = Path(path).resolve()
    ctx = LibraryContext(root, "Target Library")
    
    print(f"[*] 准备将类型 [{old_type}] 重命名为 [{new_type}]...")

    # 1. 扫描并更新实体文件
    affected_entities = []
    entity_files = list(ctx.entities_path.glob("*.md"))
    
    for file in entity_files:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
        
        metadata, body = MetadataParser.split_content(content)
        
        if metadata.get("entity type") == old_type:
            metadata["entity type"] = new_type
            metadata["date modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            new_content = MetadataParser.serialize(metadata) + body
            with open(file, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            affected_entities.append(file.stem)
            ctx.run_git(["add", str(file)])

    # 2. 更新 meta.md 中的定义
    if ctx.meta_path.exists():
        with open(ctx.meta_path, "r", encoding="utf-8") as f:
            meta_content = f.read()
        
        # 简单替换 meta.md 中的类型文本（通常在 # Entity Types 章节下）
        new_meta_content = meta_content.replace(f"- {old_type}", f"- {new_type}")
        if new_meta_content != meta_content:
            with open(ctx.meta_path, "w", encoding="utf-8") as f:
                f.write(new_meta_content)
            ctx.run_git(["add", str(ctx.meta_path)])
            print("[+] 已更新 meta.md 中的类型定义。")

    if not affected_entities:
        print("[INFO] 未发现属于该类型的实体。")
        return

    # 3. 调用 commit.py
    commit_script = Path(__file__).parent / "commit.py"
    try:
        subprocess.run([
            sys.executable, str(commit_script),
            "--path", str(root),
            "--action", "edit",
            "--target", "Global",
            "--reason", f"Rename type {old_type} -> {new_type} ({len(affected_entities)} entities): {reason}"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[WARN] 文件已更新但自动提交失败: {e}")

    print(f"[SUCCESS] 已完成 {len(affected_entities)} 个实体的类型更新。")

def main():
    if "--memo-cli-info" in sys.argv:
        print("Description: 全库范围内重命名特定的实体类型并同步文件。")
        print("Example: memocli rename-type --path . --old 旧类型 --new 新类型 --reason \"原因\"")
        sys.exit(0)

    is_memo_cli = "--memo-cli-call" in sys.argv
    action_name = Path(__file__).stem.replace("_", "-")

    parser = argparse.ArgumentParser(
        prog=f"memocli {action_name}" if is_memo_cli else None,
        description="全库重命名实体类型，同步更新 meta.md。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
用法示例:
  {'memocli ' + action_name if is_memo_cli else 'python3 ' + Path(__file__).name} --path . --old 旧类型 --new 新类型 --reason "规范化"
        """
    )
    parser.add_argument("--memo-cli-call", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-p", "--path", required=True, help="知识库根目录。")
    parser.add_argument("--old", required=True, help="旧类型名称。")
    parser.add_argument("--new", required=True, help="新类型名称。")
    parser.add_argument("-r", "--reason", required=True, help="操作原因。")
    
    args = parser.parse_args()
    
    try:
        rename_type(args.path, args.old, args.new, args.reason)
    except Exception as e:
        print(f"[ERROR] 类型重命名失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
