#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from collections import Counter
from schema_define import ScriptBase, MetadataParser

class InspectSchemaScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="inspect_schema",
            description="分析知识库的事实 Schema（通过扫描实体元数据提取实际存在的类型和键名）。",
            example="memocli inspect-schema --path ."
        )

    def run(self):
        self.setup()
        ctx = self.ctx
        
        self.add_result(f"正在分析知识库资产: {ctx.root_path}")
        
        # 1. 报告手册状态 (仅基本信息)
        if ctx.meta_path.exists():
            size = os.path.getsize(ctx.meta_path)
            self.add_result(f"[手册] meta.md 已存在 ({size} bytes)")
        else:
            self.add_result("[手册] 未找到 meta.md (建议运行 init 或手动创建)")

        # 2. 事实 Schema 提取 (Fact-based Discovery)
        if ctx.entities_path.exists():
            entity_files = list(ctx.entities_path.glob("*.md"))
            if entity_files:
                self.add_result(f"\n正在扫描 {len(entity_files)} 个实体以提取 Schema...")
                
                found_types = Counter()
                all_keys = Counter()
                relation_types = Counter()

                # 为了性能，如果实体过多则采样，否则全量
                sample_size = 100
                files_to_scan = entity_files[:sample_size]
                
                for file in files_to_scan:
                    try:
                        with open(file, "r", encoding="utf-8") as f:
                            metadata = MetadataParser.parse(f.read())
                            
                            # 统计实体类型
                            e_type = metadata.get("entity type", "未分类")
                            found_types[e_type] += 1
                            
                            # 统计元数据键
                            for k in metadata.keys():
                                all_keys[k] += 1
                                # 特别提取关系类型
                                if "relation as " in k:
                                    rel_name = k.split("relation as ")[1]
                                    relation_types[rel_name] += 1
                    except:
                        continue

                # 3. 构造报告
                self.add_result(f"\n[实际存在的实体类型] (采样自 {len(files_to_scan)} 个文件)")
                for t, count in found_types.most_common():
                    self.add_result(f"  - {t} ({count})")

                self.add_result("\n[已使用的元数据键名]")
                for k, count in sorted(all_keys.items()):
                    if "relation as " not in k:
                        self.add_result(f"  - {k} ({count})")

                self.add_result("\n[发现的关系契约] (Explicit Relations)")
                if relation_types:
                    for r, count in sorted(relation_types.items()):
                        self.add_result(f"  - {r} ({count})")
                else:
                    self.add_result("  (未发现显式关系定义)")
            else:
                self.add_result("\n[实体] 目录为空，无法提取 Schema。")
        else:
            self.error("实体目录不存在。")

        self.finalize(success=True)

if __name__ == "__main__":
    InspectSchemaScript().run()
