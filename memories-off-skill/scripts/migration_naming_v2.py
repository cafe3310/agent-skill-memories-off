#!/usr/bin/env python3
import sys
import re
from pathlib import Path
from datetime import datetime
from schema_define import ScriptBase, MetadataParser

class MigrationNamingV2Script(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="migration_naming_v2",
            description="[存量迁移] 将实体命名从 type-name.md 迁移至 name.md，并同步修复全量 WikiLinks 和元数据关系。",
            example="memocli migration-naming-v2 --dry-run"
        )
        self.parser.add_argument("--dry-run", action="store_true", help="预览变更，不实际修改文件。")
        self.rename_map = {} # OldName -> NewName
        self.all_entities = [] # List of (old_path, etype, suggested_new_name)

    def run(self):
        self.setup()
        ctx = self.ctx
        is_dry_run = self.args.dry_run

        if is_dry_run:
            self.add_result("--- DRY RUN MODE: 不会修改任何物理文件 ---")

        # 1. 扫描所有实体，识别需要更名的项
        for file in ctx.entities_path.glob("*.md"):
            try:
                content = file.read_text(encoding="utf-8")
                metadata, _ = MetadataParser.split_content(content)
                etype = metadata.get("entity type")
                old_name = file.stem
                
                if etype and old_name.startswith(f"{etype}-"):
                    suggested_name = old_name[len(etype)+1:]
                    if suggested_name:
                        self.all_entities.append((file, etype, suggested_name))
                    else:
                        self.add_result(f"[SKIP] 无法从 '{old_name}' 提取有效名称。")
            except Exception as e:
                self.add_result(f"[ERR] 读取 {file.name} 失败: {e}")

        # 2. 冲突检测与最终更名计划
        # 记录所有已经存在的“最终名称”（包含已经是新规的文件）
        existing_names = {f.stem: f for f in ctx.entities_path.glob("*.md")}
        
        # 预演更名
        final_rename_plan = [] # List of (old_path, final_new_name)
        
        for old_file, etype, suggested_name in self.all_entities:
            old_name = old_file.stem
            target_path = ctx.entities_path / f"{suggested_name}.md"
            
            # 冲突 A: 目标文件名已存在
            if suggested_name in existing_names:
                existing_file = existing_names[suggested_name]
                # 如果这个已存在的文件正是它自己（不应该发生，除非逻辑错），跳过
                if existing_file == old_file:
                    continue
                
                # 冲突处理：采取 name-type.md 兜底方案
                fallback_name = f"{suggested_name}-{etype}"
                self.add_result(f"[CONFLICT] '{suggested_name}' 已被占用 ({existing_file.name})。尝试兜底: {fallback_name}")
                
                # 二次冲突检查
                if fallback_name in existing_names:
                    self.add_result(f"[FATAL] 兜底名称 '{fallback_name}' 亦被占用，跳过此文件。")
                    continue
                
                final_new_name = fallback_name
            else:
                final_new_name = suggested_name
            
            final_rename_plan.append((old_file, final_new_name))
            self.rename_map[old_name] = final_new_name
            # 预占位，防止后续循环冲突
            existing_names[final_new_name] = target_path 

        if not final_rename_plan:
            self.add_result("未发现符合旧规范的实体。")
            self.finalize(success=True)
            return

        # 3. 执行更名 (Physical or Virtual)
        self.add_result(f"\n--- 准备更名 ({len(final_rename_plan)} 个文件) ---")
        for old_file, new_name in final_rename_plan:
            old_name = old_file.stem
            target_path = ctx.entities_path / f"{new_name}.md"
            self.add_result(f"Rename: {old_file.name} -> {new_name}.md")
            
            if not is_dry_run:
                try:
                    # 使用 git mv 保持历史
                    ctx.run_git(["mv", str(old_file), str(target_path)])
                except Exception as e:
                    self.add_result(f"[ERR] Git MV 失败: {e}")

        # 4. 全量内容修复 (WikiLinks & Relations)
        self.add_result("\n--- 准备修复内容链接与关系 ---")
        
        all_files = list(ctx.entities_path.glob("*.md"))
        if ctx.meta_path.exists():
            all_files.append(ctx.meta_path)
            
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        modified_count = 0

        for file in all_files:
            try:
                # 即使文件已更名，由于我们在内存中维护映射，逻辑依然有效
                # 逻辑注意：如果 file 已经执行了更名，但在 glob 时还是旧路径，读不到
                # 但由于我们全量重新扫描 entities 目录，且 all_files 是在更名后获取的，
                # 所以 file 路径是当前的真实路径。
                # 但在 dry_run 下，路径还是旧的。
                
                # 如果是 dry_run，我们需要调整路径读取（或者在 glob 之后、更名前获取 all_files）
                pass
            except: pass

        # 为处理 dry_run，我们再次根据最新状态构建列表
        if is_dry_run:
            current_all_files = list(ctx.entities_path.glob("*.md"))
            if ctx.meta_path.exists(): current_all_files.append(ctx.meta_path)
        else:
            current_all_files = list(ctx.entities_path.glob("*.md"))
            if ctx.meta_path.exists(): current_all_files.append(ctx.meta_path)

        for file_path in current_all_files:
            content = file_path.read_text(encoding="utf-8")
            original_content = content
            
            # A. 替换 WikiLinks
            # 使用正则精准匹配 [[name]] 或 [[name|display]]
            for old_name, new_name in self.rename_map.items():
                # 匹配 [[old_name]] 或 [[old_name|...]] 或 [[old_name#...]]
                # \b 不适合中文，直接匹配起始和特定分隔符
                pattern = r"\[\[(" + re.escape(old_name) + r")([\|#\]])"
                content = re.sub(pattern, r"[[" + new_name + r"\2", content)

            # B. 修复元数据关系
            metadata, body = MetadataParser.split_content(content)
            meta_changed = False
            for k, v in metadata.items():
                if k.startswith("relation as "):
                    targets = [t.strip() for t in v.split(",") if t.strip()]
                    new_targets = []
                    for t in targets:
                        norm_t = MetadataParser.normalize_name(t)
                        # 检查原始名或标准化后的名是否在映射中
                        # 映射表中的 Key 是 file.stem (已标准化)
                        if t in self.rename_map:
                             new_targets.append(self.rename_map[t])
                             meta_changed = True
                        elif norm_t in self.rename_map:
                             new_targets.append(self.rename_map[norm_t])
                             meta_changed = True
                        else:
                             new_targets.append(t)
                    
                    if meta_changed:
                        metadata[k] = ", ".join(new_targets)

            if meta_changed or content != original_content:
                modified_count += 1
                if not is_dry_run:
                    metadata["date modified"] = now
                    new_full_content = MetadataParser.serialize(metadata) + "\n" + body
                    file_path.write_text(new_full_content, encoding="utf-8")
                
                self.add_result(f"Fix: {file_path.name} (更新了链接或关系)")

        self.add_result(f"\n处理完成。修改文件数: {modified_count}")
        self.finalize(success=True)

if __name__ == "__main__":
    MigrationNamingV2Script().run()
