#!/usr/bin/env python3
import sys
from datetime import datetime
from schema_define import ScriptBase, MetadataParser

class AppendUpdateScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="append-update",
            description="向已有实体追加更新块，并可选更新双向关系。",
            example="memocli append-update -e \"A\" -c \"新内容\" --rel-out \"friend:B\" -r \"更新\""
        )
        self.parser.add_argument("-e", "--entity", required=True, help="实体名称。")
        self.parser.add_argument("-c", "--content", required=True, help="追加的内容。")
        self.parser.add_argument("--rel-out", help="出站关系: 修改当前实体。格式 'pred:T1,T2'。")
        self.parser.add_argument("--rel-in", help="入站关系: 修改来源实体指向当前实体。格式 'pred:S1,S2'。")

    def update_other_entity(self, other_name: str, predicate: str, target: str):
        """更新库中已有的其他实体"""
        norm_other = MetadataParser.normalize_name(other_name)
        file_path = self.ctx.entities_path / f"{norm_other}.md"
        if not file_path.exists():
            self.add_result(f"[WARN] 来源实体 '{norm_other}' 不存在，跳过。")
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            metadata, body = MetadataParser.split_content(content)
            if MetadataParser.add_relation(metadata, predicate, target):
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                metadata["date modified"] = now
                metadata["reason"] = self.args.reason
                new_content = MetadataParser.serialize(metadata) + "\n" + body
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                self.add_result(f"已更新来源实体 '{norm_other}'。")
        except Exception as e:
            self.add_result(f"[!] 更新 '{norm_other}' 失败: {e}")

    def run(self):
        self.setup()
        if self.args.reason == "none":
            self.error("必须提供执行此操作的理由 (--reason/-r)。")

        ctx = self.ctx
        raw_name = self.args.entity
        normalized_name = MetadataParser.normalize_name(raw_name)
        target_file = ctx.entities_path / f"{normalized_name}.md"

        if not target_file.exists():
            self.error(f"实体不存在: {normalized_name}")

        # 1. 构造并追加更新块
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update_block = f"\n<!-- UPDATE_BLOCK_START: {now} | reason: {self.args.reason} -->\n"
        update_block += self.args.content.strip()
        update_block += f"\n<!-- UPDATE_BLOCK_END -->\n"

        try:
            with open(target_file, "a", encoding="utf-8") as f:
                f.write(update_block)
            self.add_result(f"更新块已成功追加到 '{normalized_name}'。")
        except Exception as e:
            self.error(f"追加更新块失败: {e}")

        # 2. 读取文件以更新元数据 (包括 date modified 和 rel-out)
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read()
            metadata, body = MetadataParser.split_content(content)
            metadata["date modified"] = now
            metadata["reason"] = self.args.reason
            
            # 处理 rel-out
            if self.args.rel_out:
                if ":" in self.args.rel_out:
                    pred, targets_raw = self.args.rel_out.split(":", 1)
                    targets = [t.strip() for t in targets_raw.split(",") if t.strip()]
                    for t in targets:
                        if MetadataParser.add_relation(metadata, pred, t):
                            self.add_result(f"更新出站关系: {pred} -> {t}")
                else:
                    self.add_result("[WARN] --rel-out 格式错误")

            new_content = MetadataParser.serialize(metadata) + "\n" + body
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            self.add_result("中心实体元数据已同步更新。")
        except Exception as e:
            self.add_result(f"[!] 同步中心实体元数据失败: {e}")

        # 3. 处理 rel-in
        if self.args.rel_in:
            if ":" in self.args.rel_in:
                pred, sources_raw = self.args.rel_in.split(":", 1)
                sources = [s.strip() for s in sources_raw.split(",") if s.strip()]
                for s in sources:
                    self.update_other_entity(s, pred, normalized_name)
            else:
                self.add_result("[WARN] --rel-in 格式错误")

        self.finalize(success=True)

if __name__ == "__main__":
    AppendUpdateScript().run()
