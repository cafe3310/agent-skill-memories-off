#!/usr/bin/env python3
import sys
from collections import Counter
from pathlib import Path
from utility.runtime import ScriptBase
from utility.schema_define import MetadataParser

class StatsScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="stats",
            description="获取 Memories-Off 知识库的全局资产统计报告。",
            group_name="系统与维护 (System & Maintenance)",
            example="memocli stats --path ."
        )
        self.parser.add_argument("-c", "--commits", type=int, default=5, help="显示最近的 Git 提交记录数量 (默认: 5)。")

    def run(self):
        self.setup()
        ctx = self.ctx
        
        self.add_result(f"正在分析知识库: {ctx.root_path}")
        
        # 1. 统计实体文件
        if not ctx.entities_path.exists():
            self.error(f"实体目录不存在: {ctx.entities_path}")
            return
        
        entity_files = list(ctx.entities_path.glob("*.md"))
        
        # 2. 解析元数据分布
        type_counts = Counter()
        for file in entity_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content = f.read()
                    metadata = MetadataParser.parse(content)
                    e_type = metadata.get("entity type", "未分类")
                    type_counts[e_type] += 1
            except Exception as e:
                self.add_result(f"[!] 无法解析文件 {file.name}: {e}")

        # 3. 读取近期 Git 动态
        commits_list = []
        if ctx.is_git_repo():
            raw_commits = ctx.run_git(["log", f"-n {self.args.commits}", "--pretty=format:%h | %as | %s"])
            if raw_commits and not raw_commits.startswith("Error:"):
                commits_list = raw_commits.splitlines()

        # 4. 构造内容
        self.add_result(f"总计实体数: {len(entity_files)}")
        self.add_result("\n[实体类型分布]")
        for t, count in type_counts.most_common():
            self.add_result(f"  - {t}: {count}")
        
        if commits_list:
            self.add_result(f"\n[最近 {self.args.commits} 条变更记录]")
            for c in commits_list:
                self.add_result(f"  {c}")

        # 5. 完成并输出
        self.finalize(success=True)

if __name__ == "__main__":
    StatsScript().run()
