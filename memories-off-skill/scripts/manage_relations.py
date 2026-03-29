#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from datetime import datetime
from schema_define import LibraryContext, MetadataParser
import subprocess

def manage_relation(path: str, entity_name: str, action: str, predicate: str, target: str, reason: str):
    """
    通过脚本精确建立或删除语义关系，并更新元数据。
    """
    root = Path(path).resolve()
    ctx = LibraryContext(root, "Target Library")
    
    entity_file = ctx.entities_path / f"{entity_name}.md"
    if not entity_file.exists():
        print(f"[ERROR] 实体不存在: {entity_file}", file=sys.stderr)
        sys.exit(1)

    # 1. 验证目标实体是否存在 (仅 add 时)
    if action == "add":
        target_file = ctx.entities_path / f"{target}.md"
        if not target_file.exists():
            print(f"[ERROR] 关联目标实体不存在: {target}", file=sys.stderr)
            sys.exit(1)

    # 2. 读取并解析内容
    with open(entity_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    metadata, body = MetadataParser.split_content(content)
    
    # 构造关系 Key (遵循 memories-off 规范)
    rel_key = f"relation as {predicate.strip().lower()}"
    
    # 3. 执行动作
    changed = False
    current_targets = []
    if rel_key in metadata:
        current_targets = [t.strip() for t in metadata[rel_key].split(",")]

    if action == "add":
        if target not in current_targets:
            current_targets.append(target)
            metadata[rel_key] = ", ".join(current_targets)
            changed = True
            print(f"[*] 已添加关系: {entity_name} --[{predicate}]--> {target}")
    elif action == "delete":
        if target in current_targets:
            current_targets.remove(target)
            if not current_targets:
                del metadata[rel_key]
            else:
                metadata[rel_key] = ", ".join(current_targets)
            changed = True
            print(f"[*] 已删除关系: {entity_name} --[{predicate}]--> {target}")

    if not changed:
        print("[INFO] 关系未发生变动，跳过。")
        return

    # 4. 更新元数据 (date modified)
    metadata["date modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 5. 写回文件
    new_content = MetadataParser.serialize(metadata) + body
    with open(entity_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    # 6. 调用 commit.py
    commit_script = Path(__file__).parent / "commit.py"
    try:
        subprocess.run([
            sys.executable, str(commit_script),
            "--path", str(root),
            "--action", "edit",
            "--target", entity_name,
            "--reason", f"Update relation ({predicate}): {reason}"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[WARN] 文件已更新但自动提交失败: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="管理实体的语义关系，自动处理元数据更新与审计。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
用法示例:
  python manage_relations.py --path . --entity 人物-cafe3310 --action add --predicate 负责人 --target 概念-Memory-Skill --reason "项目立项"
  python manage_relations.py -p . -e 宠物-咪咪 -a delete -t 人物-cafe3310 -pr 所有者 -r "变更关系"
        """
    )
    parser.add_argument("-p", "--path", required=True, help="知识库根目录。")
    parser.add_argument("-e", "--entity", required=True, help="要修改的实体名称。")
    parser.add_argument("-a", "--action", choices=["add", "delete"], required=True, help="执行动作：添加或删除。")
    parser.add_argument("-pr", "--predicate", required=True, help="谓词（关系类型）。")
    parser.add_argument("-t", "--target", required=True, help="关联的目标实体名称。")
    parser.add_argument("-r", "--reason", required=True, help="修改原因。")
    
    args = parser.parse_args()
    
    try:
        manage_relation(args.path, args.entity, args.action, args.predicate, args.target, args.reason)
    except Exception as e:
        print(f"[ERROR] 关系管理失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
