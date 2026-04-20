import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from .schema_define import LibraryContext

class CustomArgumentParser(argparse.ArgumentParser):
    """
    定制化参数解析器，在保留标准错误提示的基础上，自动输出符合 memocli-result 协议的错误报告。
    """
    def error(self, message):
        # 1. 信号: 输出到 stderr (极简摘要，满足标准监控)
        sys.stderr.write(f"error: {message}\n(See stdout XML for full details)\n")

        # 2. 上下文: 构造符合新协议的 XML 错误报告 (输出到 stdout，包含全量纠错信息)
        subcommand = self.prog.split()[-1] if " " in self.prog else self.prog
        full_cmd = " ".join(sys.argv)
        if self.is_memo_cli:
             # 还原成 memocli 风格的命令，移除内部参数 --memo-cli-call
             args = [a for a in sys.argv[1:] if a != "--memo-cli-call"]
             full_cmd = f"memocli {subcommand} " + " ".join(args)

        print(f'<memocli-result subcommand="{subcommand}" reason="none" result="failed">')
        print(f"  <source-sh>{full_cmd}</source-sh>")
        print("  <content>参数验证失败，指令未执行。</content>")
        print(f"  <error-detail>")
        print(f"原因: {message}\n")
        print(f"{self.prog} 的用法帮助供参考：")
        self.print_help()
        print("  </error-detail>")
        print("</memocli-result>")
        
        sys.exit(2)

class ScriptBase:
    """
    Agent Skill 脚本基类，提供模型优先的统一输出格式。
    """
    def __init__(self, action_name: str, description: str, example: str = "", group_name: str = "未分类", enum_details: Dict[str, Dict[str, str]] = None):
        self.action_name = action_name
        self.description = description
        self.example = example
        self.group_name = group_name
        self.enum_details = enum_details or {}
        self.is_memo_cli = "--memo-cli-call" in sys.argv
        self.result_content: List[str] = []
        self._check_info()
        self.parser = self._init_parser()
        self.args: Any = None
        self.ctx: Optional[LibraryContext] = None

    def _check_info(self):
        """处理 --memo-cli-info 协议"""
        if "--memo-cli-info" in sys.argv:
            print(f"Description: {self.description}")
            print(f"Group: {self.group_name}")
            if self.example:
                print(f"Example: {self.example}")
            if self.enum_details:
                for param, choices in self.enum_details.items():
                    print(f"Enum ({param}):")
                    for choice, desc in choices.items():
                        print(f"  - {choice}: {desc}")
            sys.exit(0)

    def _init_parser(self) -> CustomArgumentParser:
        # 子命令展示时统一用中划线
        display_name = self.action_name.replace("_", "-")
        prog = f"memocli {display_name}" if self.is_memo_cli else None
        
        # 构造增强后的 description
        full_desc = self.description
        if self.enum_details:
            full_desc += "\n\nEnum Details:"
            for param, choices in self.enum_details.items():
                full_desc += f"\n  {param}:"
                for choice, desc in choices.items():
                    full_desc += f"\n    - {choice:<12} : {desc}"

        parser = CustomArgumentParser(
            prog=prog,
            description=full_desc,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=f"Example:\n  {self.example}" if self.example else None,
            add_help=True
        )
        parser.is_memo_cli = self.is_memo_cli # 注入属性供 error() 使用
        parser.add_argument("--memo-cli-call", action="store_true", help=argparse.SUPPRESS)
        parser.add_argument("-p", "--path", required=True, help="知识库根目录路径。")
        parser.add_argument("-r", "--reason", default="none", help="执行此操作的理由（用于审计）。")
        return parser

    def add_result(self, message: str):
        """向执行结果中添加一行人类可读的信息"""
        self.result_content.append(message)

    def log(self, message: str):
        """记录一条执行日志（目前映射到 add_result 以保持兼容）"""
        self.add_result(f"[*] {message}")

    def error(self, message: str, instruction: str = ""):
        """记录业务逻辑错误并立即结束执行"""
        self.finalize(success=False, error_msg=message, instruction=instruction)
        sys.exit(1)

    def finalize(self, success: bool = True, error_msg: Optional[str] = None, instruction: str = ""):
        """输出最终的统一 XML 报告"""
        status = "success" if success else "failed"
        reason = getattr(self.args, "reason", "none") if self.args else "none"
        subcommand = self.action_name.replace("_", "-")
        
        # 构造原始指令字符串 (尽可能还原 memocli 风格)
        full_cmd = " ".join(sys.argv)
        if "memocli" not in full_cmd and self.is_memo_cli:
             full_cmd = f"memocli {subcommand} " + " ".join([a for a in sys.argv[1:] if a != "--memo-cli-call"])

        print(f'<memocli-result subcommand="{subcommand}" reason="{reason}" result="{status}">')
        print(f"  <source-sh>{full_cmd}</source-sh>")
        
        # 输出执行结果
        print("  <content>")
        for line in self.result_content:
            # 简单的 XML 转义
            safe_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            print(f"    {safe_line}")
        print("  </content>")
        
        # 错误详情
        if not success:
            print("  <error-detail>")
            if error_msg:
                print(f"    原因: {error_msg}")
            if instruction:
                print(f"    指令: {instruction}")
            print("  </error-detail>")
            
        print("</memocli-result>")

    def setup(self):
        """解析参数并初始化上下文"""
        self.args = self.parser.parse_args()
        root_path = Path(self.args.path).resolve()
        if not root_path.exists():
            self.finalize(success=False, error_msg=f"路径不存在: {root_path}")
            sys.exit(1)
        self.ctx = LibraryContext(root_path, root_path.name)

    def run(self):
        """子类需实现此方法"""
        raise NotImplementedError
