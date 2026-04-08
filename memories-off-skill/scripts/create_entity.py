#!/usr/bin/env python3
import sys
from datetime import datetime
from schema_define import ScriptBase, MetadataParser

class CreateEntityScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="create_entity",
            description="在知识库中创建一个新的实体文件，文件名即为实体名称。",
            example="memocli create-entity --path . --entity \"张三\" --type \"人物\" --reason \"添加新角色\""
        )
        self.parser.add_argument("-n", "--name", help="实体名称。")
        self.parser.add_argument("-e", "--entity", help="实体名称 (等同于 --name，作为文件名使用)。")
        self.parser.add_argument("-t", "--type", required=True, help="实体类型（如：人物、概念、项目）。")
        self.parser.add_argument("-rel", "--relations", help="初始关系，格式为 'rel1:Target1,rel2:Target2'。")

    def run(self):
        self.setup()
        
        if self.args.reason == "none":
            self.error("必须提供创建实体的理由 (--reason/-r)。", instruction="请补充理由后重试。")

        ctx = self.ctx
        raw_name = self.args.entity if self.args.entity else self.args.name
        if not raw_name:
            self.error("必须提供实体名称 (--name 或 --entity)。")
            
        normalized_name = MetadataParser.normalize_name(raw_name)
        file_path = ctx.entities_path / f"{normalized_name}.md"

        if file_path.exists():
            self.error(f"实体已存在: {normalized_name}", instruction="请使用已有的实体或选择不同的名称。")

        self.add_result(f"正在创建新实体: {normalized_name} (类型: {self.args.type})")

        # 2. 构造初始元数据
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata = {
            "entity type": self.args.type,
            "date created": now,
            "date modified": now,
            "reason": self.args.reason
        }

        # 处理初始关系 (更鲁棒的解析)
        if self.args.relations:
            rel_pairs = [p.strip() for p in self.args.relations.split(",") if p.strip()]
            for pair in rel_pairs:
                if ":" in pair:
                    rel, target = pair.split(":", 1)
                    metadata[f"relation as {rel.strip()}"] = target.strip()
                else:
                    self.add_result(f"[WARN] 关系格式无效 (跳过): {pair}")

        # 3. 构造文件内容
        content = MetadataParser.serialize(metadata)
        content += f"\n# {normalized_name}\n\n(在此处输入实体的详细描述...)\n"

        # 4. 写入文件
        try:
            ctx.entities_path.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.add_result(f"文件已写入: {file_path.relative_to(ctx.root_path)}")
        except Exception as e:
            self.error(f"写入文件失败: {e}")

        # 5. 完成
        self.finalize(success=True)

if __name__ == "__main__":
    CreateEntityScript().run()
