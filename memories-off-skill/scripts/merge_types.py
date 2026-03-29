#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from datetime import datetime
from schema_define import LibraryContext, MetadataParser
import subprocess

def merge_types(path: str, sources: list, target: str, reason: str):
    """
    将多个源类型合并到目标类型中，并同步更新元数据文件。
    """
    root = Path(path).resolve()
    ctx = LibraryContext(root, "Target Library")
    
    print(f"[*] 准备将类型 {sources} 合并至 [{target}]...")

    affected_entities = []
    entity_files = list(ctx.entities_path.glob("*.md"))
    
    for file in entity_files:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
        
        metadata, body = MetadataParser.split_content(content)
        
        current_type = metadata.get("entity type")
        if current_type in sources:
            metadata["entity type"] = target
            metadata["date modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            new_content = MetadataParser.serialize(metadata) + body
            with open(file, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            affected_entities.append(file.stem)
            ctx.run_git(["add", str(file)])

    # 更新 meta.md 定义
    if ctx.meta_path.exists():
        with open(ctx.meta_path, "r", encoding="utf-8") as f:
            meta_lines = f.readlines()
        
        new_meta_lines = []
        for line in meta_lines:
            # 移除源类型的行，保留目标类型（如果存在）
            is_source = any(f"- {src}" in line for src in sources)
            if not is_source:
                new_meta_lines.append(line)
        
        if len(new_meta_lines) != len(meta_lines):
            with open(ctx.meta_path, "w", encoding="utf-8") as f:
                f.writelines(new_meta_lines)
            ctx.run_git(["add", str(ctx.meta_path)])
            print("[+] 已从 meta.md 中移除旧的类型定义。")

    if not affected_entities:
        print("[INFO] 未发现属于源类型的实体。")
        return

    # 调用 commit.py
    commit_script = Path(__file__).parent / "commit.py"
    try:
        subprocess.run([
            sys.executable, str(commit_script),
            "--path", str(root),
            "--action", "edit",
            "--target", "Global",
            "--reason", f"Merge types {sources} into {target} ({len(affected_entities)} entities): {reason}"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[WARN] 文件已更新但自动提交失败: {e}")

    print(f"[SUCCESS] 已完成 {len(affected_entities)} 个实体的类型合并。")

def main():
    if "--memo-cli-info" in sys.argv:
        print("Description: 全库范围内将一个或多个实体类型合并为目标类型。")
        print("Example: memocli merge-types --path . --sources 源类型1,源类型2 --target 目标类型 --reason \"原因\"")
        sys.exit(0)

    is_memo_cli = "--memo-cli-call" in sys.argv
    action_name = Path(__file__).stem.replace("_", "-")

    parser = argparse.ArgumentParser(
        prog=f"memocli {action_name}" if is_memo_cli else None,
        description="将多个源类型合并到目标类型中，同步更新元数据。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
用法示例:
  {'memocli ' + action_name if is_memo_cli else 'python3 ' + Path(__file__).name} --path . --sources 源类型1,源类型2 --target 目标类型 --reason "合并重复项"
        """
    )
    parser.add_argument("--memo-cli-call", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-p", "--path", required=True, help="知识库根目录。")
    parser.add_argument("-s", "--sources", required=True, help="源类型名称列表（逗号分隔）。")
    parser.add_argument("-t", "--target", required=True, help="目标类型名称。")
    parser.add_argument("-r", "--reason", required=True, help="操作原因。")
    
    args = parser.parse_args()
    source_list = [s.strip() for s in args.sources.split(",")]
    
    try:
        merge_types(args.path, source_list, args.target, args.reason)
    except Exception as e:
        print(f"[ERROR] 类型合并失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
