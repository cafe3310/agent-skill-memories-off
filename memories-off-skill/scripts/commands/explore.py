#!/usr/bin/env python3
import sys
import os
import re
import subprocess
from pathlib import Path
from collections import Counter
from utility.runtime import ScriptBase
from utility.schema_define import MetadataParser

class ExploreScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="explore",
            description="知识库全景探索工具。获取核心指南、关键实体、全局分类统计与工具帮助，适合在任务初期快速建立上下文。",
            example="memocli explore --path . [--full]"
        )
        self.parser.add_argument("--full", action="store_true", help="输出完整内容，不截断任何超过默认限制的信息。")

    def run(self):
        self.setup()
        ctx = self.ctx
        
        self.add_result(f"============== MEMORIES-OFF 知识库导览 ==============\n")
        
        # 1. 知识库 meta.md 绝对路径
        abs_meta_path = ctx.meta_path.absolute()
        self.add_result(f"【 1. 核心指南路径 】\n{abs_meta_path}\n")
        
        # 预备变量
        meta_content = ""
        wikilinks_names = []
        
        # 2. meta.md 全文
        if ctx.meta_path.exists():
            try:
                with open(ctx.meta_path, "r", encoding="utf-8") as f:
                    meta_content = f.read()
                
                self.add_result(f"【 2. meta.md 内容 】")
                lines = meta_content.splitlines()
                limit = 500
                if not self.args.full and len(lines) > limit:
                    for line in lines[:limit]:
                        self.add_result(line)
                    self.add_result(f"\n... (已截断，手册总计 {len(lines)} 行。请使用 '--full' 参数查看全文。)\n")
                else:
                    for line in lines:
                        self.add_result(line)
                    self.add_result("") # 空行分隔

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
                self.add_result(f"【 2. meta.md 内容 】\n[读取失败] {e}\n")
        else:
            self.add_result(f"【 2. meta.md 内容 】\n[不存在] 知识库尚未初始化标准手册 (meta.md)。\n")

        # 3. meta.md 中提及实体的 Frontmatter
        self.add_result(f"【 3. 核心实体导览 (出自 meta.md 提及) 】")
        if not wikilinks_names:
            self.add_result("手册中未发现提及的具体实体链接。\n")
        else:
            limit_entities = 20
            display_names = wikilinks_names if self.args.full else wikilinks_names[:limit_entities]
            
            found_any = False
            for name in display_names:
                entity_file = ctx.entities_path / f"{name}.md"
                if entity_file.exists():
                    try:
                        with open(entity_file, "r", encoding="utf-8") as f:
                            content = f.read()
                        meta_dict, _ = MetadataParser.split_content(content)
                        yaml_str = MetadataParser.serialize(meta_dict)
                        self.add_result(f"--- 实体: {name} ---")
                        self.add_result(yaml_str.strip())
                        found_any = True
                    except Exception:
                        pass
                        
            if not found_any:
                self.add_result("提及的实体暂未创建或无法读取。")
            if not self.args.full and len(wikilinks_names) > limit_entities:
                self.add_result(f"\n... (已截断，共发现 {len(wikilinks_names)} 个核心实体。请使用 '--full' 参数查看全量)。\n")
            else:
                self.add_result("")

        # 4 & 5. 全库类型与关系统计
        self.add_result(f"【 4. 全局实体类型分布 】")
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
                    
            # 渲染类型
            limit_stats = 200
            type_list = found_types.most_common()
            display_types = type_list if self.args.full else type_list[:limit_stats]
            for t, count in display_types:
                self.add_result(f"  - {t} ({count} 个实体)")
            if not self.args.full and len(type_list) > limit_stats:
                self.add_result(f"  ... (共 {len(type_list)} 种类型，已截断)")
            if not type_list:
                self.add_result("  (空)")

            self.add_result(f"\n【 5. 全局关系分布 】")
            rel_list = relation_types.most_common()
            display_rels = rel_list if self.args.full else rel_list[:limit_stats]
            for r, count in display_rels:
                self.add_result(f"  - {r} (在 {count} 个实体中被声明出站)")
            if not self.args.full and len(rel_list) > limit_stats:
                self.add_result(f"  ... (共 {len(rel_list)} 种关系，已截断)")
            if not rel_list:
                self.add_result("  (未发现显式关系)")
        else:
            self.add_result("  [错误] 实体目录不存在。")

        self.add_result("")
        
        # 6. CLI Help
        self.add_result(f"【 6. 可用工具指令速查 (memocli --help) 】")
        try:
            # 内部调用 memocli help 以捕获完整 Bash 包装器的输出
            result = subprocess.run(["memocli", "help"], capture_output=True, text=True, check=True)
            self.add_result(result.stdout.strip())
        except Exception as e:
            self.add_result(f"无法直接加载 memocli 帮助信息: {e}\n(请在终端单独运行 memocli help 查看)")

        self.finalize(success=True)

if __name__ == "__main__":
    ExploreScript().run()
