#!/usr/bin/env python3
import argparse
import sys
import os
import json
import re
import tempfile
import webbrowser
from pathlib import Path
from schema_define import LibraryContext, MetadataParser

# --- HTML 渲染模板 (Self-contained) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Memories-Off 3D 知识图谱</title>
    <style>
        body { margin: 0; background-color: #000; overflow: hidden; font-family: sans-serif; }
        #graph-container { width: 100vw; height: 100vh; }
        #info-panel {
            position: absolute; top: 10px; left: 10px;
            color: #ccc; background: rgba(0,0,0,0.6);
            padding: 10px; border-radius: 4px; pointer-events: none;
            font-size: 12px; border: 1px solid #333;
            z-index: 100;
        }
    </style>
    <!-- 核心依赖: 3d-force-graph (Vanilla JS 版，自带 Three.js) -->
    <script src="https://unpkg.com/3d-force-graph"></script>
</head>
<body>
    <div id="graph-container"></div>
    <div id="info-panel">
        <strong>Memories-Off 3D Gravity KG</strong><br/>
        左键: 旋转 | 右键: 平移 | 滚轮: 缩放<br/>
        点击节点: 聚焦中心
    </div>

    <script>
        // 由 Python 注入的数据
        const gData = {DATA_JSON};

        const elem = document.getElementById('graph-container');
        // 使用 3d-force-graph 的标准 API
        const Graph = ForceGraph3D()(elem)
            .graphData(gData)
            .nodeLabel(node => `${node.type}: ${node.display_name}`)
            .nodeAutoColorBy('type')
            .nodeVal(node => node.is_alias ? 2 : 10)
            .linkDirectionalArrowLength(3.5)
            .linkDirectionalArrowRelPos(1)
            .linkCurvature(0.25)
            .linkWidth(link => link.is_alias_link ? 0.5 : 1)
            .onNodeClick(node => {
                // 聚焦逻辑
                const distance = 60;
                const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z);
                Graph.cameraPosition(
                    { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }, // new pos
                    node, // lookAt ({x,y,z})
                    2000  // transition ms
                );
            });

        // --- 自定义物理力: 类型引力 (Type-Centric Force) ---
        Graph.d3Force('type-gravity', (alpha) => {
            const nodes = Graph.graphData().nodes;
            const typeCenters = {};
            
            // 1. 计算各类型质心
            const totals = {};
            nodes.forEach(n => {
                if (n.is_alias) return; // 别名不参与质心计算
                if (!totals[n.type]) totals[n.type] = { x: 0, y: 0, z: 0, count: 0 };
                totals[n.type].x += n.x;
                totals[n.type].y += n.y;
                totals[n.type].z += n.z;
                totals[n.type].count++;
            });
            
            Object.keys(totals).forEach(t => {
                typeCenters[t] = {
                    x: totals[t].x / totals[t].count,
                    y: totals[t].y / totals[t].count,
                    z: totals[t].z / totals[t].count
                };
            });

            // 2. 施加向心力
            nodes.forEach(n => {
                const center = typeCenters[n.type];
                if (center) {
                    n.vx += (center.x - n.x) * alpha * 0.08;
                    n.vy += (center.y - n.y) * alpha * 0.08;
                    n.vz += (center.z - n.z) * alpha * 0.08;
                }
            });
        });

        // 调整连线强度: 别名绑定极强
        Graph.d3Force('link')
            .strength(link => link.is_alias_link ? 1.0 : 0.2)
            .distance(link => link.is_alias_link ? 10 : 60);

    </script>
