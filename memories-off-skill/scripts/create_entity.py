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
    """
    root = Path(path).resolve()
    ctx = LibraryContext(root, "Target Library")
    
    # 1. 标准化名称与路径
    normalized_name = MetadataParser.normalize_name(name)
    file_path = ctx.entities_path / f"{normalized_name}.md"
    
    if file_path.exists():
        print(f"[ERROR] 实体已存在: {file_path}", file=sys.stderr)
        sys.exit(1)

    # 2. 准备元数据
    today = datetime.now().strftime("%Y-%m-%d")
    
    frontmatter = [
        "---",
        f"entity type: {entity_type}",
        f"date created: {today}",
        f"date modified: {today}",
        "status: draft"
    ]
    
    # 解析并添加关系 (格式示例: "成员: 某组织, 负责: 某项目")
    if relations:
        rel_list = [r.strip() for t in relations.split(",") for r in [t.strip()]]
        for rel in rel_list:
            if ":" in rel:
                frontmatter.append(f"relation as {rel}")

    frontmatter.append("---\n")
    
    # 3. 构造初始正文
    body = f"# {name}\n\n(在此输入实体描述)"
    
    content = "\n".join(frontmatter) + body
    
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

    # XML 报告
    print(f"\n<create_report name=\"{normalized_name}\" path=\"{file_path}\">")
    print(f"  <status>success</status>")
    print("</create_report>")

def main():
    parser = argparse.ArgumentParser(
        description="自动化创建符合规范的知识实体，包含元数据注入与自动提交。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
用法示例:
  python create_entity.py --path . --name "张三" --type "人物" --relations "成员: 某团队" --reason "新增联系人"
        """
    )
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
