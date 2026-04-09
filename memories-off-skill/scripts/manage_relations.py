#!/usr/bin/env python3
import sys
from datetime import datetime
from schema_define import ScriptBase, MetadataParser

class ManageRelationsScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="manage_relations",
            description="管理实体间的显式语义关系，支持追加出站(add-rel-out)、入站(add-rel-in)或移除(remove-rel-out)操作，可以一并添加关系。",
            example="memocli manage-relations --source \"A\" --add-rel-out \"friend:B,C\" --add-rel-in \"member:GroupX\" -r \"关联朋友与组织\""
        )
        self.parser.add_argument("-s", "--source", required=True, help="中心实体名称。")
        self.parser.add_argument("--add-rel-out", help="追加出站关系: 修改中心实体。格式 'pred:T1,T2'。")
        self.parser.add_argument("--add-rel-in", help="追加入站关系: 修改来源实体。格式 'pred:S1,S2'。")
        self.parser.add_argument("--remove-rel-out", help="移除指定的出站关系。格式 'pred:T1'。")

    def update_entity_file(self, entity_name: str, predicate: str, target: str, is_add: bool) -> bool:
        """执行单个文件的关系更新"""
        norm_name = MetadataParser.normalize_name(entity_name)
        file_path = self.ctx.entities_path / f"{norm_name}.md"
        
        if not file_path.exists():
            self.add_result(f"[WARN] 实体 '{norm_name}' 不存在，跳过。")
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            metadata, body = MetadataParser.split_content(content)
            
            if is_add:
                changed = MetadataParser.add_relation(metadata, predicate, target)
                msg = f"添加关系: {predicate} -> {target}"
            else:
                changed = MetadataParser.remove_relation(metadata, predicate, target)
                msg = f"移除关系: {predicate} -> {target}"
            
            if changed:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                metadata["date modified"] = now
                metadata["reason"] = self.args.reason
                new_content = MetadataParser.serialize(metadata) + "\n" + body
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                self.add_result(f"已更新 '{norm_name}': {msg}")
                return True
            else:
                self.add_result(f"'{norm_name}' 中关系已存在/不存在，无需变更。")
        except Exception as e:
            self.add_result(f"[!] 处理 '{norm_name}' 失败: {e}")
        return False

    def run(self):
        self.setup()
        if self.args.reason == "none":
            self.error("必须提供执行此操作的理由 (--reason/-r)。")

        source_name = MetadataParser.normalize_name(self.args.source)
        
        # 1. 处理 add-rel-out (修改 source 实体)
        if self.args.add_rel_out:
            if ":" in self.args.add_rel_out:
                pred, targets_raw = self.args.add_rel_out.split(":", 1)
                targets = [t.strip() for t in targets_raw.split(",") if t.strip()]
                for t in targets:
                    self.update_entity_file(source_name, pred, t, is_add=True)
            else:
                self.add_result("[!] --add-rel-out 格式错误 (应为 'pred:T1,T2')")

        # 2. 处理 remove-rel-out
        if self.args.remove_rel_out:
            if ":" in self.args.remove_rel_out:
                pred, target = self.args.remove_rel_out.split(":", 1)
                self.update_entity_file(source_name, pred, target.strip(), is_add=False)
            else:
                self.add_result("[!] --remove-rel-out 格式错误")

        # 3. 处理 add-rel-in (修改 source 之外的其他实体)
        if self.args.add_rel_in:
            if ":" in self.args.add_rel_in:
                pred, sources_raw = self.args.add_rel_in.split(":", 1)
                sources = [s.strip() for s in sources_raw.split(",") if s.strip()]
                for s in sources:
                    # 语义是: Source -> [pred] -> Current(source_name)
                    self.update_entity_file(s, pred, source_name, is_add=True)
            else:
                self.add_result("[!] --add-rel-in 格式错误")

        self.finalize(success=True)

if __name__ == "__main__":
    ManageRelationsScript().run()