</body>
</html>
"""

class GraphExporter:
    WIKILINK_PATTERN = re.compile(r"\[\[(.*?)\]\]")

    def __init__(self, library_path: Path):
        self.ctx = LibraryContext(library_path, "Knowledge Graph")
        self.nodes = []
        self.links = []
        self.entity_map = {} # raw_name -> id

    def _get_id(self, entity_type: str, name: str) -> str:
        clean_name = self._clean_display_name(name)
        return f"{entity_type}-{clean_name}"

    def _clean_display_name(self, name: str) -> str:
        return re.sub(r"^[^-]+-", "", name)

    def export(self) -> str:
        if not self.ctx.entities_path.exists():
            return json.dumps({"nodes": [], "links": []})

        entity_files = list(self.ctx.entities_path.glob("*.md"))
        
        # 1. 第一遍扫描：收集所有实体节点
        for file in entity_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                    metadata, body = MetadataParser.split_content(content)
                    e_type = metadata.get("entity type", "未分类")
                    raw_name = metadata.get("name", file.stem)
                    display_name = self._clean_display_name(raw_name)
                    
                    e_id = self._get_id(e_type, display_name)
                    self.entity_map[raw_name] = e_id
                    self.entity_map[display_name] = e_id
                    
                    self.nodes.append({
                        "id": e_id,
                        "display_name": display_name,
                        "type": e_type,
                        "is_alias": False,
                        "val": 10
                    })
                    
                    # 处理别名
                    aliases = metadata.get("aliases", "")
                    if aliases:
                        alias_list = [a.strip() for a in aliases.split(",") if a.strip()]
                        for alias in alias_list:
                            alias_id = f"Alias-{alias}"
                            self.nodes.append({
                                "id": alias_id,
                                "display_name": alias,
                                "type": e_type,
                                "is_alias": True,
                                "val": 3
                            })
                            self.links.append({
                                "source": alias_id,
                                "target": e_id,
                                "predicate": "alias_of",
                                "is_alias_link": True
                            })
                            self.entity_map[alias] = e_id

            except Exception as e:
                print(f"[!] 无法解析实体 {file.name}: {e}", file=sys.stderr)

        # 2. 第二遍扫描：建立连接 (Relations & WikiLinks)
        for file in entity_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                    metadata, body = MetadataParser.split_content(content)
                    raw_name = metadata.get("name", file.stem)
                    source_id = self.entity_map.get(raw_name)
                    
                    if not source_id: continue

                    for key, val in metadata.items():
                        if key.startswith("relation"):
                            predicate = "related"
                            if " as " in key:
                                predicate = key.split(" as ", 1)[1]
                            
                            targets = re.findall(r"\[\[(.*?)\]\]", val)
                            if not targets:
                                targets = [val.strip()]
                            
                            for target_raw in targets:
                                target_id = self.entity_map.get(target_raw)
                                if target_id and target_id != source_id:
                                    self.links.append({
                                        "source": source_id,
                                        "target": target_id,
                                        "predicate": predicate,
                                        "is_alias_link": False
                                    })

                    wiki_targets = self.WIKILINK_PATTERN.findall(body)
                    for target_raw in wiki_targets:
                        target_id = self.entity_map.get(target_raw)
                        if target_id and target_id != source_id:
                            exists = any(l["source"] == source_id and l["target"] == target_id for l in self.links)
                            if not exists:
                                self.links.append({
                                    "source": source_id,
                                    "target": target_id,
                                    "predicate": "mentions",
                                    "is_alias_link": False
                                })
            except Exception:
                pass

        return json.dumps({"nodes": self.nodes, "links": self.links}, ensure_ascii=False)

def run_graph(path: str):
    root = Path(path).resolve()
    print(f"[*] 正在分析知识库并生成图谱: {root}")
    
    exporter = GraphExporter(root)
    graph_json = exporter.export()
    
    html_content = HTML_TEMPLATE.replace("{DATA_JSON}", graph_json)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tf:
        tf.write(html_content)
        temp_path = tf.name

    print(f"[*] 图谱已生成: {temp_path}")
    
    try:
        if webbrowser.open(f"file://{temp_path}"):
            print("[*] 已尝试在系统浏览器中开启图谱。")
        else:
            print(f"[!] 无法自动开启浏览器，请手动访问: file://{temp_path}")
    except Exception as e:
        print(f"[!] 开启浏览器失败: {e}")
        print(f"请手动访问: file://{temp_path}")

def main():
    if "--memo-cli-info" in sys.argv:
        print("Description: 生成并开启 3D 知识图谱展示 (基于引力场模型)。")
        print("Example: memocli graph --path .")
        sys.exit(0)

    is_memo_cli = "--memo-cli-call" in sys.argv
    action_name = "graph"

    parser = argparse.ArgumentParser(
        prog=f"memocli {action_name}" if is_memo_cli else None,
        description="生成并开启 Memories-Off 3D 知识图谱展示。",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--memo-cli-call", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("-p", "--path", required=True, help="知识库的根目录路径。")
    
    args = parser.parse_args()
    
    try:
        run_graph(args.path)
    except Exception as e:
        print(f"[ERROR] 生成图谱失败: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
