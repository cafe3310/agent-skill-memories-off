#!/usr/bin/env python3
import sys
import re
from pathlib import Path
from utility.runtime import ScriptBase
from utility.schema_define import MetadataParser
from datetime import datetime

class RenameScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="rename_entity",
            description="重命名实体文件并自动同步全库范围内的 WikiLinks 引用及元数据关系。",
            group_name="结构化编辑 (Structured Editing)",
            example="memocli rename-entity --path . --old \"旧实体\" --new \"新实体\" -r \"修正命名\""
        )
        self.parser.add_argument("--old", required=True, help="原实体名称（不含 .md）。")
        self.parser.add_argument("--new", required=True, help="新实体名称（不含 .md）。")

    def run(self):
        self.setup()
        
        if self.args.reason == "none":
            self.error("必须提供重命名理由 (--reason/-r)。")

        ctx = self.ctx
        old_name = MetadataParser.normalize_name(self.args.old)
        new_name = MetadataParser.normalize_name(self.args.new)
        
        if old_name == new_name:
            self.error("新名称与旧名称相同。")

        old_file = ctx.entities_path / f"{old_name}.md"
        new_file = ctx.entities_path / f"{new_name}.md"
        
        if not old_file.exists():
            self.error(f"源文件不存在: {old_name}")
        
        if new_file.exists():
            self.error(f"目标文件已存在: {new_name}")

        self.add_result(f"正在重命名实体: {old_name} -> {new_name}")

        # 1. 执行重命名
        try:
            if ctx.is_git_repo():
                ctx.run_git(["mv", str(old_file), str(new_file)])
            else:
                old_file.rename(new_file)
        except Exception as e:
            self.error(f"物理重命名失败: {e}")

        # 2. 全量扫描并同步引用
        wikilink_pattern = re.compile(rf"\[\[{re.escape(old_name)}\]\]", re.IGNORECASE)
        affected_files = []
        files_to_scan = list(ctx.entities_path.glob("*.md")) + [ctx.meta_path]
        
        for md_file in files_to_scan:
            if not md_file.exists() or md_file.name == f"{new_name}.md":
                continue
            
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                metadata, body = MetadataParser.split_content(content)
                changed = False
                
                # A. 同步元数据中的关系 (支持多值列表)
                for key, value in metadata.items():
                    # 检查所有元数据值，如果包含 old_name 则替换
                    if old_name.lower() in value.lower():
                        targets = [t.strip() for t in value.split(",") if t.strip()]
                        new_targets = []
                        item_changed = False
                        for t in targets:
                            if MetadataParser.normalize_name(t) == old_name:
                                new_targets.append(new_name)
                                item_changed = True
                            else:
                                new_targets.append(t)
                        
                        if item_changed:
                            metadata[key] = ", ".join(new_targets)
                            changed = True
                
                # B. 同步正文中的 WikiLinks
                if wikilink_pattern.search(body):
                    body = wikilink_pattern.sub(f"[[{new_name}]]", body)
                    changed = True
                
                if changed:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    metadata["date modified"] = now
                    # 避免无限叠加理由，仅记录最新的重命名理由
                    metadata["reason"] = f"同步重命名 {old_name}->{new_name}: {self.args.reason}"
                    
                    new_content = MetadataParser.serialize(metadata) + "\n" + body
                    with open(md_file, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    
                    if ctx.is_git_repo():
                        ctx.run_git(["add", str(md_file)])
                    affected_files.append(md_file.name)
                    
            except Exception as e:
                self.add_result(f"[!] 处理 '{md_file.name}' 失败: {e}")

        # 3. 提交 Git 变更
        if ctx.is_git_repo() and affected_files:
            commit_msg = f"rename {old_name} -> {new_name}: {self.args.reason}"
            ctx.run_git(["commit", "-m", commit_msg])
            self.add_result("已提交 Git 变更。")

        self.add_result(f"同步完成！共更新 {len(affected_files)} 个文件的引用。")
        self.finalize(success=True)

if __name__ == "__main__":
    RenameScript().run()
