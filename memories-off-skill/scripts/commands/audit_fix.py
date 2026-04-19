#!/usr/bin/env python3
import sys
import re
from pathlib import Path
from utility.runtime import ScriptBase

class AuditFixScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="audit_fix",
            description="审计知识库一致性（WikiLinks, 实体命名）并可选修复。",
            example="memocli audit-fix --path . --fix --reason \"清理无效引用\""
        )
        self.parser.add_argument("--fix", action="store_true", help="启用修复模式，自动更正发现的问题。")

    def run(self):
        self.setup()
        
        if self.args.fix and self.args.reason == "none":
            self.error("启用修复模式时必须提供理由 (--reason/-r)。", instruction="请补充修复理由后重试。")

        ctx = self.ctx
        if not ctx.entities_path.exists():
            self.error("实体目录不存在。")

        entity_files = list(ctx.entities_path.glob("*.md"))
        entity_names = {f.stem for f in entity_files}
        
        issues = [] # 格式: (file_path, line_no, type, detail)
        self.add_result(f"正在对 {len(entity_files)} 个实体进行健康检查...")

        # 预编译正则
        wikilink_pattern = re.compile(r"\[\[(.*?)\]\]")
        relation_pattern = re.compile(r"relation as (.*?):\s*(.*)")

        fixed_count = 0
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
                        if t not in entity_names:
                            issues.append((file_path.name, line_no, "Orphan Relation", f"指向不存在的实体: {t}"))
                        else:
                            valid_targets.append(t)
                    
                    if self.args.fix and len(valid_targets) != len(target_list):
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
                    if link_name not in entity_names:
                        issues.append((file_path.name, line_no, "Broken Link", f"无效的 WikiLink: [[{link}]]"))
                        if self.args.fix:
                            # 仅在非修复过的行上进行简单标注
                            if " (broken)" not in line:
                                line = line.replace(f"[[{link}]]", f"[[{link}]] (broken)")
                                file_changed = True

                new_lines.append(line)

            # 3. 审计 Entity Type (单一值校验)
            for idx, line in enumerate(lines[:10]):
                if "entity type:" in line and "," in line:
                    issues.append((file_path.name, idx+1, "Schema Violation", "entity type 包含多个值（应为唯一）"))

            if self.args.fix and file_changed:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                if ctx.is_git_repo():
                    ctx.run_git(["add", str(file_path)])
                fixed_count += 1

        # 输出结果
        if not issues:
            self.add_result("  [OK] 未发现引用或规范问题。")
        else:
            self.add_result(f"发现 {len(issues)} 个问题:")
            for file, line, kind, detail in issues:
                self.add_result(f"  - [{kind}] {file}:{line} -> {detail}")

        # 如果执行了修复，提交
        if self.args.fix and fixed_count > 0:
            if ctx.is_git_repo():
                commit_msg = f"fix Global: {self.args.reason}"
                try:
                    ctx.run_git(["commit", "-m", commit_msg])
                    self.add_result(f"\n[SUCCESS] 已修复并提交 {fixed_count} 个文件。")
                except Exception as e:
                    self.add_result(f"\n[WARN] 修复已完成但 Git 提交失败: {e}")
            else:
                self.add_result(f"\n[SUCCESS] 已修复 {fixed_count} 个文件 (非 Git 环境)。")

        self.finalize(success=True)

if __name__ == "__main__":
    AuditFixScript().run()
