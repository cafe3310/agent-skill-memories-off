#!/usr/bin/env python3
import sys
import re
from pathlib import Path
from datetime import datetime
from schema_define import ScriptBase, MetadataParser

# 新版更新块正则 (匹配 HTML 注释风格)
NEW_BLOCK_RE = re.compile(
    r"<!-- UPDATE_BLOCK_START: (.*?) \| reason: (.*?) -->\n(.*?)\n<!-- UPDATE_BLOCK_END -->",
    re.DOTALL
)

class ConsolidateUpdatesScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="consolidate-updates",
            description="[高影响/严禁自动执行] 将实体末尾的缓冲更新块合并到正式章节中。除非用户明确指令，Agent 不得擅自运行此命令。",
            example='memocli consolidate-updates --path . --reason "定期整理任务内容"'
        )


    def consolidate_entity(self, file_path: Path):
        """解析并合并单个实体的所有更新块。"""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        blocks = list(NEW_BLOCK_RE.finditer(content))
        if not blocks:
            return False

        # 1. 提取元数据和纯正文（不含更新块）
        metadata, full_body = MetadataParser.split_content(content)
        # 移除所有更新块标记，得到干净正文
        clean_body = NEW_BLOCK_RE.sub("", full_body).strip()
        
        # 2. 合并逻辑 (简单追加到正文末尾)
        new_body = clean_body
        for match in blocks:
            timestamp, reason, block_content = match.groups()
            new_body += f"\n\n{block_content.strip()}"

        # 3. 更新元数据
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata["date modified"] = now
        
        # 4. 写回
        final_content = MetadataParser.serialize(metadata) + "\n" + new_body.strip() + "\n"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_content)
        
        return True

    def run(self):
        self.setup()
        
        if self.args.reason == "none":
            self.error("必须提供整理理由 (--reason/-r)。", instruction="请补充理由后重试。")

        ctx = self.ctx
        self.add_result(f"开始执行梦境整理 (Consolidation) 于: {ctx.root_path}")
        
        entity_files = list(ctx.entities_path.glob("*.md"))
        affected_files = []

        for file in entity_files:
            try:
                if self.consolidate_entity(file):
                    affected_files.append(file.stem)
                    if ctx.is_git_repo():
                        ctx.run_git(["add", str(file)])
                    self.add_result(f"[+] 已合并实体: {file.stem}")
            except Exception as e:
                self.add_result(f"[!] 处理 {file.name} 失败: {e}")

        if not affected_files:
            self.add_result("没有发现待处理的缓冲更新块。")
            self.finalize(success=True)
            return

        # 提交变更
        if ctx.is_git_repo():
            commit_msg = f"Consolidate updates for {len(affected_files)} entities: {self.args.reason}"
            try:
                ctx.run_git(["commit", "-m", commit_msg])
                self.add_result(f"已提交 Git 变更。")
            except Exception as e:
                self.add_result(f"[WARN] 整理已完成但自动提交失败: {e}")

        self.add_result(f"梦境整理圆满完成！共处理 {len(affected_files)} 个实体。")
        self.finalize(success=True)

if __name__ == "__main__":
    ConsolidateUpdatesScript().run()
