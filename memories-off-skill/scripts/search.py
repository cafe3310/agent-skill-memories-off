#!/usr/bin/env python3
import sys
import subprocess
import re
import shlex
from pathlib import Path
from schema_define import ScriptBase, MetadataParser

class SearchScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="search",
            description="在知识库中通过模式（正则表达式）检索实体。支持名称、元数据和正文搜索。",
            example='memocli search "搜索模式串" --name --names-only'
        )
        self.parser.add_argument("pattern", help="要搜索的模式（支持正则表达式）。")
        # 搜索范围
        group = self.parser.add_mutually_exclusive_group()
        group.add_argument("-n", "--name", action="store_true", help="仅搜索实体名称。")
        group.add_argument("-m", "--meta", action="store_true", help="仅搜索元数据 (Frontmatter)。")
        group.add_argument("-c", "--content", action="store_true", help="仅搜索正文内容。")
        group.add_argument("-a", "--all", action="store_true", default=True, help="全方位全局搜索 (默认)。")
        
        # 输出控制
        self.parser.add_argument("--names-only", action="store_true", help="仅输出匹配的实体名称列表。")
        self.parser.add_argument("-C", "--context", type=int, default=0, help="显示匹配行的上下文行数。")

    def run(self):
        self.setup()
        ctx = self.ctx
        pattern = self.args.pattern

        entities_dir = ctx.entities_path
        if not entities_dir.exists():
            self.error(f"实体目录不存在: {entities_dir}")

        scope = "all"
        if self.args.name: scope = "name"
        elif self.args.meta: scope = "meta"
        elif self.args.content: scope = "content"

        # 针对名称搜索的特殊处理：标准化 pattern 以匹配文件名
        search_pattern = pattern
        if scope == "name":
            search_pattern = MetadataParser.normalize_name(pattern)
            self.add_result(f"正在以标准名称格式搜索: '{search_pattern}'")

        safe_entities_dir = shlex.quote(str(entities_dir))

        safe_pattern = shlex.quote(search_pattern)
        
        if scope == "name":
            # 搜索文件名
            cmd = f"ls {safe_entities_dir} | grep -iE {safe_pattern}"
            output = subprocess.run(cmd, capture_output=True, text=True, shell=True).stdout.strip()
            if output:
                results = output.splitlines()
        else:
            grep_flags = "-riE"
            if self.args.names_only:
                grep_flags += "l"
            elif self.args.context > 0:
                grep_flags += f" -C {self.args.context}"
            
            cmd = f"grep {grep_flags} {safe_pattern} {safe_entities_dir} --exclude='meta.md'"
            output = subprocess.run(cmd, capture_output=True, text=True, shell=True).stdout.strip()
            if output:
                results = output.splitlines()

        if not results:
            self.add_result(f"未找到匹配项: {pattern}")
            self.finalize(success=True)
            return

        if self.args.names_only:
            clean_names = []
            for r in results:
                name = Path(r).name.replace(".md", "")
                if name not in clean_names:
                    clean_names.append(name)
            
            self.add_result(f"找到 {len(clean_names)} 个匹配实体:")
            for n in clean_names:
                self.add_result(f"  - {n}")
        else:
            current_entity = ""
            for line in results:
                # 仅在第一个冒号处分割，避免误伤包含中划线的路径
                if ":" in line:
                    file_path, match_detail = line.split(":", 1)
                    entity_name = Path(file_path).name.replace(".md", "")
                    
                    if entity_name != current_entity:
                        self.add_result(f"\n[实体: {entity_name}]")
                        current_entity = entity_name
                    
                    # 清理显示路径，使其更简洁
                    display_line = line.replace(str(entities_dir)+'/', "")
                    self.add_result(f"  {display_line}")
                else:
                    self.add_result(f"  {line}")
        
        self.finalize(success=True)

if __name__ == "__main__":
    SearchScript().run()
