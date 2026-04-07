import os
import re
import sys
import argparse
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

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

class CustomArgumentParser(argparse.ArgumentParser):
    """
    定制化参数解析器，在保留标准错误提示的基础上，自动追加详细的用法帮助。
    """
    def error(self, message):
        # 1. 保留 argparse 标准的 usage 和 error 输出
        self.print_usage(sys.stderr)
        sys.stderr.write(f"{self.prog}: error: {message}\n")

        # 2. 追加详细帮助引导
        sys.stderr.write(f"\n{self.prog} 的详细用法参考：\n")
        self.print_help(sys.stderr)
        sys.stderr.write("\n")
        
        sys.exit(2)

class ScriptBase:
    """
    Agent Skill 脚本基类，提供统一的输出格式和参数处理。
    """
    def __init__(self, action_name: str, description: str, example: str = ""):
        self.action_name = action_name
        self.description = description
        self.example = example
        self.is_memo_cli = "--memo-cli-call" in sys.argv
        self.report_elements: List[str] = []
        self._check_info()
        self.parser = self._init_parser()
        self.args: Any = None
        self.ctx: Optional[LibraryContext] = None

    def _check_info(self):
        """处理 --memo-cli-info 协议"""
        if "--memo-cli-info" in sys.argv:
            print(f"Description: {self.description}")
            if self.example:
                print(f"Example: {self.example}")
            sys.exit(0)

    def _init_parser(self) -> CustomArgumentParser:
        prog = f"memocli {self.action_name}" if self.is_memo_cli else None
        parser = CustomArgumentParser(
            prog=prog,
            description=self.description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=f"Example:\n  {self.example}" if self.example else None,
            add_help=True
        )
        parser.add_argument("--memo-cli-call", action="store_true", help=argparse.SUPPRESS)
        parser.add_argument("-p", "--path", required=True, help="知识库根目录路径。")
        return parser

    def add_element(self, tag: str, content: str = "", **attrs):
        """向报告中添加一个 XML 元素"""
        attr_str = " ".join([f'{k}="{v}"' for k, v in attrs.items()])
        if attr_str:
            attr_str = " " + attr_str
        
        if content:
            # 简单的内容转义，防止破坏 XML 结构
            safe_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            self.report_elements.append(f"  <{tag}{attr_str}>{safe_content}</{tag}>")
        else:
            self.report_elements.append(f"  <{tag}{attr_str} />")

    def log(self, message: str, level: str = "info"):
        """记录一条日志"""
        self.add_element("log", message, level=level, time=datetime.now().strftime("%H:%M:%S"))

    def error(self, message: str, fatal: bool = True):
        """记录业务逻辑错误并根据需要退出"""
        self.add_element("error", message, fatal=str(fatal).lower())
        if fatal:
            self.finalize(success=False)
            sys.exit(1)

    def finalize(self, success: bool = True):
        """输出最终的 XML 报告并结束"""
        root_tag = f"{self.action_name}_report"
        print(f"<{root_tag} success=\"{str(success).lower()}\">")
        
        # 记录调用参数 (脱敏或精简)
        arg_attrs = {k: v for k, v in vars(self.args).items() if k != "memo_cli_call"}
        arg_attr_str = " ".join([f'{k}="{v}"' for k, v in arg_attrs.items()])
        print(f"  <args {arg_attr_str} />")
        
        for element in self.report_elements:
            print(element)
            
        print(f"</{root_tag}>")

    def setup(self):
        """解析参数并初始化上下文"""
        self.args = self.parser.parse_args()
        root_path = Path(self.args.path).resolve()
        if not root_path.exists():
            self.error(f"路径不存在: {root_path}")
        self.ctx = LibraryContext(root_path, root_path.name)

    def run(self):
        """子类需实现此方法"""
        raise NotImplementedError
