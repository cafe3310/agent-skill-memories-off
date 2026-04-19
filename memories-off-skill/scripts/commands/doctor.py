#!/usr/bin/env python3
import sys
import re
import os
from pathlib import Path
from utility.runtime import ScriptBase
from utility.schema_define import MetadataParser

class DoctorScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="doctor",
            description="诊断并修复知识库中的常见问题，特别是实体命名、WikiLink 规范和元数据格式的一致性。",
            example='memocli doctor --path . --normalize-name --reason "自动修复全库命名不规范问题"'
        )
        self.parser.add_argument("--normalize-name", action="store_true", help="强制全库实体文件名、WikiLinks、关系和别名标准化。")

    def run(self):
        self.setup()
        
        if self.args.normalize_name and self.args.reason == "none":
            self.error("执行批量修复模式时必须提供理由 (--reason/-r)。")

        ctx = self.ctx
        if not ctx.entities_path.exists():
            self.error("实体目录不存在。")

        entity_files = list(ctx.entities_path.glob("*.md"))
        
        issues = []
        fixed_count = 0
        self.add_result(f"正在对 {len(entity_files)} 个实体进行诊断...")

        if self.args.normalize_name:
            self._run_normalize_name_pass(entity_files, issues)

        if not issues:
            self.add_result("  [OK] 未发现需要修复的问题。")
        else:
            self.add_result(f"共发现/处理了 {len(issues)} 个问题点:")
            for issue in issues[:50]:
                self.add_result(f"  - {issue}")
            if len(issues) > 50:
                self.add_result(f"  ... (还有 {len(issues) - 50} 个问题被省略)")

        if self.args.normalize_name and issues:
            if ctx.is_git_repo():
                commit_msg = f"fix(doctor): {self.args.reason}"
                try:
                    ctx.run_git(["add", "entities/"])
                    ctx.run_git(["commit", "-m", commit_msg])
                    self.add_result(f"\n[SUCCESS] 已应用修复并提交至 Git。")
                except Exception as e:
                    self.add_result(f"\n[WARN] 修复已完成但 Git 提交失败: {e}")
            else:
                self.add_result(f"\n[SUCCESS] 已应用修复 (非 Git 环境)。")

        self.finalize(success=True)

    def _run_normalize_name_pass(self, entity_files, issues):
        """执行命名标准化检查和修复"""
        # Step 1: 重命名不符合规范的文件名，并记录映射
        rename_map = {}
        for file_path in entity_files:
            original_stem = file_path.stem
            normalized_stem = MetadataParser.normalize_name(original_stem)
            
            if original_stem != normalized_stem:
                issues.append(f"[文件重命名] {original_stem}.md -> {normalized_stem}.md")
                new_path = file_path.with_name(f"{normalized_stem}.md")
                if not new_path.exists():
                    os.rename(file_path, new_path)
                rename_map[original_stem] = normalized_stem
        
        # 重新获取文件列表
        entity_files = list(self.ctx.entities_path.glob("*.md"))
        
        # Step 2: 扫描并修复文件内容（元数据与正文）
        for file_path in entity_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
                
            metadata, body = MetadataParser.split_content(content)
            content_changed = False
            
            # 1. 修复关系目标
            rel_keys = [k for k in metadata.keys() if k.startswith("relation as ")]
            for rk in rel_keys:
                targets_raw = metadata[rk]
                targets = [t.strip() for t in targets_raw.split(",") if t.strip()]
                normalized_targets = []
                for t in targets:
                    norm_t = MetadataParser.normalize_name(t)
                    if norm_t != t:
                        issues.append(f"[{file_path.name}] 关系目标标准化: {t} -> {norm_t}")
                        content_changed = True
                    normalized_targets.append(norm_t)
                metadata[rk] = ", ".join(normalized_targets)

            # 2. 修复别名 (首尾去空，但别名本身不强求全小写或连字符)
            if "aliases" in metadata:
                aliases_raw = metadata["aliases"]
                aliases = [a.strip() for a in aliases_raw.split(",") if a.strip()]
                # 如果当前文件名被重命名过，且原始名字不在别名里，自动把原名字加入别名
                original_stem = next((k for k, v in rename_map.items() if v == file_path.stem), None)
                if original_stem and original_stem not in aliases:
                    aliases.append(original_stem)
                    issues.append(f"[{file_path.name}] 自动添加原名作为别名: {original_stem}")
                    content_changed = True
                
                clean_aliases = []
                for a in aliases:
                    if a not in clean_aliases:
                        clean_aliases.append(a)
                
                new_aliases_str = ", ".join(clean_aliases)
                if new_aliases_str != aliases_raw:
                    metadata["aliases"] = new_aliases_str
                    content_changed = True

            # 3. 修复正文中的 WikiLinks
            new_body = MetadataParser.normalize_wikilinks(body)
            if new_body != body:
                issues.append(f"[{file_path.name}] 已标准化正文中的 WikiLinks")
                content_changed = True

            if content_changed:
                new_content = MetadataParser.serialize(metadata) + "\n" + new_body
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

if __name__ == "__main__":
    DoctorScript().run()
