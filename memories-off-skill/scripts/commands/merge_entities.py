#!/usr/bin/env python3
import sys
import re
from pathlib import Path
from utility.schema_define import ScriptBase, MetadataParser
from datetime import datetime

class MergeEntitiesScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="merge_entities",
            description="将多个源实体的内容和关系合并到目标实体，并同步重定向全库引用。",
            example="memocli merge-entities -s \"A,B\" -t \"C\" -r \"合并重复实体\""
        )
        self.parser.add_argument("-s", "--sources", required=True, help="源实体名称列表，逗号分隔。")
        self.parser.add_argument("-t", "--target", required=True, help="目标实体名称。")

    def run(self):
        self.setup()
        
        if self.args.reason == "none":
            self.error("必须提供合并理由 (--reason/-r)。")

        ctx = self.ctx
        source_names = [MetadataParser.normalize_name(s.strip()) for s in self.args.sources.split(",") if s.strip()]
        target_name = MetadataParser.normalize_name(self.args.target)
        target_file = ctx.entities_path / f"{target_name}.md"

        if not target_file.exists():
            self.error(f"目标实体不存在: {target_name}")

        self.add_result(f"正在准备合并: {', '.join(source_names)} -> {target_name}")

        # 1. 读取目标实体现状
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                target_content = f.read()
            target_meta, target_body = MetadataParser.split_content(target_content)
        except Exception as e:
            self.error(f"读取目标实体失败: {e}")

        # 2. 遍历源实体，提取内容并合并关系
        merged_body_blocks = [target_body, "\n\n--- 合并内容注入 ---"]
        valid_sources = []
        
        for src in source_names:
            if src == target_name: continue
            src_file = ctx.entities_path / f"{src}.md"
            if not src_file.exists():
                self.add_result(f"[WARN] 源实体 '{src}' 不存在，跳过。")
                continue
            
            try:
                with open(src_file, "r", encoding="utf-8") as f:
                    src_content = f.read()
                src_meta, src_body = MetadataParser.split_content(src_content)
                
                # 合并正文
                merged_body_blocks.append(f"\n### 来自 {src} 的内容\n{src_body.strip()}")
                
                # 合并关系 (Metadata)
                for key, val in src_meta.items():
                    if " as " in key:
                        pred = key.split(" as ", 1)[1]
                        targets = [t.strip() for t in val.split(",") if t.strip()]
                        for t in targets:
                            # 如果目标不是正在被合并的源实体之一，则添加
                            # 如果目标是源实体之一，则将其重定向到 target_name
                            t_norm = MetadataParser.normalize_name(t)
                            if t_norm in source_names or t_norm == target_name:
                                # 自身关联或内部关联，统一指向合并后的目标
                                # (通常这种环状引用在合并后可以忽略，但为了严谨我们保留指向 target)
                                MetadataParser.add_relation(target_meta, pred, target_name)
                            else:
                                MetadataParser.add_relation(target_meta, pred, t)
                
                valid_sources.append(src)
            except Exception as e:
                self.add_result(f"[!] 处理源实体 '{src}' 失败: {e}")

        if not valid_sources:
            self.error("没有有效的源实体可供合并。")

        # 3. 写回目标实体
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        target_meta["date modified"] = now
        target_meta["reason"] = f"合并实体 {', '.join(valid_sources)}: {self.args.reason}"
        
        new_target_content = MetadataParser.serialize(target_meta) + "\n" + "\n".join(merged_body_blocks)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(new_target_content)
        self.add_result(f"[+] 目标实体 '{target_name}' 已更新（内容与关系已合并）。")

        # 4. 全局重定向引用 (同 rename 逻辑，但支持多对一)
        self.add_result("正在同步全库引用...")
        affected_count = 0
        all_files = list(ctx.entities_path.glob("*.md")) + [ctx.meta_path]
        
        for md_file in all_files:
            if not md_file.exists() or md_file.name == target_file.name: continue
            
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                m, b = MetadataParser.split_content(content)
                changed = False
                
                # 元数据重定向
                for k, v in m.items():
                    targets = [t.strip() for t in v.split(",") if t.strip()]
                    new_targets = []
                    item_changed = False
                    for t in targets:
                        if MetadataParser.normalize_name(t) in valid_sources:
                            if target_name not in [MetadataParser.normalize_name(nt) for nt in new_targets]:
                                new_targets.append(target_name)
                            item_changed = True
                        else:
                            new_targets.append(t)
                    
                    if item_changed:
                        # 再次去重，防止合并后出现重复目标
                        unique_targets = []
                        seen = set()
                        for nt in new_targets:
                            norm_nt = MetadataParser.normalize_name(nt)
                            if norm_nt not in seen:
                                unique_targets.append(nt)
                                seen.add(norm_nt)
                        m[k] = ", ".join(unique_targets)
                        changed = True
                
                # 正文 WikiLinks 重定向
                for src in valid_sources:
                    pattern = re.compile(rf"\[\[{re.escape(src)}\]\]", re.IGNORECASE)
                    if pattern.search(b):
                        b = pattern.sub(f"[[{target_name}]]", b)
                        changed = True
                
                if changed:
                    m["date modified"] = now
                    m["reason"] = f"同步合并引用 {', '.join(valid_sources)} -> {target_name}"
                    new_c = MetadataParser.serialize(m) + "\n" + b
                    with open(md_file, "w", encoding="utf-8") as f:
                        f.write(new_c)
                    if ctx.is_git_repo():
                        ctx.run_git(["add", str(md_file)])
                    affected_count += 1
            except Exception as e:
                self.add_result(f"[!] 同步文件 '{md_file.name}' 失败: {e}")

        self.add_result(f"[+] 已同步 {affected_count} 个引用文件。")

        # 5. 删除源文件
        for src in valid_sources:
            src_file = ctx.entities_path / f"{src}.md"
            if ctx.is_git_repo():
                ctx.run_git(["rm", str(src_file)])
            else:
                src_file.unlink()
        
        if ctx.is_git_repo():
            ctx.run_git(["commit", "-m", f"merge {', '.join(valid_sources)} into {target_name}: {self.args.reason}"])
            self.add_result("已提交 Git 变更。")

        self.finalize(success=True)

if __name__ == "__main__":
    MergeEntitiesScript().run()
