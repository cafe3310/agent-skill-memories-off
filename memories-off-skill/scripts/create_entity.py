#!/usr/bin/env python3
import argparse
import sys
from datetime import datetime
from pathlib import Path
from schema_define import LibraryContext, MetadataParser
import subprocess

def create_entity(path: str, name: str, entity_type: str, relations: str, reason: str):
    """
    创建符合规范的实体文件并执行 Initial Commit。
    自动处理 [类型-名称] 的命名契约。
    """
    root = Path(path).resolve()
    ctx = LibraryContext(root, "Target Library")
    
    # 1. 处理命名契约: [类型-名称]
    prefix = f"{entity_type}-"
    if not name.startswith(prefix):
        full_name = f"{prefix}{name}"
    else:
        full_name = name

    # 标准化名称与路径
    normalized_name = MetadataParser.normalize_name(full_name)
    file_path = ctx.entities_path / f"{normalized_name}.md"
    
    if file_path.exists():
        print(f"[ERROR] 实体已存在: {file_path}", file=sys.stderr)
        sys.exit(1)

    # 2. 准备元数据
    today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 使用 MetadataParser.serialize 保证格式统一
    metadata = {
        "entity type": entity_type,
        "date created": today,
        "date modified": today,
        "status": "draft"
    }
    
    # 解析并添加关系 (格式示例: "成员: 某组织, 负责: 某项目")
    if relations:
        rel_items = [r.strip() for r in relations.split(",")]
        for item in rel_items:
            if ":" in item:
                k, v = item.split(":", 1)
                metadata[f"relation as {k.strip().lower()}"] = v.strip()

    # 3. 构造初始内容
    body = f"\n# {name}\n\n(在此输入实体描述)"
    content = MetadataParser.serialize(metadata) + body
    
    # 4. 写入文件
    print(f"[*] 正在创建实体: {normalized_name} (路径: {file_path})")
    ctx.entities_path.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    # 5. 调用外部 commit.py 执行标准化提交
    commit_script = Path(__file__).parent / "commit.py"
    try:
        subprocess.run([
            sys.executable, str(commit_script),
            "--path", str(root),
            "--action", "create",
            "--target", normalized_name,
            "--reason", reason
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[WARN] 实体已创建但自动提交失败: {e}")

    # XML 报告 (明确返回生成的实体名，供 Agent 后续引用)
    print(f"\n<create_report entity_name=\"{normalized_name}\" file=\"{file_path.name}\">")
    print(f"  <status>success</status>")
    print(f"  <message>Created entity with standardized name: {normalized_name}</message>")
    print("</create_report>")

def main():
    if "--memo-cli-info" in sys.argv:
        print("Description: 创建符合规范的新实体文件，并处理命名契约。")
        print("Example: memocli create-entity --path . --name 咪咪 --type 宠物 --relations \"成员: 咖啡馆\" --reason \"新增宠物档案\"")
        sys.exit(0)

    is_memo_cli = "--memo-cli-call" in sys.argv
    action_name = Path(__file__).stem.replace("_", "-")

    parser = argparse.ArgumentParser(
        prog=f"memocli {action_name}" if is_memo_cli else None,
        description="自动化创建符合规范的知识实体，自动补全 [类型-名称] 前缀。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"用法示例:\n  {'memocli ' + action_name if is_memo_cli else 'python3 ' + Path(__file__).name} --path . --name 咪咪 --type 宠物 --relations \"成员: 咖啡馆\" --reason \"新增宠物档案\""
    )
    parser.add_argument("--memo-cli-call", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-p", "--path", required=True, help="知识库根目录。")
    parser.add_argument("-n", "--name", required=True, help="实体显示名称。")
    parser.add_argument("-t", "--type", required=True, help="实体分类（单一值）。")
    parser.add_argument("-rel", "--relations", help="初始关系（格式：'谓词: 目标, ...'）。")
    parser.add_argument("-r", "--reason", required=True, help="创建原因（用于 Git Commit）。")
    
    args = parser.parse_args()
    
    try:
        create_entity(args.path, args.name, args.type, args.relations, args.reason)
    except Exception as e:
        print(f"[ERROR] 创建失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
