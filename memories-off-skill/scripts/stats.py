#!/usr/bin/env python3
import argparse
import sys
import os
from collections import Counter
from pathlib import Path
from schema_define import LibraryContext, MetadataParser

def get_stats(path: str, limit_commits: int = 5):
    """
    获取知识库的概要统计信息。
    """
    root = Path(path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"路径不存在: {root}")
    
    ctx = LibraryContext(root, "Target Library")
    
    print(f"[*] 正在分析知识库: {root}")
    
    # 1. 统计实体文件
    if not ctx.entities_path.exists():
        print(f"[WARN] 实体目录不存在: {ctx.entities_path}")
        entity_files = []
    else:
        entity_files = list(ctx.entities_path.glob("*.md"))
    
    # 2. 解析元数据分布
    type_counts = Counter()
    for file in entity_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                metadata = MetadataParser.parse(content)
                e_type = metadata.get("entity type", "未分类")
                type_counts[e_type] += 1
        except Exception as e:
            print(f"[!] 无法解析文件 {file.name}: {e}")

    # 3. 读取近期 Git 动态
    commits = "无 Git 记录"
    if ctx.is_git_repo():
        commits = ctx.run_git(["log", f"-n {limit_commits}", "--pretty=format:%h | %as | %s"])

    # 4. 生成报告
    print("\n" + "="*40)
    print(f"  Memories-Off 知识库概要报告")
    print("="*40)
    print(f"总计实体数: {len(entity_files)}")
    print("\n[实体类型分布]")
    for t, count in type_counts.most_common():
        print(f"  - {t}: {count}")
    
    print(f"\n[最近 {limit_commits} 条变更记录]")
    print(commits if commits else "  (暂无提交记录)")
    print("="*40)
    
    # 同时也返回一个精简的 XML 块供 Agent 直接解析
    print(f"\n<library_report total_entities=\"{len(entity_files)}\">")
    print("  <types>")
    for t, count in type_counts.items():
        print(f"    <type name=\"{t}\" count=\"{count}\" />")
    print("  </types>")
    print("</library_report>")

def main():
    parser = argparse.ArgumentParser(
        description="获取 memories-off 知识库的全局资产统计报告。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
用法示例:
  python stats.py --path /path/to/library
  python stats.py -p ./my_kb --commits 10
        """
    )
    parser.add_argument("-p", "--path", required=True, help="知识库的根目录路径。")
    parser.add_argument("-c", "--commits", type=int, default=5, help="显示最近的 Git 提交记录数量 (默认: 5)。")
    
    args = parser.parse_args()
    
    try:
        get_stats(args.path, args.commits)
    except Exception as e:
        print(f"[ERROR] 统计失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
