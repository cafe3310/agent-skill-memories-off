#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from utility.runtime import ScriptBase

class FindDocScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="find_doc_by_name",
            description="在配置的外部文档仓库 (External Document Repository) 中检索文档。仅检索文件名，不索引内容。",
            group_name="检索与加载 (Search & Loading)",
            example='memocli find-doc-by-name "计划"'
        )
        self.parser.add_argument("query", help="要搜索的文档名称关键字（模糊匹配文件名）。")

    def run(self):
        self.setup()
        ctx = self.ctx
        config = ctx.get_external_repo_config()

        if not config.root_path:
            self.error("未在 meta.md 中配置外部文档仓库根目录 (ext_doc_repo_root)。")

        if not config.root_path.exists():
            self.error(f"配置的外部文档仓库路径不存在: {config.root_path}")

        query = self.args.query.lower()
        matches = []

        # 遍历外部仓库
        for root, dirs, files in os.walk(config.root_path):
            # 排除目录
            dirs[:] = [d for d in dirs if d not in config.exclude_dirs]
            
            for file in files:
                file_path = Path(root) / file
                
                # 检查扩展名
                if file_path.suffix not in config.extensions:
                    continue
                
                # 模糊匹配文件名 (包含后缀)
                if query in file.lower():
                    rel_path = file_path.relative_to(config.root_path)
                    try:
                        # 获取文件大小 (Bytes)
                        size = os.path.getsize(file_path)
                    except Exception:
                        size = 0
                        
                    matches.append({
                        "name": file,
                        "rel_path": str(rel_path),
                        "size": size
                    })

        if not matches:
            self.add_result(f"在外部仓库中未找到匹配 '{self.args.query}' 的文档。")
            self.finalize(success=True)
            return

        self.add_result(f"找到 {len(matches)} 个匹配文档:")
        for m in sorted(matches, key=lambda x: x["rel_path"]):
            self.add_result(f"  - {m['rel_path']} ({m['size']} bytes)")
        
        self.finalize(success=True)

if __name__ == "__main__":
    FindDocScript().run()
