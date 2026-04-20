#!/usr/bin/env python3
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple
from utility.runtime import ScriptBase
from utility.schema_define import MetadataParser

class SearchScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="search_entities",
            description="在知识库中通过模式（正则表达式）检索实体。支持精准过滤（按类型、关系）和包含别名的全方位搜索。",
            group_name="检索与加载 (Search & Loading)",
            example='memocli search-entities "模式串" --name --type "人物" --rel "friend:张三"'
        )
        self.parser.add_argument("pattern", nargs="?", default="", help="要搜索的模式串（支持正则表达式）。如果仅过滤列表可为空。")
        
        # 过滤器
        self.parser.add_argument("-t", "--type", help="过滤实体类型（支持正则表达式）。")
        self.parser.add_argument("--rel", help="过滤关系目标。格式必须为 '谓词模式:目标模式'，均支持正则。注意: 仅能筛选出当前实体中明确声明的该关系，不具备逆向推导能力。")
        
        # 搜索范围
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument("-n", "--name", action="store_true", help="仅搜索实体名称及别名 (aliases)。")
        group.add_argument("-c", "--content", action="store_true", help="仅搜索正文内容。")
        group.add_argument("-a", "--all", action="store_true", default=True, help="全方位全局搜索 (默认)。")
        
        # 输出控制
        self.parser.add_argument("--names-only", action="store_true", help="仅输出匹配的实体名称列表。")
        self.parser.add_argument("-C", "--context", type=int, default=0, help="显示匹配正文时的上下文行数。")

    def run(self):
        self.setup()
        ctx = self.ctx

        entities_dir = ctx.entities_path
        if not entities_dir.exists():
            self.error(f"实体目录不存在: {entities_dir}")

        scope = "all"
        if self.args.name: scope = "name"
        elif self.args.content: scope = "content"

        # 1. 编译过滤器和搜索正则
        try:
            type_regex = re.compile(self.args.type, re.IGNORECASE) if self.args.type else None
            
            rel_pred_regex = None
            rel_target_regex = None
            if self.args.rel:
                if ":" not in self.args.rel:
                    self.error("--rel 参数必须包含且仅包含一个 ':' 分隔谓词与目标。格式: 'pred:target'")
                parts = self.args.rel.split(":", 1)
                rel_pred_regex = re.compile(parts[0].strip(), re.IGNORECASE)
                rel_target_regex = re.compile(parts[1].strip(), re.IGNORECASE)
            
            search_regex = re.compile(self.args.pattern, re.IGNORECASE) if self.args.pattern else None
        except re.error as e:
            self.error(f"正则表达式错误: {e}")

        matched_entities = {} # { entity_name: [ match_lines... ] }
        files_to_scan = list(entities_dir.glob("*.md"))

        # 2. 遍历全库扫描
        for file_path in files_to_scan:
            entity_name = file_path.stem
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
                
            metadata, body = MetadataParser.split_content(content)
            
            # --- 第一道防线：属性过滤 ---
            # 过滤 Type
            if type_regex:
                entity_type = metadata.get("entity type", "")
                if not type_regex.search(entity_type):
                    continue
                    
            # 过滤 Relation
            if self.args.rel:
                all_rels = MetadataParser.get_all_relations(metadata)
                rel_matched = False
                for pred, targets in all_rels.items():
                    if rel_pred_regex.search(pred):
                        if any(rel_target_regex.search(t) for t in targets):
                            rel_matched = True
                            break
                if not rel_matched:
                    continue

            # 如果只有过滤条件，没有搜文本的 pattern
            if not search_regex:
                matched_entities[entity_name] = []
                continue

            # --- 第二道防线：文本匹配 ---
            file_matched_lines = []
            
            # 搜名字 (包括 aliases)
            if scope in ("name", "all"):
                if search_regex.search(entity_name):
                    file_matched_lines.append(f"  [文件] {entity_name}.md")
                else:
                    aliases = MetadataParser.get_aliases(metadata)
                    for alias in aliases:
                        if search_regex.search(alias):
                            file_matched_lines.append(f"  [别名] {alias}")
                            break # 命中一个别名就行了
            
            # 搜正文
            if scope in ("content", "all"):
                lines = body.splitlines()
                matched_line_indices = []
                for i, line in enumerate(lines):
                    if search_regex.search(line):
                        matched_line_indices.append(i)
                
                if matched_line_indices:
                    # 处理上下文行
                    c = self.args.context
                    if c == 0:
                        for idx in matched_line_indices:
                            file_matched_lines.append(f"  {idx+1}: {lines[idx]}")
                    else:
                        # 合并重叠的上下文窗口
                        intervals = []
                        for idx in matched_line_indices:
                            intervals.append((max(0, idx - c), min(len(lines) - 1, idx + c)))
                        
                        merged_intervals = []
                        if intervals:
                            intervals.sort()
                            curr_start, curr_end = intervals[0]
                            for start, end in intervals[1:]:
                                if start <= curr_end + 1:
                                    curr_end = max(curr_end, end)
                                else:
                                    merged_intervals.append((curr_start, curr_end))
                                    curr_start, curr_end = start, end
                            merged_intervals.append((curr_start, curr_end))
                        
                        for start, end in merged_intervals:
                            if file_matched_lines and not file_matched_lines[-1].startswith("  ["):
                                file_matched_lines.append("  ---")
                            for i in range(start, end + 1):
                                prefix = ">" if i in matched_line_indices else " "
                                file_matched_lines.append(f" {prefix}{i+1}: {lines[i]}")

            if file_matched_lines or (scope == "all" and not file_matched_lines and search_regex.search(content)):
                # 如果匹配到了，或者全匹配但没有任何可提取的信息行（比如匹配到了不在规范内的元数据区域）
                matched_entities[entity_name] = file_matched_lines

        # 3. 输出结果
        if not matched_entities:
            self.add_result(f"未找到符合条件的实体。")
            self.finalize(success=True)
            return

        if self.args.names_only:
            self.add_result(f"找到 {len(matched_entities)} 个匹配实体:")
            for name in sorted(matched_entities.keys()):
                self.add_result(f"  - {name}")
        else:
            self.add_result(f"找到 {len(matched_entities)} 个匹配实体:")
            for name, lines in sorted(matched_entities.items()):
                self.add_result(f"\n[实体: {name}]")
                if not lines and search_regex:
                    self.add_result("  (无详细匹配行)")
                for line in lines:
                    self.add_result(line)
        
        self.finalize(success=True)

if __name__ == "__main__":
    SearchScript().run()
