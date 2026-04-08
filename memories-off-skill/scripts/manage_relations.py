#!/usr/bin/env python3
import sys
from datetime import datetime
from schema_define import ScriptBase, MetadataParser

class ManageRelationsScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="manage_relations",
            description="在实体 Frontmatter 中增加或删除显式语义关系。",
            example="memocli manage-relations --path . --source \"人物-cafe3310\" --add \"负责:概念-Memory-Skill\" -r \"分配职责\""
        )
        self.parser.add_argument("-s", "--source", required=True, help="源实体名称（不含 .md）。")
        self.parser.add_argument("--add", help="增加关系，格式为 'rel_type:TargetEntity'。")
        self.parser.add_argument("--remove", help="删除关系，格式为 'rel_type:TargetEntity'。")

    def run(self):
        self.setup()
        
        if self.args.reason == "none":
            self.error("必须提供执行此操作的理由 (--reason/-r)。", instruction="请补充理由后重试。")

        if not self.args.add and not self.args.remove:
            self.error("必须提供 --add 或 --remove 参数。", instruction="请指定要添加或删除的关系。")

        ctx = self.ctx
        raw_source_name = self.args.source
        source_name = MetadataParser.normalize_name(raw_source_name)
        source_file = ctx.entities_path / f"{source_name}.md"

        if not source_file.exists():
            self.error(f"源实体不存在: {source_name}")

        self.add_result(f"正在管理实体 '{source_name}' 的显式关系...")

        # 1. 读取并解析文件
        try:
            with open(source_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            metadata, body = MetadataParser.split_content(content)
        except Exception as e:
            self.error(f"读取或解析实体失败: {e}")

        changed = False

        # 2. 处理删除关系
        if self.args.remove:
            if ":" in self.args.remove:
                rel_type, target = self.args.remove.split(":", 1)
                normalized_rel = MetadataParser.normalize_predicate(rel_type)
                rel_key = f"relation as {normalized_rel}".lower()
                target_val = MetadataParser.normalize_name(target.strip())

                if rel_key in metadata:
                    # 获取旧值进行精确匹配
                    old_val = metadata[rel_key]
                    if MetadataParser.normalize_name(old_val) == target_val:
                        del metadata[rel_key]
                        self.add_result(f"成功删除关系: {normalized_rel} -> {target_val}")
                        changed = True
                    else:
                        self.add_result(f"[!] 关系类型 '{normalized_rel}' 存在，但指向的是 '{old_val}' 而非 '{target_val}' (跳过)")
                else:
                    self.add_result(f"[!] 未找到指定的关系: {normalized_rel} (跳过)")
            else:
                self.add_result("[!] --remove 格式无效，应为 'type:target' (跳过)")

        # 3. 处理增加关系
        if self.args.add:
            if ":" in self.args.add:
                rel_type, target = self.args.add.split(":", 1)
                normalized_rel = MetadataParser.normalize_predicate(rel_type)
                rel_key = f"relation as {normalized_rel}".lower()
                target_val = MetadataParser.normalize_name(target.strip())

                # 检查目标是否存在
                target_file = ctx.entities_path / f"{target_val}.md"
                if not target_file.exists():
                    self.add_result(f"[WARN] 目标实体 '{target_val}' 似乎不存在，但仍将建立链接。")

                metadata[rel_key] = target_val
                self.add_result(f"成功建立关系: {normalized_rel} -> {target_val}")
                changed = True

            else:
                self.add_result("[!] --add 格式无效，应为 'type:target' (跳过)")

        # 4. 写回文件
        if changed:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            metadata["date modified"] = now
            metadata["reason"] = self.args.reason
            
            new_content = MetadataParser.serialize(metadata) + "\n" + body
            
            try:
                with open(source_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
                self.add_result(f"实体文件已更新 (date modified: {now})。")
            except Exception as e:
                self.error(f"写回文件失败: {e}")
        else:
            self.add_result("未发生任何变更。")

        # 5. 完成
        self.finalize(success=True)

if __name__ == "__main__":
    ManageRelationsScript().run()
