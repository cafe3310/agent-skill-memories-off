#!/usr/bin/env python3
import argparse
import sys
import os
import subprocess
import re
import shlex
from pathlib import Path

def run_command(cmd):
    """
    运行 shell 命令并返回输出。
    """
    try:
        # 使用 shell=True 需要非常小心路径中的空格，必须正确转义
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def search_entities(path: str, pattern: str, scope: str = "content", names_only: bool = False, context: int = 0):
    root = Path(path).resolve()
    entities_dir = root / "entities"
    
    if not entities_dir.exists():
        print(f"[ERROR] 实体目录不存在: {entities_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] 正在搜索模式 '{pattern}' (范围: {scope}, 默认忽略大小写)...")
    
    results = []
    
    # 路径安全转义
    safe_entities_dir = shlex.quote(str(entities_dir))
    safe_pattern = shlex.quote(pattern)
    
    # 1. 仅搜索实体名称 (Filename)
    if scope == "name":
        # 使用 ls | grep 逻辑
        cmd = f"ls {safe_entities_dir} | grep -iE {safe_pattern}"
        output = run_command(cmd)
        if output:
            results = output.splitlines()

    # 2. 搜索内容 (含 meta, all 逻辑)
    else:
        grep_flags = "-riE"
        if names_only:
            grep_flags += "l"
        elif context > 0:
            grep_flags += f" -C {context}"
        
        # 排除 meta.md
        cmd = f"grep {grep_flags} {safe_pattern} {safe_entities_dir} --exclude='meta.md'"
        output = run_command(cmd)
        if output:
            results = output.splitlines()

    # 3. 输出处理
    if not results:
        print(f"[!] 未找到匹配项: {pattern}")
        print("\n<search_results count=\"0\" />")
        return

    if names_only:
        # 只提取文件名
        clean_names = []
        for r in results:
            name = Path(r).name.replace(".md", "")
            if name not in clean_names:
                clean_names.append(name)
                print(name)
        
        print(f"\n<search_results count=\"{len(clean_names)}\">")
        for n in clean_names:
            print(f"  <match entity=\"{n}\" />")
        print("</search_results>")
    else:
        # 显示详细匹配
        current_entity = ""
        match_count = 0
        
        for line in results:
            # grep 输出格式: path/to/file:line_num:matched_text
            # 或者 path/to/file-line_num-context_text (如果有 -C)
            
            parts = re.split(r"[:\-]", line, 2)
            if len(parts) >= 2:
                file_path = parts[0]
                entity_name = Path(file_path).name.replace(".md", "")
                content = parts[2] if len(parts) > 2 else ""
                
                if entity_name != current_entity:
                    print(f"\n[+] 实体: {entity_name}")
                    current_entity = entity_name
                    match_count += 1
                
                print(f"    {line.replace(str(entities_dir)+'/', '')}")
        
        print(f"\n<search_results count=\"{match_count}\" />")

def main():
    if "--memo-cli-info" in sys.argv:
        print("Description: 在知识库中通过模式（正则表达式）检索实体。支持名称、元数据和正文搜索。")
        print("Example: memocli search \"五一\" --content --names-only")
        sys.exit(0)

    is_memo_cli = "--memo-cli-call" in sys.argv
    action_name = "search"

    parser = argparse.ArgumentParser(
        prog=f"memocli {action_name}" if is_memo_cli else None,
        description="检索 Memories-Off 知识库中的实体。",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--memo-cli-call", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-p", "--path", required=True, help="知识库的根目录路径。")
    parser.add_argument("pattern", help="要搜索的模式（支持正则表达式）。")
    
    # 搜索范围
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-n", "--name", action="store_true", help="仅搜索实体名称。")
    group.add_argument("-m", "--meta", action="store_true", help="仅搜索元数据 (Frontmatter)。")
    group.add_argument("-c", "--content", action="store_true", default=True, help="仅搜索正文内容 (默认)。")
    group.add_argument("-a", "--all", action="store_true", help="全方位全局搜索。")
    
    # 输出控制
    parser.add_argument("--names-only", action="store_true", help="仅输出匹配的实体名称列表。")
    parser.add_argument("-C", "--context", type=int, default=0, help="显示匹配行的上下文行数。")
    
    args = parser.parse_args()
    
    # 确定 scope
    scope = "content"
    if args.name: scope = "name"
    elif args.meta: scope = "meta"
    elif args.all: scope = "all"

    try:
        search_entities(args.path, args.pattern, scope, args.names_only, args.context)
    except Exception as e:
        print(f"[ERROR] 搜索失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
