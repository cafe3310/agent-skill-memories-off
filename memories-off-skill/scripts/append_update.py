#!/usr/bin/env python3
import sys
from datetime import datetime
from schema_define import ScriptBase, MetadataParser

class AppendUpdateScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="append-update",
            description="向已有实体追加非破坏性的更新块（Buffer-Update 模式）。",
            example="memocli append-update --path . -e \"人物-cafe3310\" -c \"最近在学习 Python\" -r \"更新技能记录\""
        )
        self.parser.add_argument("-e", "--entity", required=True, help="实体名称（不含 .md）。")
        self.parser.add_argument("-c", "--content", required=True, help="要追加的内容。")

    def run(self):
        self.setup()
        
        if self.args.reason == "none":
            self.error("必须提供执行此操作的理由 (--reason/-r)。", instruction="请补充理由后重试。")

        ctx = self.ctx
        raw_name = self.args.entity
        normalized_name = MetadataParser.normalize_name(raw_name)
        target_file = ctx.entities_path / f"{normalized_name}.md"

        if not target_file.exists():
            self.error(f"实体不存在: {normalized_name}")

        self.add_result(f"正在向实体 '{normalized_name}' 追加更新块...")

        # 1. 构造更新块
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update_block = f"\n<!-- UPDATE_BLOCK_START: {now} | reason: {self.args.reason} -->\n"
        update_block += self.args.content.strip()
        update_block += f"\n<!-- UPDATE_BLOCK_END -->\n"

        # 2. 追加到文件末尾
        try:
            with open(target_file, "a", encoding="utf-8") as f:
                f.write(update_block)
            self.add_result("更新块已成功追加到文件末尾。")
        except Exception as e:
            self.error(f"追加更新块失败: {e}")

        # 3. 更新元数据的 date modified (可选，但建议)
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            metadata, body = MetadataParser.split_content(content)
            metadata["date modified"] = now
            metadata["reason"] = self.args.reason
            
            new_content = MetadataParser.serialize(metadata) + "\n" + body
            
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            self.add_result(f"实体元数据已同步更新 (date modified: {now})。")
        except Exception as e:
            self.add_result(f"[!] 同步更新元数据失败: {e} (但更新块已写入)")

        # 4. 完成
        self.finalize(success=True)

if __name__ == "__main__":
    AppendUpdateScript().run()
