#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from schema_define import LibraryContext, MetadataParser

def inspect_schema(path: str, mode: str):
    """
    扫描库内所有实体，提取已使用的实体类型或元数据键名。
    """
    root = Path(path).resolve()
    ctx = LibraryContext(root, "Target Library")
    
    if not ctx.entities_path.exists():
        print(f"[ERROR] 实体目录不存在: {ctx.entities_path}", file=sys.stderr)
        sys.exit(1)

    entity_files = list(ctx.entities_path.glob("*.md"))
    
    unique_types = set()
    unique_keys = set()

    print(f"[*] 正在扫描 {len(entity_files)} 个实体以提取 Schema 信息...")

    for file in entity_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                metadata = MetadataParser.parse(content)
                
                # 记录类型
                if "entity type" in metadata:
                    unique_types.add(metadata["entity type"])
                
                # 记录所有键名
                for key in metadata.keys():
                    unique_keys.add(key)
        except Exception:
            continue

    if mode == "types" or mode == "all":
        print("\n[可用实体类型 (Entity Types)]")
        for t in sorted(unique_types):
            print(f"  - {t}")
            
    if mode == "keys" or mode == "all":
        print("\n[已使用的元数据键名 (Metadata Keys)]")
        for k in sorted(unique_keys):
            print(f"  - {k}")

    # XML 报告输出
    print(f"\n<schema_inspection_report path=\"{root}\">")
    if mode in ["types", "all"]:
        print("  <entity_types>")
        for t in sorted(unique_types):
            print(f"    <type>{t}</type>")
        print("  </entity_types>")
    if mode in ["keys", "all"]:
        print("  <metadata_keys>")
        for k in sorted(unique_keys):
            print(f"    <key>{k}</key>")
        print("  </metadata_keys>")
    print("</schema_inspection_report>")

def main():
    if "--memo-cli-info" in sys.argv:
        print("Description: 检查并输出知识库的元数据 Schema 详情。")
        print("Example: memocli inspect-schema --path . --mode types")
        sys.exit(0)

    is_memo_cli = "--memo-cli-call" in sys.argv
    action_name = Path(__file__).stem.replace("_", "-")

    parser = argparse.ArgumentParser(
        prog=f"memocli {action_name}" if is_memo_cli else None,
        description="扫描知识库资产，获取已定义的实体类型和元数据键名枚举。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"用法示例:\n  {'memocli ' + action_name if is_memo_cli else 'python3 ' + Path(__file__).name} --path . --mode types\n  {'memocli ' + action_name if is_memo_cli else 'python3 ' + Path(__file__).name} -p ./kb -m keys\n  {'memocli ' + action_name if is_memo_cli else 'python3 ' + Path(__file__).name} -p ./kb -m all"
    )
    parser.add_argument("--memo-cli-call", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-p", "--path", required=True, help="知识库根目录。")
    parser.add_argument("-m", "--mode", choices=["types", "keys", "all"], default="all",
                        help="检查模式：types (类型), keys (键名), all (全部)。")
    
    args = parser.parse_args()
    
    try:
        inspect_schema(args.path, args.mode)
    except Exception as e:
        print(f"[ERROR] 检查失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
