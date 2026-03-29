import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

@dataclass
class LibraryContext:
    """
    表示 memories-off 知识库的全局上下文。
    """
    root_path: Path
    library_name: str
    
    @property
    def entities_path(self) -> Path:
        return self.root_path / "entities"
    
    @property
    def meta_path(self) -> Path:
        return self.root_path / "meta.md"

    def is_git_repo(self) -> bool:
        return (self.root_path / ".git").is_dir()

    def run_git(self, args: List[str]) -> str:
        """
        在库根目录下执行 Git 命令。
        """
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.root_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr.strip()}"

@dataclass
class Entity:
    """
    表示单个知识实体。
    """
    name: str
    path: Path
    entity_type: str = "人物"  # 默认类型
    metadata: Dict[str, str] = field(default_factory=dict)
    body: str = ""

class MetadataParser:
    """
    用于解析和标准化实体文件中的 YAML Frontmatter。
    """
    FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

    @staticmethod
    def parse(content: str) -> Dict[str, str]:
        """
        简单的正则提取，满足 memories-off 规范（一级键值对，无需复杂嵌套）。
        """
        match = MetadataParser.FRONTMATTER_PATTERN.match(content)
        if not match:
            return {}
        
        yaml_text = match.group(1)
        metadata = {}
        for line in yaml_text.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                metadata[key.strip().lower()] = val.strip()
        return metadata

    @staticmethod
    def normalize_name(name: str) -> str:
        """
        按照规范标准化实体名称。
        """
        # 非法字符替换为单个 -
        name = re.sub(r"[^\w\u4e00-\u9fa5]+", "-", name)
        # 连续的 - 合并并移除首尾
        name = re.sub(r"-+", "-", name).strip("-")
        return name
