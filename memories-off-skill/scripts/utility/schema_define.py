import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import subprocess

class UpdateBlockManager:
    """
    负责实体末尾「缓冲更新块 (Update Blocks)」的生命周期管理：创建、提取与清理。
    """
    BLOCK_PATTERN = re.compile(
        r"<!-- UPDATE_BLOCK_START: (.*?) \| reason: (.*?) -->\n(.*?)\n<!-- UPDATE_BLOCK_END -->",
        re.DOTALL
    )

    @staticmethod
    def create_block(content: str, reason: str) -> str:
        """
        生成一个标准化的、包含时间戳和操作理由的 HTML 注释包裹块。
        内部会自动对内容中的 WikiLinks 进行标准化。
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        safe_content = MetadataParser.normalize_wikilinks(content.strip())
        block = f"\n<!-- UPDATE_BLOCK_START: {now} | reason: {reason} -->\n"
        block += f"{safe_content}\n"
        block += "<!-- UPDATE_BLOCK_END -->\n"
        return block

    @staticmethod
    def extract_blocks(content: str) -> List[re.Match]:
        """
        从完整文本中提取所有更新块，返回正则 Match 对象的列表。
        Match.groups() = (timestamp, reason, block_content)
        """
        return list(UpdateBlockManager.BLOCK_PATTERN.finditer(content))

    @staticmethod
    def remove_blocks(content: str) -> str:
        """
        从完整文本中移除所有更新块并去首尾空白，通常用于获取「干净正文」。
        """
        return UpdateBlockManager.BLOCK_PATTERN.sub("", content).strip()

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

    @staticmethod
    def normalize_predicate(predicate: str) -> str:
        """
        按照规范标准化关系谓词 (Relation Predicate)。
        """
        # 转小写，非单词字符替换为 _
        predicate = predicate.lower().strip()
        predicate = re.sub(r"[^\w]+", "_", predicate)
        # 连续的 _ 合并
        predicate = re.sub(r"_+", "_", predicate).strip("_")
        return predicate

    @staticmethod
    def add_relation(metadata: Dict[str, str], predicate: str, target: str) -> bool:
        """
        向元数据中安全地添加一个关系目标，支持多值。
        """
        normalized_predicate = MetadataParser.normalize_predicate(predicate)
        rel_key = f"relation as {normalized_predicate}"
        target_name = MetadataParser.normalize_name(target)
        
        existing_val = metadata.get(rel_key, "").strip()
        if not existing_val:
            metadata[rel_key] = target_name
            return True
        
        # 解析现有值并检查是否存在
        targets = [t.strip() for t in existing_val.split(",") if t.strip()]
        normalized_targets = [MetadataParser.normalize_name(t) for t in targets]
        
        if target_name in normalized_targets:
            return False # 已存在，无需变更
        
        targets.append(target_name)
        metadata[rel_key] = ", ".join(targets)
        return True

    @staticmethod
    def add_alias(metadata: Dict[str, str], alias: str) -> bool:
        """
        向元数据中安全地添加一个别名。别名本身不被转为 slug，仅做去重和首尾去空格处理。
        """
        alias = alias.strip()
        if not alias:
            return False
            
        existing_val = metadata.get("aliases", "").strip()
        if not existing_val:
            metadata["aliases"] = alias
            return True
            
        aliases = [a.strip() for a in existing_val.split(",") if a.strip()]
        if alias in aliases:
            return False # 已存在
            
        aliases.append(alias)
        metadata["aliases"] = ", ".join(aliases)
        return True

    @staticmethod
    def normalize_wikilinks(text: str) -> str:
        """
        将正文中的 WikiLinks 自动标准化。
        [[Raw Name]] -> [[Normalized-Name|Raw Name]]
        [[Raw Name|Display]] -> [[Normalized-Name|Display]]
        若 Normalized-Name 等同于 Raw Name，则保持 [[Raw Name]] 即可。
        """
        def repl(match):
            inner = match.group(1)
            parts = inner.split("|", 1)
            target = parts[0].strip()
            display = parts[1].strip() if len(parts) > 1 else target
            
            norm_target = MetadataParser.normalize_name(target)
            if norm_target == display:
                return f"[[{norm_target}]]"
            return f"[[{norm_target}|{display}]]"
            
        # 匹配 [[...]]，排除跨行的复杂匹配
        return re.sub(r"\[\[(.*?)\]\]", repl, text)

    @staticmethod
    def remove_relation(metadata: Dict[str, str], predicate: str, target: str) -> bool:
        """
        从元数据中移除一个特定的关系目标。
        """
        normalized_predicate = MetadataParser.normalize_predicate(predicate)
        rel_key = f"relation as {normalized_predicate}"
        target_name = MetadataParser.normalize_name(target)
        
        existing_val = metadata.get(rel_key, "").strip()
        if not existing_val:
            return False
        
        targets = [t.strip() for t in existing_val.split(",") if t.strip()]
        new_targets = [t for t in targets if MetadataParser.normalize_name(t) != target_name]
        
        if len(new_targets) == len(targets):
            return False # 未找到匹配项
        
        if not new_targets:
            del metadata[rel_key]
        else:
            metadata[rel_key] = ", ".join(new_targets)
        return True
