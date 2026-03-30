# 技术调研: react-force-graph 框架特性全景

## 1. 概述 (Overview)

基于用户希望为 `memories-off` 知识库添加「3D 引力知识图谱」展示的需求，本报告对 `react-force-graph` 系列组件进行了全维度的技术梳理。

该框架由 Vasco Asturiano (vasturiano) 开发，是一套专门用于可视化力导向图（Force-directed Graph）的 React 组件库。其底层深度整合了 **D3.js (d3-force)** 的物理引擎与 **Three.js / WebGL** 的渲染能力，是目前 React 生态中性能最强、定制化程度最高的关系图谱解决方案。

### 1.1 来源文档
- [官方在线示例 (react-force-graph)](https://vasturiano.github.io/react-force-graph)
- [GitHub 仓库 (vasturiano/react-force-graph)](https://github.com/vasturiano/react-force-graph)

---

## 2. 核心组件家族 (Component Suite)

该框架提供四个维度的展示组件，共享几乎一致的 API，方便跨平台迁移：
- **ForceGraph2D**: 基于 HTML5 Canvas 渲染，适合常规网页展示，交互极其流畅。
- **ForceGraph3D**: 基于 Three.js/WebGL 渲染，支持 3D 空间漫游，适合处理节点极多、关系极其复杂的知识网络。
- **ForceGraphVR**: 专为 WebVR/XR 优化，支持沉浸式探索。
- **ForceGraphAR**: 支持增强现实（AR）场景下的图谱展示。

---

## 3. 核心特性 (Key Features)

### 3.1 高性能渲染引擎
- **WebGL 加速**: 在 3D 模式下，即便面对上万个节点和连接，依然能保持 60fps 的帧率。
- **Canvas 渲染**: 2D 模式下避免了大量 DOM 节点导致的页面卡顿。

### 3.2 强大的 D3 物理仿真 (Physics Engine)
内置 `d3-force-3d` 引擎，支持实时模拟以下物理力：
- **引力 (Link Force)**: 节点间的连接力，决定了关系紧密度。
- **斥力 (Charge Force)**: 节点间的相互排斥，防止节点重叠，形成自组织的簇状结构。
- **碰撞力 (Collision)**: 确保节点间有物理间距。
- **中心重力 (Center Force)**: 将整个图谱拉向视野中心。

### 3.3 维度与布局模式 (Layouts)
- **3D 自由空间**: 节点在 XYZ 三维坐标中自动寻找平衡点。
- **DAG 模式 (Directed Acyclic Graph)**: 强制节点按层级排列（如 Top-Down, Radial, Z-Level 等），非常适合展示知识本体或家族树。
- **2D/3D 平滑切换**: 支持动态改变渲染维度。

---

## 4. 数据架构 (Data Schema)

该框架采用极简的 JSON 对象作为输入数据，结构如下：

```json
{
  "nodes": [
    { 
      "id": "unique_id",        // 必须：唯一标识符
      "name": "Node Label",     // 建议：显示名称
      "group": "category",      // 建议：用于自动着色
      "val": 10                 // 建议：权重，决定节点大小
    }
  ],
  "links": [
    {
      "source": "id_1",         // 必须：源节点 ID
      "target": "id_2",         // 必须：目标节点 ID
      "label": "predicate"      // 建议：关系名称
    }
  ]
}
```

---

## 5. 视觉与交互定制 (API & Customization)

### 5.1 节点定制 (Node Customization)
- **`nodeAutoColorBy`**: 传入字段名（如 `type`），框架会自动为不同类型的实体分配对比色。
- **`nodeThreeObject`**: **【高级功能】** 允许使用任意 Three.js 对象替代默认球体。例如，可以直接将 3D 文字、平面图标或复杂的 3D 模型作为节点。
- **`nodeVal`**: 可通过函数动态计算大小，如根据连接数（度数）调整。

### 5.2 链接定制 (Link Customization)
- **`linkDirectionalArrowLength`**: 在连接上添加方向箭头，明确知识图谱的谓词指向。
- **`linkDirectionalParticles`**: 在连接上生成流动的粒子，模拟数据流或激活状态，视觉效果极佳。
- **`linkCurvature`**: 设置连线的曲率，避免多重连线重叠。

### 5.3 交互逻辑 (Interaction)
- **点击聚焦 (`onNodeClick`)**: 点击节点时，相机平滑过渡到该节点位置并放大（Camera Zoom）。
- **悬停高亮 (`onNodeHover`)**: 悬停时高亮该节点及其一度关系，淡化无关部分。
- **节点拖拽**: 用户可以手动干预节点位置，物理引擎会实时响应重新计算平衡。
- **相机控制**: 内置 `Trackball`, `Orbit`, `Fly` 三种导航模式，支持缩放、旋转和平移。

---

## 6. 在 memories-off 中的应用潜力

1. **自动簇化**: 无需手动布局，脚本导出的知识实体会自动根据关系密度聚集成“领域块”。
2. **多重关系可视化**: 不同的显式关系（如 `part_of`, `works_at`）可以用不同颜色的连线或流动的粒子来区分。
3. **沉浸式审计**: 3D 环境让 Agent 或用户能一眼识破知识库中的“断头链接”（孤立节点）或逻辑环路。
4. **层级展示**: 开启 DAG 模式后，可以清晰展示笔记间的包含或衍生关系。

---

## 7. 结论 (Conclusion)

`react-force-graph` 是目前市面上最契合 `memories-off` 愿景的图形化工具。它不仅能提供极具冲击力的视觉效果，更重要的是其底层物理模型能够真实反映出个人知识网络中实体间的“重力”与“关联性”。

下一步建议：开发 `scripts/export_graph.py` 脚本，将现有的实体 Markdown 文件转化为上述 JSON 格式，并构建一个极简的 React 项目进行初步挂载渲染。
