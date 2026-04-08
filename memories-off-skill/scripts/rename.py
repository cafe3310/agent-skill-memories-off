#!/usr/bin/env python3
import sys
import re
from pathlib import Path
from schema_define import ScriptBase, MetadataParser

class RenameScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="rename",
            description="重命名实体文件并自动更新全库范围内的 WikiLinks 引用和语义关系。",
            example="memocli rename --path . --old 旧名称 --new 新名称 --reason \"修正命名\""
        )
        self.parser.add_argument("--old", required=True, help="原实体名称（不含 .md）。")
        self.parser.add_argument("--new", required=True, help="新实体名称（不含 .md）。")

    def run(self):
        self.setup()
        
        if self.args.reason == "none":
            self.error("必须提供重命名理由 (--reason/-r)。", instruction="请补充理由后重试。")

        ctx = self.ctx
        old_name = self.args.old
        new_name = MetadataParser.normalize_name(self.args.new)
        
        old_file = ctx.entities_path / f"{old_name}.md"
        new_file = ctx.entities_path / f"{new_name}.md"
        
        if not old_file.exists():
            self.error(f"源文件不存在: {old_name}", instruction=f"请确认实体名称是否正确。")
        
        if new_file.exists():
            self.error(f"目标文件已存在: {new_name}", instruction="请选择一个不同的新名称。")

        self.add_result(f"正在重命名实体: {old_name} -> {new_name}")

        # 1. 执行 Git MV (如果是在 Git 仓库中)
        if ctx.is_git_repo():
            ctx.run_git(["mv", str(old_file), str(new_file)])
        else:
            old_file.rename(new_file)
        
        # 2. 全局搜索并替换引用
        wikilink_pattern = re.compile(re.escape(f"[[{old_name}]]"))
        relation_pattern = re.compile(rf"(relation as .*?:\s*)(.*)")

        affected_files = []
        files_to_scan = list(ctx.entities_path.glob("*.md")) + [ctx.meta_path]
        
        for md_file in files_to_scan:
            if not md_file.exists() or md_file == new_file: # 跳过已重命名的文件自身
                continue
            
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                changed = False
                new_lines = []
                for line in lines:
                    # 替换 WikiLinks
                    if f"[[{old_name}]]" in line:
                        line = wikilink_pattern.sub(f"[[{new_name}]]", line)
                        changed = True
                    
                    # 替换 Relation as
                    if "relation as" in line:
                        match = relation_pattern.match(line)
                        if match:
                            prefix, targets = match.groups()
                            target_list = [t.strip() for t in targets.split(",")]
                            if old_name in target_list:
                                new_target_list = [new_name if t == old_name else t for t in target_list]
                                line = f"{prefix}{', '.join(new_target_list)}\n"
                                changed = True
                    
                    new_lines.append(line)
                
                if changed:
                    with open(md_file, "w", encoding="utf-8") as f:
                        f.writelines(new_lines)
                    if ctx.is_git_repo():
                        ctx.run_git(["add", str(md_file)])
                    affected_files.append(md_file.name)
            except Exception as e:
                self.add_result(f"[!] 处理文件 {md_file.name} 时出错: {e}")

        # 3. 提交变更 (如果是在 Git 仓库中)
        if ctx.is_git_repo():
            commit_msg = f"rename {old_name} -> {new_name}: {self.args.reason}"
            ctx.run_git(["commit", "-m", commit_msg])
            self.add_result(f"已提交 Git 变更。")

        self.add_result(f"重命名成功！受影响的引用文件数: {len(affected_files)}")
        for f in affected_files:
            self.add_result(f"  - {f}")

        self.finalize(success=True)

if __name__ == "__main__":
    RenameScript().run()
