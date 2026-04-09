#!/usr/bin/env python3
import sys
import re
from pathlib import Path
from schema_define import ScriptBase, MetadataParser

class GetRelationsScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="get_relations",
            description="分析实体的关联网络，列出所有指向和被指向的关系。",
            example="memocli get-relations --path . --entity 人物-cafe3310"
        )
        self.parser.add_argument("-e", "--entity", required=True, help="要查询的实体名称（不含 .md）。")
        self.parser.add_argument("-t", "--type", help="按关系类型过滤（模糊匹配）。")

    def run(self):
        self.setup()
        ctx = self.ctx
        raw_name = self.args.entity
        target_name = MetadataParser.normalize_name(raw_name)
        target_file = ctx.entities_path / f"{target_name}.md"

        if not target_file.exists():
            self.error(f"实体不存在: {target_name}")

        self.add_result(f"正在分析实体 '{target_name}' 的关联网络...")
        
        explicit_out = [] # 显式流出 (Metadata)
        explicit_in = []  # 显式流入
        implicit_out = [] # 隐式流出 (WikiLinks)
        implicit_in = []  # 隐式流入

        # 1. 解析目标实体的流出关系
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read()
                metadata, body = MetadataParser.split_content(content)
                
                # 显式流出
                for key, val in metadata.items():
                    if " as " in key:
                        rel_type = key.split(" as ")[1]
                        if not self.args.type or self.args.type.lower() in rel_type.lower():
                            # 分割并去重
                            for t in [x.strip() for x in val.split(",") if x.strip()]:
                                explicit_out.append((rel_type, t))
                
                # 隐式流出 (WikiLinks)
                links = re.findall(r"\[\[(.*?)\]\]", body)
                for link in links:
                    # 处理 [[Path/To/Entity|Alias]] 或 [[Entity]]
                    link_name = link.split("|")[0].strip()
                    implicit_out.append(link_name)
        except Exception as e:
            self.add_result(f"[!] 读取目标实体失败: {e}")

        # 2. 全库扫描流入关系
        self.add_result("正在扫描全库以查找流入关联...")
        for file in ctx.entities_path.glob("*.md"):
            if file.name == target_file.name:
                continue
            
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                    name = file.stem
                    m, b = MetadataParser.split_content(content)
                    
                    # 显式流入
                    for k, v in m.items():
                        if " as " in k:
                            # 拆分多值并规范化比较
                            vals = [MetadataParser.normalize_name(x.strip()) for x in v.split(",") if x.strip()]
                            if target_name in vals:
                                rel_type = k.split(" as ")[1]
                                if not self.args.type or self.args.type.lower() in rel_type.lower():
                                    explicit_in.append((name, rel_type))
                    
                    # 隐式流入
                    if f"[[{target_name}]]" in b or f"[[{target_name}|" in b:
                        implicit_in.append(name)
            except:
                pass

        # 3. 构造结果展示
        self.add_result("\n[显式关系 - 流出] (Explicit Outbound)")
        if explicit_out:
            for r, t in explicit_out:
                self.add_result(f"  - {target_name} --({r})--> {t}")
        else:
            self.add_result("  (无)")

        self.add_result("\n[显式关系 - 流入] (Explicit Inbound)")
        if explicit_in:
            for s, r in explicit_in:
                self.add_result(f"  - {s} --({r})--> {target_name}")
        else:
            self.add_result("  (无)")

        self.add_result("\n[隐式链接 - 流出] (Implicit Outbound WikiLinks)")
        if implicit_out:
            for t in sorted(set(implicit_out)):
                self.add_result(f"  - [[{t}]]")
        else:
            self.add_result("  (无)")

        self.add_result("\n[隐式链接 - 流入] (Implicit Inbound WikiLinks)")
        if implicit_in:
            for s in sorted(set(implicit_in)):
                self.add_result(f"  - [[{s}]]")
        else:
            self.add_result("  (无)")

        self.finalize(success=True)

if __name__ == "__main__":
    GetRelationsScript().run()
