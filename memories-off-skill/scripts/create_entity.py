#!/usr/bin/env python3
import sys
from datetime import datetime
from schema_define import ScriptBase, MetadataParser

class CreateEntityScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="create_entity",
            description="在知识库中创建一个新的实体文件，可以一并添加关系（支持双向关联）。",
            example="memocli create-entity -n \"ProjectA\" -t \"Project\" --add-rel-out \"member:Alice,Bob\" --add-rel-in \"part of:CompanyX\" -r \"初始化项目\""
        )
        self.parser.add_argument("-n", "--name", help="实体名称。")
        self.parser.add_argument("-e", "--entity", help="实体名称 (等价于 --name)。")
        self.parser.add_argument("-t", "--type", required=True, help="实体类型。")
        self.parser.add_argument("-rel", "--relations", help="[别名] 等价于 --add-rel-out。")
        self.parser.add_argument("--add-rel-out", help="追加出站关系: 修改当前新实体。格式 'pred:T1,T2'。")
        self.parser.add_argument("--add-rel-in", help="追加入站关系: 修改来源实体，使其指向当前实体。格式 'pred:S1,S2'。")

    def update_other_entity(self, other_name: str, predicate: str, target: str):
        """更新库中已有的其他实体"""
        norm_other = MetadataParser.normalize_name(other_name)
        file_path = self.ctx.entities_path / f"{norm_other}.md"
        
        if not file_path.exists():
            self.add_result(f"[WARN] 来源实体 '{norm_other}' 不存在，无法建立入站关联。")
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
            self.add_result(f"[!] 更新来源实体 '{norm_other}' 失败: {e}")

    def run(self):
        self.setup()
        
        if self.args.reason == "none":
            self.error("必须提供创建实体的理由 (--reason/-r)。")

        ctx = self.ctx
        raw_name = self.args.entity if self.args.entity else self.args.name
        if not raw_name:
            self.error("必须提供实体名称 (--name 或 --entity)。")
            
        normalized_name = MetadataParser.normalize_name(raw_name)
        file_path = ctx.entities_path / f"{normalized_name}.md"

        if file_path.exists():
            self.error(f"实体已存在: {normalized_name}")

        # 1. 构造初始元数据
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata = {
            "entity type": self.args.type,
            "date created": now,
            "date modified": now,
            "reason": self.args.reason
        }

        # 2. 处理 add-rel-out (当前实体 -> 目标)
        add_rel_out_str = self.args.add_rel_out or self.args.relations
        if add_rel_out_str:
            if ":" in add_rel_out_str:
                pred, targets_raw = add_rel_out_str.split(":", 1)
                targets = [t.strip() for t in targets_raw.split(",") if t.strip()]
                for t in targets:
                    MetadataParser.add_relation(metadata, pred, t)
                    self.add_result(f"追加出站关系: {pred} -> {t}")
            else:
                self.add_result("[WARN] --add-rel-out 格式错误，已跳过。")

        # 3. 构造文件内容并写入
        content = MetadataParser.serialize(metadata)
        content += f"\n# {normalized_name}\n\n(在此处输入实体的详细描述...)\n"

        try:
            ctx.entities_path.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.add_result(f"实体创建成功: {normalized_name}")
        except Exception as e:
            self.error(f"写入文件失败: {e}")

        # 4. 处理 add-rel-in (来源 -> 当前实体)
        if self.args.add_rel_in:
            if ":" in self.args.add_rel_in:
                pred, sources_raw = self.args.add_rel_in.split(":", 1)
                sources = [s.strip() for s in sources_raw.split(",") if s.strip()]
                for s in sources:
                    self.update_other_entity(s, pred, normalized_name)
            else:
                self.add_result("[WARN] --add-rel-in 格式错误，已跳过。")

        self.finalize(success=True)

if __name__ == "__main__":
    CreateEntityScript().run()
