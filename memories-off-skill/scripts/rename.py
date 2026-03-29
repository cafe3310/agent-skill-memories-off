#!/usr/bin/env python3
import argparse
import sys
import re
from pathlib import Path
from schema_define import LibraryContext, MetadataParser

def rename_entity(path: str, old_name: str, new_name: str, reason: str):
    """
    安全重命名实体，并自动更新全局引用。
    """
    root = Path(path).resolve()
    ctx = LibraryContext(root, "Target Library")
    
    # 标准化新名称
    new_name = MetadataParser.normalize_name(new_name)
    
    old_file = ctx.entities_path / f"{old_name}.md"
    new_file = ctx.entities_path / f"{new_name}.md"
    
    if not old_file.exists():
        print(f"[ERROR] 源文件不存在: {old_file}", file=sys.stderr)
        sys.exit(1)
    if new_file.exists():
        print(f"[ERROR] 目标文件已存在: {new_file}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] 正在重命名实体: {old_name} -> {new_name}")

    # 1. 执行 Git MV
    ctx.run_git(["mv", str(old_file), str(new_file)])
    
    # 2. 全局搜索并替换引用
    # 匹配规则: 
    #   - [[old_name]]
    #   - relation as [谓词]: ..., old_name, ...
    
    # WikiLink 正则
    wikilink_pattern = re.compile(re.escape(f"[[{old_name}]]"))
    # Relation 正则 (处理逗号分隔)
    relation_pattern = re.compile(rf"(relation as .*?:\s*)(.*)")

    affected_files = []
    
    # 扫描所有 .md 文件 (entities + meta.md)
    files_to_scan = list(ctx.entities_path.glob("*.md")) + [ctx.meta_path]
    
    for md_file in files_to_scan:
        if not md_file.exists(): continue
        
        with open(md_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        changed = False
        new_lines = []
        for line in lines:
            # 替换 WikiLinks
            if f"[[{old_name}]]" in line:
                line = wikilink_pattern.sub(f"[[{new_name}]]", line)
                changed = True
            
            # 替换 Relation as (仅在元数据区或 Frontmatter 可能出现)
            if "relation as" in line:
                match = relation_pattern.match(line)
                if match:
                    prefix, targets = match.groups()
                    # 拆分目标，精准替换
                    target_list = [t.strip() for t in targets.split(",")]
                    if old_name in target_list:
                        new_target_list = [new_name if t == old_name else t for t in target_list]
                        line = f"{prefix}{', '.join(new_target_list)}\n"
                        changed = True
            
            new_lines.append(line)
        
        if changed:
            with open(md_file, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            ctx.run_git(["add", str(md_file)])
            affected_files.append(md_file.name)

    # 3. 提交变更
    commit_msg = f"rename {old_name} -> {new_name}: {reason}"
    ctx.run_git(["commit", "-m", commit_msg])
    
    print(f"\n[SUCCESS] 重命名成功！")
    print(f"受影响的引用文件: {', '.join(affected_files) if affected_files else '无'}")
    
    # 返回报告
    print(f"\n<rename_report old=\"{old_name}\" new=\"{new_name}\" affected_count=\"{len(affected_files)}\">")
    for f in affected_files:
        print(f"  <file>{f}</file>")
    print("</rename_report>")

def main():
    parser = argparse.ArgumentParser(
        description="安全重命名实体文件，并自动同步更新库内所有 WikiLinks 和语义关系。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
用法示例:
  python rename.py --path . --old 人物-张三 --new 人物-张小三 --reason "修正姓名"
        """
    )
    parser.add_argument("-p", "--path", required=True, help="知识库根目录。")
    parser.add_argument("--old", required=True, help="原实体名称（不含 .md）。")
    parser.add_argument("--new", required=True, help="新实体名称（不含 .md）。")
    parser.add_argument("-r", "--reason", required=True, help="重命名原因。")
    
    args = parser.parse_args()
    
    try:
        rename_entity(args.path, args.old, args.new, args.reason)
    except Exception as e:
        print(f"[ERROR] 重命名失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
