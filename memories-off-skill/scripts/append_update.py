#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from datetime import datetime
from schema_define import LibraryContext
import subprocess

def append_update(path: str, entity_name: str, target_heading: str, action: str, content: str, reason: str):
    """
    向实体文件末尾追加一个格式化的更新块。
    """
    root = Path(path).resolve()
    ctx = LibraryContext(root, "Target Library")
    
    entity_file = ctx.entities_path / f"{entity_name}.md"
    if not entity_file.exists():
        print(f"[ERROR] 实体不存在: {entity_file}", file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 构造更新块
    block = [
        "\n",
        "--- [UPDATE BLOCK] ---",
        f"timestamp: {timestamp}",
        f"target_heading: \"{target_heading}\"",
        f"action: \"{action}\"",
        "content: |",
        # 对内容进行缩进处理，以符合 YAML block scalar 风格
        "\n".join(f"  {line}" for line in content.strip().splitlines()),
        "--- [END OF UPDATE BLOCK] ---",
        "\n"
    ]
    
    with open(entity_file, "a", encoding="utf-8") as f:
        f.write("\n".join(block))
    
    # 调用 commit.py
    commit_script = Path(__file__).parent / "commit.py"
    try:
        subprocess.run([
            sys.executable, str(commit_script),
            "--path", str(root),
            "--action", "edit",
            "--target", entity_name,
            "--reason", f"Buffer update for {entity_name}: {reason}"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[WARN] 文件已更新但自动提交失败: {e}")
    
    print(f"[SUCCESS] 已向 {entity_name} 追加更新块并提交审计。")

def main():
    if "--memo-cli-info" in sys.argv:
        print("Description: 向已有实体追加非破坏性的更新块（Buffer-Update 模式）。")
        print("Example: memocli append-update --path . --entity 实体名 --action append --content \"内容\" --reason \"理由\"")
        sys.exit(0)

    is_memo_cli = "--memo-cli-call" in sys.argv
    action_name = Path(__file__).stem.replace("_", "-")

    parser = argparse.ArgumentParser(
        prog=f"memocli {action_name}" if is_memo_cli else None,
        description="向实体文件追加缓冲更新块，确保内容不丢失。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"用法示例:\n  {'memocli ' + action_name if is_memo_cli else 'python3 ' + Path(__file__).name} --path . --entity 实体名 --action append --content \"内容\" --reason \"理由\""
    )
    parser.add_argument("--memo-cli-call", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-p", "--path", required=True, help="知识库根目录。")
    parser.add_argument("-e", "--entity", required=True, help="目标实体名称。")
    parser.add_argument("-th", "--target_heading", default="", help="目标章节标题。")
    parser.add_argument("-a", "--action", choices=["append", "replace", "new_section"], required=True, help="动作类型。")
    parser.add_argument("-c", "--content", required=True, help="要更新的具体内容。")
    parser.add_argument("-r", "--reason", required=True, help="操作原因。")
    
    args = parser.parse_args()
    
    try:
        append_update(args.path, args.entity, args.target_heading, args.action, args.content, args.reason)
    except Exception as e:
        print(f"[ERROR] 追加更新块失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
