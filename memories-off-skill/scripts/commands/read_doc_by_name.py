#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from utility.runtime import ScriptBase

class ReadDocScript(ScriptBase):
    def __init__(self):
        super().__init__(
            action_name="read_doc_by_name",
            description="读取外部文档仓库 (External Document Repository) 中的指定文档。优先提供文件名；若存在同名文件，需提供包含部分路径的标识以消歧义。",
            group_name="检索与加载 (Search & Loading)",
            example='memocli read-doc-by-name "alpha.md"'
        )
        self.parser.add_argument("name", help="文档标识。优先使用文件名（如 alpha.md），仅在有重名时才需要提供相对路径（如 projects/alpha.md）。")

    def run(self):
        self.setup()
        ctx = self.ctx
        config = ctx.get_external_repo_config()

        if not config.root_path:
            self.error("未在 meta.md 中配置外部文档仓库根目录 (ext_doc_repo_root)。")

        if not config.root_path.exists():
            self.error(f"配置的外部文档仓库路径不存在: {config.root_path}")

        name = self.args.name
        target_path = config.root_path / name

        # 1. 尝试直接作为相对路径匹配
        if target_path.exists() and target_path.is_file():
            self._read_file(target_path)
            return

        # 2. 如果不存在，尝试在仓库中搜索同名文件
        matches = []
        for root, dirs, files in os.walk(config.root_path):
            dirs[:] = [d for d in dirs if d not in config.exclude_dirs]
            if name in files:
                matches.append(Path(root) / name)

        if not matches:
            # 尝试补充后缀名
            for ext in config.extensions:
                full_name = name + ext if not name.endswith(ext) else name
                for root, dirs, files in os.walk(config.root_path):
                    dirs[:] = [d for d in dirs if d not in config.exclude_dirs]
                    if full_name in files:
                        matches.append(Path(root) / full_name)
                if matches: break

        if not matches:
            self.error(f"在外部仓库中未找到文档: {name}")
        
        if len(matches) > 1:
            paths = [str(p.relative_to(config.root_path)) for p in matches]
            self.error(f"找到多个同名文档，请提供更精确的相对路径:\n  - " + "\n  - ".join(paths))

        self._read_file(matches[0])

    def _read_file(self, path: Path):
        try:
            content = path.read_text(encoding="utf-8")
            self.add_result(f"--- DOCUMENT START: {path.name} ---")
            self.add_result(content)
            self.add_result(f"--- DOCUMENT END: {path.name} ---")
            self.finalize(success=True)
        except Exception as e:
            self.error(f"读取文件失败: {e}")

if __name__ == "__main__":
    ReadDocScript().run()