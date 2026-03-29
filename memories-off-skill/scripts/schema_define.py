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
                # 键名强制小写以保持规范一致性
                metadata[key.strip().lower()] = val.strip()
        return metadata

    @staticmethod
    def serialize(metadata: Dict[str, str]) -> str:
        """
        将元数据字典序列化为标准 YAML Frontmatter。
        """
        lines = ["---"]
        # 按照特定顺序排列（可选，但有助于美观）
        # 优先排列 entity type, date created, date modified 等核心字段
        core_keys = ["entity type", "date created", "date modified", "aliases"]
        seen_keys = set()
        
        for k in core_keys:
            if k in metadata:
                lines.append(f"{k}: {metadata[k]}")
                seen_keys.add(k)
        
        for k, v in sorted(metadata.items()):
            if k not in seen_keys:
                lines.append(f"{k}: {v}")
        
        lines.append("---\n")
        return "\n".join(lines)

    @staticmethod
    def split_content(content: str) -> tuple[Dict[str, str], str]:
        """
        将完整内容分离为元数据字典和正文部分。
        """
        metadata = MetadataParser.parse(content)
        body = MetadataParser.FRONTMATTER_PATTERN.sub("", content).strip()
        return metadata, body

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
