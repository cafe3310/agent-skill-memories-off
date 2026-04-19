#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from utility.runtime import ScriptBase
from utility.schema_define import MetadataParser

class RenameTypeScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="rename_type",
            description="全库范围内重命名特定的实体类型并同步文件、meta.md。",
            example="memocli rename-type --path . --old 旧类型 --new 新类型 --reason \"规范化\""
        )
        self.parser.add_argument("--old", required=True, help="旧类型名称。")
        self.parser.add_argument("--new", required=True, help="新类型名称。")

    def run(self):
        self.setup()
        
        if self.args.reason == "none":
            self.error("必须提供重命名理由 (--reason/-r)。", instruction="请补充理由后重试。")

        ctx = self.ctx
        old_type = self.args.old
        new_type = self.args.new
        
        self.add_result(f"准备将类型 [{old_type}] 重命名为 [{new_type}]...")

        # 1. 扫描并更新实体文件
        affected_entities = []
        entity_files = list(ctx.entities_path.glob("*.md"))
        
        for file in entity_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                metadata, body = MetadataParser.split_content(content)
                
                if metadata.get("entity type") == old_type:
                    metadata["entity type"] = new_type
                    metadata["date modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    new_content = MetadataParser.serialize(metadata) + "\n" + body
                    with open(file, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    
                    affected_entities.append(file.stem)
                    if ctx.is_git_repo():
                        ctx.run_git(["add", str(file)])
            except Exception as e:
                self.add_result(f"[!] 处理文件 {file.name} 时出错: {e}")

        # 2. 更新 meta.md 中的定义并检查残留
        if ctx.meta_path.exists():
            try:
                with open(ctx.meta_path, "r", encoding="utf-8") as f:
                    meta_content = f.read()
                
                # 安全替换：仅替换标准列表定义
                new_meta_content = meta_content.replace(f"- {old_type}", f"- {new_type}")
                if new_meta_content != meta_content:
                    with open(ctx.meta_path, "w", encoding="utf-8") as f:
                        f.write(new_meta_content)
                    if ctx.is_git_repo():
                        ctx.run_git(["add", str(ctx.meta_path)])
                    self.add_result("已更新 meta.md 中标准的类型定义 (- 类型名)。")
                
                # 检查是否还有残留匹配
                remaining_matches = []
                lines = new_meta_content.splitlines()
                for i, line in enumerate(lines):
                    if old_type in line:
                        remaining_matches.append((i+1, line.strip()))
                
                if remaining_matches:
                    self.add_result(f"\n[!] 提示: 在 meta.md 中发现了 [{old_type}] 的其他匹配项。如果它们是相关说明文本，Agent 需要使用相关工具手动修改:")
                    for line_num, line_text in remaining_matches[:10]:
                        self.add_result(f"    第 {line_num} 行: {line_text}")
                    if len(remaining_matches) > 10:
                        self.add_result(f"    ... (还有 {len(remaining_matches) - 10} 项匹配)")

            except Exception as e:
                self.add_result(f"[!] 更新/检查 meta.md 失败: {e}")

        if not affected_entities:
            self.add_result("未发现属于该类型的实体。")
            self.finalize(success=True)
            return

        # 3. 提交变更
        if ctx.is_git_repo():
            commit_msg = f"Rename type {old_type} -> {new_type} ({len(affected_entities)} entities): {self.args.reason}"
            try:
                # 尝试直接使用 ctx.run_git
                ctx.run_git(["commit", "-m", commit_msg])
                self.add_result(f"已提交 Git 变更。")
            except Exception as e:
                self.add_result(f"[WARN] 文件已更新但自动提交失败: {e}")

        self.add_result(f"类型重命名成功！已完成 {len(affected_entities)} 个实体的更新。")
        for e in affected_entities:
            self.add_result(f"  - {e}")

        self.finalize(success=True)

if __name__ == "__main__":
    RenameTypeScript().run()
