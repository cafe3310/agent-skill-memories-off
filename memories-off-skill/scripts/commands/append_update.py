#!/usr/bin/env python3
import sys
from datetime import datetime
from utility.runtime import ScriptBase
from utility.schema_define import MetadataParser, UpdateBlockManager

class AppendUpdateScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="append_update",
            description="向已有实体追加更新块（Buffer-Update 模式），可以一并添加多组复杂的双向关系关联。",
            group_name="知识写入 (Knowledge Writing)",
            example='memocli append-update --entity "实体名称" --content "在此输入追加内容" --add-rel-out "关系谓词:目标1" --reason "理由"'
        )
        self.parser.add_argument("-e", "--entity", required=True, help="实体名称。")
        self.parser.add_argument("-c", "--content", help="追加的内容（字符串形式）。")
        self.parser.add_argument("--content-stdin", action="store_true", help="从标准输入 (STDIN) 读取追加内容。与 --content 互斥。")
        self.parser.add_argument("--add-rel-out", action="append", help="追加出站关系: 修改当前实体。支持多次使用。格式 'pred:T1,T2'。")
        self.parser.add_argument("--add-rel-in", action="append", help="追加入站关系: 修改来源实体指向当前实体支持多次使用。格式 'pred:S1,S2'。")

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

        # 互斥检查与内容获取
        if self.args.content and self.args.content_stdin:
            self.error("参数冲突：不能同时使用 --content 和 --content-stdin。")
            
        update_content = ""
        if self.args.content_stdin:
            try:
                update_content = sys.stdin.read()
            except Exception as e:
                self.error(f"从 STDIN 读取内容失败: {e}")
        elif self.args.content:
            update_content = self.args.content

        if not update_content.strip() and not self.args.add_rel_out and not self.args.add_rel_in:
            self.error("未提供任何有效的更新内容或关系变更。请提供 --content, --content-stdin 或关系参数。")

        ctx = self.ctx
        raw_name = self.args.entity
        normalized_name = MetadataParser.normalize_name(raw_name)
        target_file = ctx.entities_path / f"{normalized_name}.md"

        if not target_file.exists():
            self.error(f"实体不存在: {normalized_name}")

        # 1. 构造并追加更新块
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update_block = UpdateBlockManager.create_block(update_content, self.args.reason)

        try:
            with open(target_file, "a", encoding="utf-8") as f:
                f.write(update_block)
            self.add_result(f"更新块已成功追加到 '{normalized_name}'。")
        except Exception as e:
            self.error(f"追加更新块失败: {e}")

        # 2. 读取文件以更新元数据 (包括 date modified 和 add-rel-out)
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                content = f.read()
            metadata, body = MetadataParser.split_content(content)
            metadata["date modified"] = now
            
            # 处理 add-rel-out (List of Strings)
            if self.args.add_rel_out:
                for rel_str in self.args.add_rel_out:
                    if ":" in rel_str:
                        pred, targets_raw = rel_str.split(":", 1)
                        targets = [t.strip() for t in targets_raw.split(",") if t.strip()]
                        for t in targets:
                            if MetadataParser.add_relation(metadata, pred, t):
                                self.add_result(f"追加出站关系: {pred} -> {t}")
                    else:
                        self.add_result(f"[!] 格式错误: {rel_str}")

            new_content = MetadataParser.serialize(metadata) + "\n" + body
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            self.add_result("中心实体元数据已同步更新。")
        except Exception as e:
            self.add_result(f"[!] 同步中心实体元数据失败: {e}")

        # 3. 处理 add-rel-in (List of Strings)
        if self.args.add_rel_in:
            for rel_str in self.args.add_rel_in:
                if ":" in rel_str:
                    pred, sources_raw = rel_str.split(":", 1)
                    sources = [s.strip() for s in sources_raw.split(",") if s.strip()]
                    for s in sources:
                        self.update_other_entity(s, pred, normalized_name)
                else:
                    self.add_result(f"[!] 格式错误: {rel_str}")

        self.finalize(success=True)

if __name__ == "__main__":
    AppendUpdateScript().run()
