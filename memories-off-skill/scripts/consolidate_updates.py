#!/usr/bin/env python3
import argparse
import sys
import re
from pathlib import Path
from datetime import datetime
from schema_define import LibraryContext, MetadataParser
import subprocess

# 正则：提取更新块
BLOCK_RE = re.compile(
    r"--- \[UPDATE BLOCK\] ---\n"
    r"timestamp: (.*?)\n"
    r"target_heading: \"(.*?)\"\n"
    r"action: \"(.*?)\"\n"
    r"content: \|\n"
    r"(.*?)\n"
    r"--- \[END OF UPDATE BLOCK\] ---",
    re.DOTALL
)

def consolidate_entity(file_path: Path):
    """
    解析并合并单个实体的所有更新块。
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = list(BLOCK_RE.finditer(content))
    if not blocks:
        return False

    # 1. 提取元数据和纯正文（不含更新块）
    metadata, full_body = MetadataParser.split_content(content)
    # 移除所有更新块标记，得到原始正文
    clean_body = BLOCK_RE.sub("", full_body).strip()
    
    new_body = clean_body
    
    for match in blocks:
        _, target_heading, action, block_content = match.groups()
        # 去掉 block_content 每行前面的 2 个空格缩进
        lines = [line[2:] if line.startswith("  ") else line for line in block_content.splitlines()]
        refined_content = "\n".join(lines).strip()
        
        if action == "new_section":
            new_body += f"\n\n{refined_content}"
        elif action == "append":
            if target_heading in new_body:
                # 在目标标题后追加
                pattern = re.escape(target_heading)
                # 寻找目标标题到下一个同级或更高级标题之间的内容
                # 此处简化逻辑：寻找标题后到下一个标题或文件尾
                new_body = re.sub(f"({pattern}.*?)(\n#|$)", f"\\1\n\n{refined_content}\\2", new_body, flags=re.DOTALL)
            else:
                # 找不到标题，退化为追加到末尾
                new_body += f"\n\n{refined_content}"
        elif action == "replace":
            if target_heading in new_body:
                # 替换目标标题下的内容
                pattern = re.escape(target_heading)
                new_body = re.sub(f"({pattern}).*?(\n#|$)", f"\\1\n\n{refined_content}\\2", new_body, flags=re.DOTALL)
            else:
                new_body += f"\n\n{refined_content}"

    # 2. 更新元数据
    metadata["date modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 3. 合并写回
    final_content = MetadataParser.serialize(metadata) + "\n" + new_body.strip() + "\n"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_content)
    
    return True

def consolidate_all(path: str, reason: str):
    """
    遍历全库执行整理任务。
    """
    root = Path(path).resolve()
    ctx = LibraryContext(root, "Target Library")
    
    print(f"[*] 开始执行梦境整理 (Consolidation)...")
    
    entity_files = list(ctx.entities_path.glob("*.md"))
    affected_files = []

    for file in entity_files:
        if consolidate_entity(file):
            affected_files.append(file.stem)
            ctx.run_git(["add", str(file)])
            print(f"[+] 已合并实体: {file.stem}")

    if not affected_files:
        print("[INFO] 没有待处理的更新块。")
        return

    # 调用 commit.py
    commit_script = Path(__file__).parent / "commit.py"
    try:
        subprocess.run([
            sys.executable, str(commit_script),
            "--path", str(root),
            "--action", "edit",
            "--target", "Global",
            "--reason", f"Consolidate updates for {len(affected_files)} entities: {reason}"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[WARN] 整理已完成但自动提交失败: {e}")

    print(f"\n[SUCCESS] 梦境整理圆满完成！共处理 {len(affected_files)} 个实体。")

def main():
    parser = argparse.ArgumentParser(
        description="解析并合并所有实体的缓冲更新块，完成‘梦境整理’。",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-p", "--path", required=True, help="知识库根目录。")
    parser.add_argument("-r", "--reason", default="定期梦境整理", help="操作原因。")
    
    args = parser.parse_args()
    
    try:
        consolidate_all(args.path, args.reason)
    except Exception as e:
        print(f"[ERROR] 梦境整理失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
