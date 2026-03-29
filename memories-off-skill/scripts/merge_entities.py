#!/usr/bin/env python3
import argparse
import sys
import re
from pathlib import Path
from schema_define import LibraryContext, MetadataParser
import subprocess

def merge_entities(path: str, sources: list, target: str, reason: str):
    """
    将多个源实体合并到目标实体，同步更新全局引用并删除源文件。
    """
    root = Path(path).resolve()
    ctx = LibraryContext(root, "Target Library")
    
    target_file = ctx.entities_path / f"{target}.md"
    if not target_file.exists():
        print(f"[ERROR] 目标实体不存在: {target_file}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] 准备将 {len(sources)} 个实体合并至: {target}")

    # 1. 提取源实体内容并准备删除
    merged_content_blocks = ["\n\n--- 合并内容开始 ---"]
    valid_sources = []
    
    for src_name in sources:
        src_file = ctx.entities_path / f"{src_name}.md"
        if not src_file.exists():
            print(f"[WARN] 源实体 {src_name} 不存在，跳过。")
            continue
        
        with open(src_file, "r", encoding="utf-8") as f:
            content = f.read()
            # 剔除 Frontmatter
            body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL)
            merged_content_blocks.append(f"\n## 来自 {src_name} 的内容\n{body.strip()}")
            valid_sources.append(src_name)

    if not valid_sources:
        print("[ERROR] 没有有效的源实体可供合并。")
        sys.exit(1)

    # 2. 追加内容到目标实体
    with open(target_file, "a", encoding="utf-8") as f:
        f.write("\n".join(merged_content_blocks))
    print(f"[+] 内容已追加至 {target}.md")

    # 3. 全局重定向引用 (Source -> Target)
    print("[*] 正在更新全库引用...")
    all_md_files = list(ctx.entities_path.glob("*.md")) + [ctx.meta_path]
    
    for md_file in all_md_files:
        if not md_file.exists(): continue
        with open(md_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        changed = False
        new_lines = []
        for line in lines:
            # 批量替换 WikiLinks 和 Relations
            original_line = line
            for src in valid_sources:
                # WikiLink 替换
                line = line.replace(f"[[{src}]]", f"[[{target}]]")
                # Relation 替换 (简单字符串匹配)
                if "relation as" in line:
                    line = line.replace(f": {src}", f": {target}").replace(f", {src}", f", {target}")
            
            if line != original_line:
                changed = True
            new_lines.append(line)
            
        if changed:
            with open(md_file, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            ctx.run_git(["add", str(md_file)])

    # 4. 删除源文件
    for src in valid_sources:
        src_file = ctx.entities_path / f"{src}.md"
        ctx.run_git(["rm", str(src_file)])
    print(f"[+] 已删除源文件: {', '.join(valid_sources)}")

    # 5. 调用外部 commit.py 执行标准化提交
    commit_script = Path(__file__).parent / "commit.py"
    try:
        subprocess.run([
            sys.executable, str(commit_script),
            "--path", str(root),
            "--action", "rename",  # 合并视为一种特殊的重命名/迁移
            "--target", target,
            "--reason", f"Merge {', '.join(valid_sources)} into {target}: {reason}"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[WARN] 合并已完成但自动提交失败: {e}")

    print(f"\n[SUCCESS] 合并操作圆满完成！")

def main():
    if "--memo-cli-info" in sys.argv:
        print("Description: 将多个源实体内容合并到目标实体并清理源文件。")
        print("Example: memocli merge-entities --path . --sources 人物-张三,人物-李四 --target 人物-王五 --reason \"重复录入\"")
        sys.exit(0)

    is_memo_cli = "--memo-cli-call" in sys.argv
    action_name = Path(__file__).stem.replace("_", "-")

    parser = argparse.ArgumentParser(
        prog=f"memocli {action_name}" if is_memo_cli else None,
        description="将多个源实体的内容合并到目标实体，自动更新全库引用并删除源实体。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
用法示例:
  {'memocli ' + action_name if is_memo_cli else 'python3 ' + Path(__file__).name} --path . --sources 人物-张三,人物-李四 --target 人物-王五 --reason "重复录入"
        """
    )
    parser.add_argument("--memo-cli-call", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-p", "--path", required=True, help="知识库根目录。")
    parser.add_argument("-s", "--sources", required=True, help="源实体名称列表，逗号分隔。")
    parser.add_argument("-t", "--target", required=True, help="目标实体名称。")
    parser.add_argument("-r", "--reason", required=True, help="合并原因。")
    
    args = parser.parse_args()
    source_list = [s.strip() for s in args.sources.split(",")]
    
    try:
        merge_entities(args.path, source_list, args.target, args.reason)
    except Exception as e:
        print(f"[ERROR] 合并失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
