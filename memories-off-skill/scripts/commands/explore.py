#!/usr/bin/env python3
import sys
import os
import re
import subprocess
from pathlib import Path
from collections import Counter
from utility.runtime import ScriptBase
from utility.schema_define import MetadataParser

def escape_text(text):
    if not text: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

class ExploreScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="explore",
            description="知识库全景探索工具。获取核心指南、关键实体、全局分类统计与工具帮助，适合在任务初期快速建立上下文。",
            group_name="核心探索 (Core Exploration)",
            example="memocli explore --path . [--full]"
        )
        self.parser.add_argument("--full", action="store_true", help="输出完整内容，不截断任何超过默认限制的信息。")
        self.explore_xml = ""

    def run(self):
        self.setup()
        ctx = self.ctx
        
        xml_parts = []
        xml_parts.append("<explore-data>")
        
        # 1. 知识库 meta.md 绝对路径
        abs_meta_path = ctx.meta_path.absolute()
        xml_parts.append(f"  <meta-path>{escape_text(str(abs_meta_path))}</meta-path>")
        
        # 预备变量
        meta_content = ""
        wikilinks_names = []
        
        # 2. meta.md 全文
        if ctx.meta_path.exists():
            try:
                with open(ctx.meta_path, "r", encoding="utf-8") as f:
                    meta_content = f.read()
                
                lines = meta_content.splitlines()
                limit = 500
                if not self.args.full and len(lines) > limit:
                    display_content = "\n".join(lines[:limit]) + f"\n\n... (已截断，手册总计 {len(lines)} 行。请使用 '--full' 参数查看全文。)"
                else:
                    display_content = meta_content

                xml_parts.append(f"  <meta-content>{escape_text(display_content)}</meta-content>")

                # 提取 WikiLinks 备用
                wikilink_pattern = re.compile(r"\[\[(.*?)\]\]")
                links = wikilink_pattern.findall(meta_content)
                
                # 去重并统一标准化
                seen = set()
                for link in links:
                    name_raw = link.split("|")[0].strip()
                    norm_name = MetadataParser.normalize_name(name_raw)
                    if norm_name and norm_name not in seen:
                        seen.add(norm_name)
                        wikilinks_names.append(norm_name)
            except Exception as e:
                xml_parts.append(f"  <meta-content error=\"读取失败: {escape_text(str(e))}\" />")
        else:
            xml_parts.append("  <meta-content error=\"不存在: 知识库尚未初始化标准手册 (meta.md)\" />")

        # 3. meta.md 中提及实体的 Frontmatter
        xml_parts.append("  <core-entities>")
        if wikilinks_names:
            limit_entities = 20
            display_names = wikilinks_names if self.args.full else wikilinks_names[:limit_entities]
            
            for name in display_names:
                entity_file = ctx.entities_path / f"{name}.md"
                if entity_file.exists():
                    try:
                        with open(entity_file, "r", encoding="utf-8") as f:
                            content = f.read()
                        meta_dict, _ = MetadataParser.split_content(content)
                        yaml_str = MetadataParser.serialize(meta_dict)
                        xml_parts.append(f'    <entity name="{escape_text(name)}">')
                        xml_parts.append(f'      <frontmatter>{escape_text(yaml_str.strip())}</frontmatter>')
                        xml_parts.append(f'    </entity>')
                    except Exception:
                        pass
                        
            if not self.args.full and len(wikilinks_names) > limit_entities:
                xml_parts.append(f'    <truncated total="{len(wikilinks_names)}" limit="{limit_entities}" />')
        xml_parts.append("  </core-entities>")

        # 4 & 5. 全库类型与关系统计
        found_types = Counter()
        relation_types = Counter()
        
        if ctx.entities_path.exists():
            entity_files = list(ctx.entities_path.glob("*.md"))
            for file in entity_files:
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        # 只取前100行足够解析元数据了，提升性能
                        head_content = "".join([f.readline() for _ in range(100)])
                        metadata, _ = MetadataParser.split_content(head_content)
                        
                        e_type = metadata.get("entity type", "未分类")
                        found_types[e_type] += 1
                        
                        for k in metadata.keys():
                            if "relation as " in k:
                                rel_name = k.split("relation as ")[1].strip()
                                relation_types[rel_name] += 1
                except:
                    continue
                    
            limit_stats = 200
            
            # --- 4. 类型分布 (简化层级) ---
            type_list = found_types.most_common()
            display_types = type_list if self.args.full else type_list[:limit_stats]
            
            type_lines = ["全局实体类型列表:"]
            for t, count in display_types:
                type_lines.append(f'  - "{t}" ({count} 个实体)')
            if not self.args.full and len(type_list) > limit_stats:
                type_lines.append(f'  ... (共 {len(type_list)} 种类型，已截断)')
            
            xml_parts.append(f"  <global-entity-types>\n{escape_text(chr(10).join(type_lines))}\n  </global-entity-types>")

            # --- 5. 关系分布 (简化层级) ---
            rel_list = relation_types.most_common()
            display_rels = rel_list if self.args.full else rel_list[:limit_stats]
            
            rel_lines = ["全局关系分布列表:"]
            for r, count in display_rels:
                rel_lines.append(f'  - "{r}" ({count} 个实体有出站声明)')
            if not self.args.full and len(rel_list) > limit_stats:
                rel_lines.append(f'  ... (共 {len(rel_list)} 种关系，已截断)')

            xml_parts.append(f"  <global-relations>\n{escape_text(chr(10).join(rel_lines))}\n  </global-relations>")
        else:
            xml_parts.append('  <global-entity-types>实体目录不存在</global-entity-types>')
            xml_parts.append('  <global-relations>实体目录不存在</global-relations>')

        # 6. CLI Help
        try:
            result = subprocess.run(["memocli", "help"], capture_output=True, text=True, check=True)
            xml_parts.append(f"  <cli-help>{escape_text(result.stdout.strip())}</cli-help>")
        except Exception as e:
            xml_parts.append(f'  <cli-help error="读取失败: {escape_text(str(e))}" />')

        xml_parts.append("</explore-data>")
        self.explore_xml = "\n".join(xml_parts)
        
        self.finalize(success=True)

    def finalize(self, success: bool = True, error_msg: str = None, instruction: str = ""):
        """重写 finalize 以直接输出结构化 XML 而不是逐行转义的文本。"""
        status = "success" if success else "failed"
        reason = getattr(self.args, "reason", "none") if self.args else "none"
        subcommand = self.action_name.replace("_", "-")
        
        full_cmd = " ".join(sys.argv)
        if "memocli" not in full_cmd and self.is_memo_cli:
             full_cmd = f"memocli {subcommand} " + " ".join([a for a in sys.argv[1:] if a != "--memo-cli-call"])

        print(f'<memocli-result subcommand="{subcommand}" reason="{reason}" result="{status}">')
        print(f"  <source-sh>{full_cmd}</source-sh>")
        
        if not success:
            print("  <error-detail>")
            if error_msg:
                print(f"    原因: {error_msg}")
            if instruction:
                print(f"    指令: {instruction}")
            print("  </error-detail>")
        else:
            print("  <content>")
            print(self.explore_xml)
            print("  </content>")
            
        print("</memocli-result>")

if __name__ == "__main__":
    ExploreScript().run()
