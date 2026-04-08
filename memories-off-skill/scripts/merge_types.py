#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import datetime
from schema_define import ScriptBase, MetadataParser

class MergeTypesScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="merge_types",
            description="全库范围内将一个或多个实体类型合并为目标类型。",
            example="memocli merge-types --path . --sources 源类型1,源类型2 --target 目标类型 --reason \"原因\""
        )
        self.parser.add_argument("-s", "--sources", required=True, help="源类型名称列表（逗号分隔）。")
        self.parser.add_argument("-t", "--target", required=True, help="目标类型名称。")

    def run(self):
        self.setup()
        
        if self.args.reason == "none":
            self.error("必须提供合并理由 (--reason/-r)。", instruction="请补充理由后重试。")

        ctx = self.ctx
        source_types = [s.strip() for s in self.args.sources.split(",") if s.strip()]
        target_type = self.args.target
        
        self.add_result(f"准备将类型 {source_types} 合并至 [{target_type}]...")

        # 1. 扫描并更新实体文件
        affected_entities = []
        entity_files = list(ctx.entities_path.glob("*.md"))
        
        for file in entity_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                metadata, body = MetadataParser.split_content(content)
                
                current_type = metadata.get("entity type")
                if current_type in source_types:
                    metadata["entity type"] = target_type
                    metadata["date modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    new_content = MetadataParser.serialize(metadata) + "\n" + body
                    with open(file, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    
                    affected_entities.append(file.stem)
                    if ctx.is_git_repo():
                        ctx.run_git(["add", str(file)])
            except Exception as e:
                self.add_result(f"[!] 处理文件 {file.name} 时出错: {e}")

        # 2. 更新 meta.md 定义
        if ctx.meta_path.exists():
            try:
                with open(ctx.meta_path, "r", encoding="utf-8") as f:
                    meta_lines = f.readlines()
                
                new_meta_lines = []
                for line in meta_lines:
                    # 移除源类型的行
                    is_source = any(f"- {src}" in line for src in source_types)
                    if not is_source:
                        new_meta_lines.append(line)
                
                if len(new_meta_lines) != len(meta_lines):
                    with open(ctx.meta_path, "w", encoding="utf-8") as f:
                        f.writelines(new_meta_lines)
                    if ctx.is_git_repo():
                        ctx.run_git(["add", str(ctx.meta_path)])
                    self.add_result("已从 meta.md 中移除旧的类型定义。")
            except Exception as e:
                self.add_result(f"[!] 更新 meta.md 失败: {e}")

        if not affected_entities:
            self.add_result("未发现属于源类型的实体。")
            self.finalize(success=True)
            return

        # 3. 提交变更
        if ctx.is_git_repo():
            commit_msg = f"Merge types {source_types} into {target_type} ({len(affected_entities)} entities): {self.args.reason}"
            try:
                ctx.run_git(["commit", "-m", commit_msg])
                self.add_result("已提交 Git 变更。")
            except Exception as e:
                self.add_result(f"[WARN] 自动提交失败: {e}")

        self.add_result(f"类型合并成功！已完成 {len(affected_entities)} 个实体的更新。")
        for e in affected_entities:
            self.add_result(f"  - {e}")

        self.finalize(success=True)

if __name__ == "__main__":
    MergeTypesScript().run()
