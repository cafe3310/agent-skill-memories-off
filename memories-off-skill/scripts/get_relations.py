#!/usr/bin/env python3
import argparse
import sys
import re
from pathlib import Path
from schema_define import LibraryContext, MetadataParser

def get_related_entities(path: str, entity_name: str, relation_type: str = None):
    """
    查询与特定实体相连的所有其他实体。
    """
    root = Path(path).resolve()
    ctx = LibraryContext(root, "Target Library")
    
    target_file = ctx.entities_path / f"{entity_name}.md"
    if not target_file.exists():
        print(f"[ERROR] 实体不存在: {target_file}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] 正在查询实体 [{entity_name}] 的关联网络...")
    
    relations = [] # 存储格式: {"type": "", "target": "", "direction": ""}

    # 1. 扫描出向关系 (Outgoing: 当前实体指向别人)
    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()
        metadata = MetadataParser.parse(content)
        for key, val in metadata.items():
            if key.startswith("relation as"):
                predicate = key.replace("relation as", "").strip()
                # 处理逗号分隔的目标
                targets = [t.strip() for t in val.split(",")]
                for t in targets:
                    if not relation_type or relation_type.lower() in predicate.lower():
                        relations.append({"type": predicate, "entity": t, "direction": "outgoing"})

    # 2. 扫描入向关系 (Incoming: 别人指向当前实体)
    all_entity_files = list(ctx.entities_path.glob("*.md"))
    for file in all_entity_files:
        if file.name == f"{entity_name}.md": continue
        
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                metadata = MetadataParser.parse(content)
                for key, val in metadata.items():
                    if key.startswith("relation as"):
                        predicate = key.replace("relation as", "").strip()
                        targets = [t.strip() for t in val.split(",")]
                        if entity_name in targets:
                            if not relation_type or relation_type.lower() in predicate.lower():
                                relations.append({"type": predicate, "entity": file.stem, "direction": "incoming"})
        except Exception:
            continue

    # 3. 输出报告
    print("\n" + "="*40)
    print(f"  关联分析报告: {entity_name}")
    print("="*40)
    
    if not relations:
        print("  (未发现任何显式语义关系)")
    else:
        for rel in relations:
            dir_icon = "→" if rel["direction"] == "outgoing" else "←"
            print(f"  [{rel['type']}] {dir_icon} {rel['entity']}")
    
    print("="*40)

    # XML 报告
    print(f"\n<relations_report entity=\"{entity_name}\">")
    for rel in relations:
        print(f"  <relation type=\"{rel['type']}\" target=\"{rel['entity']}\" direction=\"{rel['direction']}\" />")
    print("</relations_report>")

def main():
    parser = argparse.ArgumentParser(
        description="分析实体的关联网络，列出所有指向和被指向的关系。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
用法示例:
  python get_relations.py --path . --entity 人物-四盘
  python get_relations.py -p ./kb -e 宠物-咪咪 --type 消耗
        """
    )
    parser.add_argument("-p", "--path", required=True, help="知识库根目录。")
    parser.add_argument("-e", "--entity", required=True, help="要查询的实体名称（不含 .md）。")
    parser.add_argument("-t", "--type", help="按关系类型过滤（模糊匹配）。")
    
    args = parser.parse_args()
    
    try:
        get_related_entities(args.path, args.entity, args.type)
    except Exception as e:
        print(f"[ERROR] 查询失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
