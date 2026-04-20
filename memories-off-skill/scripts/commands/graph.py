#!/usr/bin/env python3
import sys
import os
import json
import re
import tempfile
import webbrowser
from pathlib import Path
from utility.runtime import ScriptBase
from utility.schema_define import LibraryContext, MetadataParser

# --- HTML 渲染模板已从 assets 目录加载 ---
TEMPLATE_PATH = Path(__file__).parent.parent / "assets" / "graph_template.html"
try:
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        HTML_TEMPLATE = f.read()
except Exception as e:
    # 备退机制: 如果文件丢失，至少报出错误
    HTML_TEMPLATE = f"<h1>Template Load Error</h1><p>{e}</p>"


class GraphExporter:
    WIKILINK_PATTERN = re.compile(r"\[\[(.*?)\]\]")

    def __init__(self, ctx: LibraryContext):
        self.ctx = ctx
        self.nodes = []
        self.links = []
        self.entity_map = {}

    def _clean_display_name(self, name: str) -> str:
        return re.sub(r"^[^-]+-", "", name)

    def export(self) -> str:
        if not self.ctx.entities_path.exists():
            return json.dumps({"nodes": [], "links": []})

        entity_files = list(self.ctx.entities_path.glob("*.md"))
        for file in entity_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                    metadata, _ = MetadataParser.split_content(content)
                    e_type = metadata.get("entity type", "未分类")
                    raw_name = file.stem
                    display_name = self._clean_display_name(raw_name)
                    e_id = f"{e_type}-{display_name}"
                    self.entity_map[raw_name] = e_id
                    self.entity_map[display_name] = e_id
                    self.nodes.append({"id": e_id, "display_name": display_name, "type": e_type, "is_alias": False, "file_size": os.path.getsize(file)})
                    
                    aliases = metadata.get("aliases", "")
                    if aliases:
                        for alias in [a.strip() for a in aliases.split(",") if a.strip()]:
                            alias_id = f"Alias-{alias}"
                            self.nodes.append({"id": alias_id, "display_name": alias, "type": e_type, "is_alias": True, "val": 3})
                            self.links.append({"source": alias_id, "target": e_id, "predicate": "alias_of", "is_alias_link": True})
                            self.entity_map[alias] = e_id
            except Exception: pass

        for file in entity_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                    metadata, body = MetadataParser.split_content(content)
                    source_id = self.entity_map.get(file.stem)
                    if not source_id: continue

                    for key, val in metadata.items():
                        if key.startswith("relation"):
                            predicate = key.split(" as ", 1)[1] if " as " in key else "related"
                            # 优先处理 [[WikiLinks]]，否则处理逗号分隔列表
                            targets = self.WIKILINK_PATTERN.findall(val) or [t.strip() for t in val.split(",") if t.strip()]
                            for t in targets:
                                tid = self.entity_map.get(t) or self.entity_map.get(MetadataParser.normalize_name(t))
                                if tid and tid != source_id:
                                    self.links.append({"source": source_id, "target": tid, "predicate": predicate, "is_alias_link": False})

                    for t in self.WIKILINK_PATTERN.findall(body):
                        tid = self.entity_map.get(t)
                        if tid and tid != source_id:
                            if not any(l["source"] == source_id and l["target"] == tid for l in self.links):
                                self.links.append({"source": source_id, "target": tid, "predicate": "mentions", "is_alias_link": False})
            except Exception: pass

        return json.dumps({"nodes": self.nodes, "links": self.links}, ensure_ascii=False)

class GraphScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="graph",
            description="生成并开启 3D 知识图谱展示 (基于引力场模型)。",
            group_name="系统与维护 (System & Maintenance)",
            example="memocli graph --path ."
        )

    def run(self):
        self.setup()
        ctx = self.ctx
        self.add_result(f"正在分析知识库并生成图谱: {ctx.root_path}")
        
        exporter = GraphExporter(ctx)
        graph_json = exporter.export()
        html_content = HTML_TEMPLATE.replace("{DATA_JSON}", graph_json)
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tf:
                tf.write(html_content)
                temp_path = tf.name
            self.add_result(f"图谱已生成至临时文件: {temp_path}")
            
            if webbrowser.open(f"file://{temp_path}"):
                self.add_result("已成功在系统浏览器中开启图谱展示。")
            else:
                self.add_result(f"[!] 无法自动开启浏览器，请手动访问: file://{temp_path}")
        except Exception as e:
            self.error(f"图谱生成或展示失败: {e}")

        self.finalize(success=True)

if __name__ == "__main__":
    GraphScript().run()
