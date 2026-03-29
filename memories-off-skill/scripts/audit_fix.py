#!/usr/bin/env python3
import argparse
import sys
import re
from pathlib import Path
from schema_define import LibraryContext, MetadataParser
import subprocess

def audit_library(path: str, fix: bool, reason: str):
    """
    审计知识库的一致性，发现并可选修复问题。
    """
    root = Path(path).resolve()
    ctx = LibraryContext(root, "Target Library")
    
    if not ctx.entities_path.exists():
        print(f"[ERROR] 实体目录不存在", file=sys.stderr)
        sys.exit(1)

    entity_files = list(ctx.entities_path.glob("*.md"))
    entity_names = {f.stem for f in entity_files}
    
    issues = [] # 格式: (file_path, line_no, type, detail)
    
    print(f"[*] 正在对 {len(entity_files)} 个实体进行健康检查...")

    # 预编译正则
    wikilink_pattern = re.compile(r"\[\[(.*?)\]\]")
    relation_pattern = re.compile(r"relation as (.*?):\s*(.*)")

    for file_path in entity_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            continue
        
        new_lines = []
        file_changed = False
        
        for idx, line in enumerate(lines):
            original_line = line
            line_no = idx + 1
            
            # 1. 审计 Relation 引用
            rel_match = relation_pattern.search(line)
            if rel_match:
                predicate, targets = rel_match.groups()
                target_list = [t.strip() for t in targets.split(",")]
                valid_targets = []
                for t in target_list:
                    if t not in entity_names:
                        issues.append((file_path.name, line_no, "Orphan Relation", f"指向不存在的实体: {t}"))
                    else:
                        valid_targets.append(t)
                
                if fix and len(valid_targets) != len(target_list):
                    if not valid_targets:
                        line = "" # 移除整行
                    else:
                        line = f"relation as {predicate}: {', '.join(valid_targets)}\n"
                    file_changed = True

            # 2. 审计 WikiLinks
            links = wikilink_pattern.findall(line)
            for link in links:
                if link not in entity_names:
                    issues.append((file_path.name, line_no, "Broken Link", f"无效的 WikiLink: [[{link}]]"))
                    if fix:
                        line = line.replace(f"[[{link}]]", f"[[{link}]] (broken)")
                        file_changed = True

            new_lines.append(line)

        # 3. 审计 Entity Type (单一值校验)
        for line in lines[:10]: # 仅在头部的 Frontmatter 检查
            if "entity type:" in line and "," in line:
                issues.append((file_path.name, "FM", "Schema Violation", "entity type 包含多个值（应为唯一）"))

        if fix and file_changed:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            ctx.run_git(["add", str(file_path)])

    # 输出审计报告
    print("\n" + "="*50)
    print(f"  知识库审计报告: {root.name}")
    print("="*50)
    
    if not issues:
        print("  [OK] 未发现引用或规范问题。")
    else:
        for file, line, kind, detail in issues:
            print(f"  [{kind}] {file}:{line} -> {detail}")
    
    print("="*50)

    # 如果执行了修复，调用 commit
    if fix and issues:
        commit_script = Path(__file__).parent / "commit.py"
        try:
            subprocess.run([
                sys.executable, str(commit_script),
                "--path", str(root),
                "--action", "fix",
                "--target", "Global",
                "--reason", reason if reason else "自动修复孤儿引用与失效链接"
            ], check=True)
            print("\n[SUCCESS] 修复已完成并提交。")
        except:
            print("\n[WARN] 修复已执行，但自动提交失败。")

    # XML 报告
    print(f"\n<audit_report issues_found=\"{len(issues)}\" fixed=\"{fix}\">")
    for file, line, kind, detail in issues:
        print(f"  <issue type=\"{kind}\" file=\"{file}\" line=\"{line}\">{detail}</issue>")
    print("</audit_report>")

def main():
    parser = argparse.ArgumentParser(
        description="全量审计知识库引用的一致性，发现孤儿关系、失效链接及元数据违规。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
用法示例:
  python audit_fix.py --path .
  python audit_fix.py --path ./kb --fix --reason "清理无效引用"
        """
    )
    parser.add_argument("-p", "--path", required=True, help="知识库根目录。")
    parser.add_argument("--fix", action="store_true", help="启用修复模式，自动更正发现的问题。")
    parser.add_argument("-r", "--reason", help="修复时的提交原因（仅在 --fix 时有效）。")
    
    args = parser.parse_args()
    
    try:
        audit_library(args.path, args.fix, args.reason)
    except Exception as e:
        print(f"[ERROR] 审计过程出错: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
