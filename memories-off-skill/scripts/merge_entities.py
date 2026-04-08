#!/usr/bin/env python3
import sys
import re
from pathlib import Path
from schema_define import ScriptBase, MetadataParser

class MergeEntitiesScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="merge_entities",
            description="将多个源实体内容合并到目标实体，同步更新全局引用并删除源文件。",
            example="memocli merge-entities --path . --sources 人物-张三,人物-李四 --target 人物-王五 --reason \"重复录入\""
        )
        self.parser.add_argument("-s", "--sources", required=True, help="源实体名称列表，逗号分隔。")
        self.parser.add_argument("-t", "--target", required=True, help="目标实体名称。")

    def run(self):
        self.setup()
        
        if self.args.reason == "none":
            self.error("必须提供合并理由 (--reason/-r)。", instruction="请补充理由后重试。")

        ctx = self.ctx
        source_list = [MetadataParser.normalize_name(s.strip()) for s in self.args.sources.split(",") if s.strip()]
        target = MetadataParser.normalize_name(self.args.target)
        target_file = ctx.entities_path / f"{target}.md"

        if not target_file.exists():
            self.error(f"目标实体不存在: {target}", instruction="请先创建目标实体或核对名称。")

        self.add_result(f"准备将 {len(source_list)} 个实体合并至: {target}")

        # 1. 提取源实体内容
        merged_content_blocks = ["\n\n--- 合并内容开始 ---"]
        valid_sources = []
        
        for src_name in source_list:
            src_file = ctx.entities_path / f"{src_name}.md"
            if not src_file.exists():
                self.add_result(f"[WARN] 源实体 {src_name} 不存在，跳过。")
                continue
            
            try:
                with open(src_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 剔除 Frontmatter
                    _, body = MetadataParser.split_content(content)
                    merged_content_blocks.append(f"\n## 来自 {src_name} 的内容\n{body.strip()}")
                    valid_sources.append(src_name)
            except Exception as e:
                self.add_result(f"[!] 读取源实体 {src_name} 失败: {e}")

        if not valid_sources:
            self.error("没有有效的源实体可供合并。")

        # 2. 追加内容到目标实体
        try:
            with open(target_file, "a", encoding="utf-8") as f:
                f.write("\n".join(merged_content_blocks))
            self.add_result(f"[+] 内容已追加至 {target}.md")
        except Exception as e:
            self.error(f"内容追加失败: {e}")

        # 3. 全局重定向引用 (Source -> Target)
        self.add_result("正在更新全库引用...")
        all_md_files = list(ctx.entities_path.glob("*.md")) + [ctx.meta_path]
        affected_ref_count = 0
        
        for md_file in all_md_files:
            if not md_file.exists(): continue
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                changed = False
                new_lines = []
                for line in lines:
                    original_line = line
                    for src in valid_sources:
                        # WikiLink 替换
                        line = line.replace(f"[[{src}]]", f"[[{target}]]")
                        # Relation 替换 (简单字符串匹配)
                        if "relation as" in line:
                            line = line.replace(f": {src}", f": {target}").replace(f", {src}", f", {target}")
                    
                    if line != original_line:
                        changed = True
                    new_lines.append(line)
                    
                if changed:
                    with open(md_file, "w", encoding="utf-8") as f:
                        f.writelines(new_lines)
                    if ctx.is_git_repo():
                        ctx.run_git(["add", str(md_file)])
                    affected_ref_count += 1
            except:
                pass
        
        self.add_result(f"[+] 已更新 {affected_ref_count} 个引用文件。")

        # 4. 删除源文件
        for src in valid_sources:
            src_file = ctx.entities_path / f"{src}.md"
            try:
                if ctx.is_git_repo():
                    ctx.run_git(["rm", str(src_file)])
                else:
                    src_file.unlink()
            except:
                pass
        self.add_result(f"[+] 已删除源文件: {', '.join(valid_sources)}")

        # 5. 提交变更
        if ctx.is_git_repo():
            commit_msg = f"merge {', '.join(valid_sources)} into {target}: {self.args.reason}"
            try:
                ctx.run_git(["commit", "-m", commit_msg])
                self.add_result("已提交 Git 变更。")
            except Exception as e:
                self.add_result(f"[WARN] 自动提交失败: {e}")

        self.add_result("合并操作圆满完成！")
        self.finalize(success=True)

if __name__ == "__main__":
    MergeEntitiesScript().run()
