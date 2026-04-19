#!/usr/bin/env python3
import sys
import re
import os
from pathlib import Path
from datetime import datetime
from utility.runtime import ScriptBase
from utility.schema_define import MetadataParser, UpdateBlockManager

class DoctorScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="doctor",
            description="诊断并修复知识库中的常见问题（规范化、孤立引用等）。若不加 --fix 参数，则仅列出问题（Dry-run）。",
            example='memocli doctor --normalize-name --fix --reason "标准化命名"'
        )
        self.parser.add_argument("--normalize-name", action="store_true", help="检查并修复实体文件名、WikiLinks和关系目标的标准化问题。")
        self.parser.add_argument("--audit", action="store_true", help="检查并修复孤立关系、损坏的 WikiLink 以及 Schema 冲突。")
        self.parser.add_argument("--fix-update-blocks", action="store_true", help="检查并修复老旧的缓冲更新块，交互式地补齐时间戳和理由。")
        self.parser.add_argument("--fix", action="store_true", help="执行修复模式。自动更正发现的问题。")

    def run(self):
        self.setup()
        
        if not (self.args.normalize_name or self.args.audit or self.args.fix_update_blocks):
            self.error("必须至少指定一个诊断规则（例如 --normalize-name, --audit, 或 --fix-update-blocks）。")

        if self.args.fix and self.args.reason == "none":
            self.error("执行修复模式时必须提供理由 (--reason/-r)。")

        ctx = self.ctx
        if not ctx.entities_path.exists():
            self.error("实体目录不存在。")

        entity_files = list(ctx.entities_path.glob("*.md"))
        issues = []
        fixed_count = 0
        
        mode_str = "修复" if self.args.fix else "诊断"
        self.add_result(f"正在对 {len(entity_files)} 个实体进行{mode_str}...")

        if self.args.normalize_name:
            fixed_count += self._run_normalize_name_pass(entity_files, issues, self.args.fix)
            # 如果重命名了文件，重新获取文件列表供下一个规则使用
            entity_files = list(ctx.entities_path.glob("*.md"))

        if self.args.audit:
            fixed_count += self._run_audit_pass(entity_files, issues, self.args.fix)

        if self.args.fix_update_blocks:
            fixed_count += self._run_fix_update_blocks_pass(entity_files, issues, self.args.fix)

        if not issues:
            self.add_result(f"  [OK] 未发现需要处理的问题。")
        else:
            self.add_result(f"共发现 {len(issues)} 个问题点:")
            for issue in issues[:50]:
                self.add_result(f"  - {issue}")
            if len(issues) > 50:
                self.add_result(f"  ... (还有 {len(issues) - 50} 个问题被省略)")

        if self.args.fix and fixed_count > 0:
            if ctx.is_git_repo():
                commit_msg = f"fix(doctor): {self.args.reason}"
                try:
                    ctx.run_git(["add", "entities/"])
                    ctx.run_git(["commit", "-m", commit_msg])
                    self.add_result(f"\n[SUCCESS] 已应用修复并提交 {fixed_count} 个文件的变更至 Git。")
                except Exception as e:
                    self.add_result(f"\n[WARN] 修复已完成但 Git 提交失败: {e}")
            else:
                self.add_result(f"\n[SUCCESS] 已应用 {fixed_count} 个文件的修复 (非 Git 环境)。")
        elif not self.args.fix and issues:
            self.add_result("\n[INFO] 当前为诊断模式，未修改任何文件。如需修复，请添加 --fix 和 --reason 参数。")

        self.finalize(success=True)

    def _run_normalize_name_pass(self, entity_files, issues, do_fix):
        """执行命名标准化检查和修复"""
        rename_map = {}
        fixed_files = set()
        
        # Step 1: 检查文件名
        for file_path in entity_files:
            original_stem = file_path.stem
            normalized_stem = MetadataParser.normalize_name(original_stem)
            
            if original_stem != normalized_stem:
                issues.append(f"[文件命名] {original_stem}.md 需标准化为 {normalized_stem}.md")
                rename_map[original_stem] = normalized_stem
                if do_fix:
                    new_path = file_path.with_name(f"{normalized_stem}.md")
                    if not new_path.exists():
                        os.rename(file_path, new_path)
                    fixed_files.add(original_stem)

        # 重新获取文件列表以便处理内容
        current_entity_files = list(self.ctx.entities_path.glob("*.md")) if do_fix else entity_files
        
        # Step 2: 扫描文件内容（元数据与正文）
        for file_path in current_entity_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
                
            metadata, body = MetadataParser.split_content(content)
            content_changed = False
            
            # 1. 检查关系目标
            rel_keys = [k for k in metadata.keys() if k.startswith("relation as ")]
            for rk in rel_keys:
                targets_raw = metadata[rk]
                targets = [t.strip() for t in targets_raw.split(",") if t.strip()]
                normalized_targets = []
                for t in targets:
                    norm_t = MetadataParser.normalize_name(t)
                    if norm_t != t:
                        issues.append(f"[{file_path.name}] 关系目标需标准化: {t} -> {norm_t}")
                        content_changed = True
                    normalized_targets.append(norm_t)
                if do_fix:
                    metadata[rk] = ", ".join(normalized_targets)

            # 2. 检查别名并处理重命名的回退记录
            if do_fix and "aliases" in metadata or (not do_fix and "aliases" in metadata):
                aliases_raw = metadata.get("aliases", "")
                aliases = [a.strip() for a in aliases_raw.split(",") if a.strip()]
                
                # 如果文件被重命名了，原名字应加入别名
                original_stem = next((k for k, v in rename_map.items() if v == file_path.stem), None)
                if original_stem and original_stem not in aliases:
                    issues.append(f"[{file_path.name}] 需自动添加原名作为别名: {original_stem}")
                    if do_fix:
                        aliases.append(original_stem)
                        content_changed = True
                
                # 去重
                clean_aliases = []
                for a in aliases:
                    if a not in clean_aliases:
                        clean_aliases.append(a)
                
                new_aliases_str = ", ".join(clean_aliases)
                if new_aliases_str != aliases_raw:
                    if do_fix:
                        metadata["aliases"] = new_aliases_str
                        content_changed = True

            # 3. 检查正文中的 WikiLinks
            new_body = MetadataParser.normalize_wikilinks(body)
            if new_body != body:
                issues.append(f"[{file_path.name}] 正文中的 WikiLinks 需标准化")
                content_changed = True

            if content_changed and do_fix:
                new_content = MetadataParser.serialize(metadata) + "\n" + new_body
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                fixed_files.add(file_path.stem)
                
        return len(fixed_files)

    def _run_audit_pass(self, entity_files, issues, do_fix):
        """执行知识库引用和格式健康审计"""
        entity_names = {f.stem for f in entity_files}
        fixed_files = set()
        
        wikilink_pattern = re.compile(r"\[\[(.*?)\]\]")
        relation_pattern = re.compile(r"relation as (.*?):\s*(.*)")

        for file_path in entity_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except Exception:
                continue
            
            new_lines = []
            file_changed = False
            
            for idx, line in enumerate(lines):
                line_no = idx + 1
                
                # 1. 审计 Relation 引用
                rel_match = relation_pattern.search(line)
                if rel_match:
                    predicate, targets = rel_match.groups()
                    target_list = [t.strip() for t in targets.split(",")]
                    valid_targets = []
                    for t in target_list:
                        # 关系目标通常已经被标准化过，直接检查文件是否存在
                        if t not in entity_names:
                            issues.append(f"[{file_path.name}:{line_no}] Orphan Relation 指向不存在的实体: {t}")
                        else:
                            valid_targets.append(t)
                    
                    if do_fix and len(valid_targets) != len(target_list):
                        if not valid_targets:
                            line = "" # 移除整行
                        else:
                            line = f"relation as {predicate}: {', '.join(valid_targets)}\n"
                        file_changed = True

                # 2. 审计 WikiLinks
                links = wikilink_pattern.findall(line)
                for link in links:
                    # 处理 [[Entity|Alias]]
                    link_name = link.split("|")[0].strip()
                    # 检查时，使用标准化后的名字去找是否存在
                    norm_link = MetadataParser.normalize_name(link_name)
                    if norm_link not in entity_names:
                        issues.append(f"[{file_path.name}:{line_no}] Broken Link 无效的 WikiLink: [[{link}]]")
                        if do_fix and " (broken)" not in line:
                            line = line.replace(f"[[{link}]]", f"[[{link}]] (broken)")
                            file_changed = True

                new_lines.append(line)

            # 3. 审计 Entity Type (单一值校验)
            for idx, line in enumerate(lines[:10]):
                if "entity type:" in line and "," in line:
                    issues.append(f"[{file_path.name}:{idx+1}] Schema Violation: entity type 包含多个值（应为唯一）")
                    # 目前对 entity type 冲突只报不自动修，留待人工或专门工具

            if do_fix and file_changed:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                fixed_files.add(file_path.stem)
                
        return len(fixed_files)

    def _run_fix_update_blocks_pass(self, entity_files, issues, do_fix):
        """扫描并修复、补齐含有缺陷或使用旧格式的缓冲更新块"""
        fixed_files = set()
        
        loose_pattern = re.compile(
            r"<!-- UPDATE_BLOCK_START(?:|:\s*(.*?))\s*\|\s*reason:\s*(.*?)\s*-->\n(.*?)\n<!-- UPDATE_BLOCK_END(?:|:\s*(.*?))\s*-->",
            re.DOTALL
        )
        
        legacy_pattern = re.compile(
            r"---\s*\[UPDATE BLOCK\]\s*---\n(.*?)\n---\s*\[END OF UPDATE BLOCK\]\s*---",
            re.DOTALL
        )
        
        for file_path in entity_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            file_mtime = file_path.stat().st_mtime
            fallback_time_obj = datetime.fromtimestamp(file_mtime)
            
            content_changed = False
            new_content = content
            
            # 1. 处理极旧的 Legacy 格式
            legacy_matches = list(legacy_pattern.finditer(new_content))
            for i, match in enumerate(legacy_matches):
                issues.append(f"[{file_path.name}] 发现极其古老的更新块 (Legacy Format)")
                if do_fix:
                    block_content = match.group(1)
                    # 每遇到一个缺少时间的块，时间 +1s
                    block_time = (fallback_time_obj + __import__("datetime").timedelta(seconds=i)).strftime("%Y-%m-%d %H:%M:%S")
                    reason = "迁移补充"
                    
                    new_block = UpdateBlockManager.create_block(block_content, reason, block_time)
                    print(f"\n[{file_path.name}] 拟修复极其古老的更新块:")
                    print("--- 原内容 ---")
                    print(match.group(0).strip())
                    print("--- 修复后 ---")
                    print(new_block.strip())
                    
                    ans = input("确认修复此块? (y/N): ")
                    if ans.lower() == 'y':
                        new_content = new_content.replace(match.group(0), new_block)
                        content_changed = True
                        
            # 2. 处理带有标准 HTML 注释但格式可能存在缺陷的格式
            loose_matches = list(loose_pattern.finditer(new_content))
            for i, match in enumerate(loose_matches):
                t_start = match.group(1)
                reason = match.group(2)
                block_content = match.group(3)
                t_end = match.group(4)
                
                needs_fix = False
                issue_msgs = []
                
                if not t_start:
                    issue_msgs.append("START 缺少时间戳")
                    needs_fix = True
                if not t_end:
                    issue_msgs.append("END 缺少时间戳")
                    needs_fix = True
                if t_start and t_end and t_start != t_end:
                    issue_msgs.append("START 和 END 时间戳不一致")
                    needs_fix = True
                if not reason or reason.strip() == "":
                    issue_msgs.append("缺少 reason")
                    needs_fix = True
                    
                if needs_fix:
                    issues.append(f"[{file_path.name}] 更新块格式不合规: {', '.join(issue_msgs)}")
                    if do_fix:
                        # 确定时间戳
                        if t_start and "缺少时间戳" not in issue_msgs[0]:
                            final_time = t_start
                        else:
                            final_time = (fallback_time_obj + __import__("datetime").timedelta(seconds=i)).strftime("%Y-%m-%d %H:%M:%S")
                            
                        # 确定原因
                        final_reason = reason if reason and reason.strip() else "迁移补充"
                        
                        new_block = UpdateBlockManager.create_block(block_content, final_reason, final_time)
                        print(f"\n[{file_path.name}] 拟修复更新块缺陷 ({', '.join(issue_msgs)}):")
                        print("--- 原内容 ---")
                        print(match.group(0).strip())
                        print("--- 修复后 ---")
                        print(new_block.strip())
                        
                        ans = input("确认修复此块? (y/N): ")
                        if ans.lower() == 'y':
                            new_content = new_content.replace(match.group(0), new_block)
                            content_changed = True

            if content_changed and do_fix:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                fixed_files.add(file_path.stem)
                
        return len(fixed_files)

if __name__ == "__main__":
    DoctorScript().run()
