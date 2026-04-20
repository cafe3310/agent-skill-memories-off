#!/usr/bin/env python3
import sys
from pathlib import Path
from utility.runtime import ScriptBase
from utility.schema_define import MetadataParser

class LoadScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="load",
            description="精确读取一系列实体的全文内容（含 YAML Frontmatter）。",
            example='memocli load --names "实体1,实体2"'
        )
        self.parser.add_argument("-n", "--names", required=True, help="要加载的实体名称列表，以逗号分隔。")

    def run(self):
        self.setup()
        ctx = self.ctx
        
        # 1. 解析名称列表
        names_raw = [n.strip() for n in self.args.names.split(",") if n.strip()]
        if not names_raw:
            self.error("未提供有效的实体名称。")

        # 2. 构建别名映射表 (仅在目录存在时)
        alias_map = {}
        if ctx.entities_path.exists():
            for file_path in ctx.entities_path.glob("*.md"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        # 仅读取头部足够解析 Frontmatter 的行数
                        head_content = "".join([f.readline() for _ in range(100)])
                    metadata, _ = MetadataParser.split_content(head_content)
                    aliases = MetadataParser.get_aliases(metadata)
                    for alias in aliases:
                        alias_lower = alias.strip().lower()
                        alias_norm = MetadataParser.normalize_name(alias)
                        alias_map[alias_lower] = file_path.stem
                        alias_map[alias_norm] = file_path.stem
                except Exception:
                    continue

        # 3. 逐一加载实体
        for name in names_raw:
            norm_name = MetadataParser.normalize_name(name)
            entity_file = ctx.entities_path / f"{norm_name}.md"
            
            actual_stem = norm_name
            found_via_alias = False
            
            # 如果直接规范化后的文件不存在，尝试别名回退
            if not entity_file.exists():
                name_lower = name.lower()
                if name_lower in alias_map:
                    actual_stem = alias_map[name_lower]
                    entity_file = ctx.entities_path / f"{actual_stem}.md"
                    found_via_alias = True
                elif norm_name in alias_map:
                    actual_stem = alias_map[norm_name]
                    entity_file = ctx.entities_path / f"{actual_stem}.md"
                    found_via_alias = True
            
            if not entity_file.exists():
                self.add_result(f"--- [加载失败: '{name}'] (规范化为 '{norm_name}'，且未匹配到别名) ---")
                continue
            
            try:
                with open(entity_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                if found_via_alias:
                    self.add_result(f"--- [实体: {actual_stem}] (经由别名 '{name}' 匹配) ---")
                else:
                    self.add_result(f"--- [实体: {actual_stem}] ---")
                    
                for line in content.splitlines():
                    self.add_result(line)
            except Exception as e:
                self.add_result(f"--- [加载失败: {actual_stem}] (错误: {e}) ---")

        self.finalize(success=True)

if __name__ == "__main__":
    LoadScript().run()
