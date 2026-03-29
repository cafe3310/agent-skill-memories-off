# 关联定义: Relation Types

本文档定义了 `memory-skill` 中实体间显式语义关系的表示方式及处理规则。

---

## 1. 显式关系表示 (Explicit Relations)

显式关系通过实体的 Front Matter 进行定义，具有强语义特征，可供 Agent 直接检索和推理。

### 1.1 `relation as` 前缀
- **职能**: 表示“当前实体”与“目标实体”之间存在某种特定类型的关系。
- **格式**: `relation as [谓词]: [目标实体名称]`。
- **谓词 (Predicate)**: 表示关系的性质（如 `member of`, `authored by`, `dependent on`）。
- **示例**:
  ```yaml
  ---
  entity type: Person
  relation as member of: Ant Group
  relation as reported to: Zhang San
  ---
  ```

## 2. 关系方向 (Relation Direction)

- **Outgoing (出站)**: 从当前实体指向目标实体的关系。存储在当前实体的 Front Matter 中。
- **Incoming (入站)**: 从其他实体指向当前实体的关系。通过扫描所有实体获取。
- **Both (双向)**: 以上两者之和。

## 3. 谓词规范 (Predicate Conventions)

为提高知识图谱的互操作性，建议使用以下通用谓词：
- **层级关系**: `is a` (分类), `part of` (归属), `child of` (继承)。
- **归属关系**: `owned by` (所属), `member of` (成员)。
- **时序/依赖**: `dependent on` (依赖), `preceded by` (前置)。
- **人物角色**: `authored by` (作者), `assigned to` (指派)。

## 4. 自动维护 (Automated Maintenance)

- **唯一性**: 每个谓词在单个实体中通常对应一个目标，除非特定业务场景需要列表形式。
- **重命名同步**: 当实体被重命名时，系统应自动扫描所有相关的 `relation as` 条目并更新目标实体名称。
- **清理逻辑**: 对应目标实体被删除（trash）后，相关的关系条目应标记为“失效”或进行回收清理。

## 5. 推理能力 (Inference)

Agent 在检索时应能基于关系链进行简单推理：
- 如果 `A relation as member of B` 且 `B relation as part of C`，则可以推断 `A` 与 `C` 存在间接关联。
