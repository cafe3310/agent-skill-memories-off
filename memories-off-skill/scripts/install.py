#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def create_memocli():
    """
    创建并安装 memocli 包装器，支持自动发现子命令描述。
    """
    # 1. 获取路径
    script_dir = Path(__file__).parent.resolve()
    skill_root = script_dir.parent
    skill_md_path = skill_root / "SKILL.md"
    
    # 2. 自动获取子命令列表及其描述
    subcommands_info = []
    py_files = sorted(script_dir.glob("*.py"))
    
    for py_file in py_files:
        name = py_file.stem
        if name in ["install", "schema_define"] or name.startswith("_"):
            continue
            
        # 优先使用中划线展示
        display_name = name.replace("_", "-")
            
        try:
            # 运行脚本获取描述
            result = subprocess.run(
                [sys.executable, str(py_file), "--memo-cli-info"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                desc = "无说明"
                for line in result.stdout.splitlines():
                    if line.startswith("Description:"):
                        desc = line.replace("Description:", "").strip()
                        break
                # 关键修复：转义描述中的双引号，防止破坏 Bash 脚本语法
                safe_desc = desc.replace('"', '\\"')
                subcommands_info.append(f"    echo \"  {display_name:<20} - {safe_desc}\"")
            else:
                subcommands_info.append(f"    echo \"  {display_name:<20} - (无法获取描述)\"")
        except Exception:
            subcommands_info.append(f"    echo \"  {name:<20} - (加载失败)\"")

    subcommands_list_bash = "\n".join(subcommands_info)

    # 3. 确定安装路径
    target_bin = Path("/usr/local/bin")
    if not os.access(target_bin, os.W_OK):
        target_bin = Path.home() / ".local" / "bin"
        target_bin.mkdir(parents=True, exist_ok=True)
        
        path_env = os.environ.get("PATH", "")
        if str(target_bin) not in path_env:
            print(f"[WARN] {target_bin} 不在 PATH 中，请手动添加。")
    
    install_path = target_bin / "memocli"
    
    # 4. 构造 memocli 脚本内容 (使用 RAW 字符串或正确处理 $ 符号)
    # 在 Python 3.6+ f-string 中，$ 不需要转义，除非后面跟着 {
    content = f"""#!/bin/bash
# memocli: memories-off 技能的命令行包装器

SCRIPTS_DIR="{script_dir}"
PYTHON_CMD="python3"
SKILL_MD="{skill_md_path}"

ACTION=$1

# --- 1. 全局帮助处理 ---
if [[ "$ACTION" == "--help" ]] || [[ "$ACTION" == "-h" ]] || [[ "$ACTION" == "help" ]] || [[ -z "$ACTION" ]]; then
    echo "Memories-Off CLI (memocli) - An Agent Skill Wrapper"
    echo "Skill Root: $SKILL_MD"
    echo "----------------------------------------------------------------------"
    echo "用法: memocli <subcommand> [args...]"
    echo ""
    echo "参数简化说明:"
    echo "  如果在包含 meta.md 的目录下运行（知识库根目录），且未提供 --path 或 -p，"
    echo "  memocli 会自动追加 --path . 以简化操作。"
    echo ""
    echo "常用指令:"
    echo "  memocli --help              显示此全局帮助"
    echo "  memocli <subcommand> --help 显示特定子命令的详细用法"
    echo ""
    echo "可用子命令:"
{subcommands_list_bash}
    exit 0
fi

shift # 移除 subcommand 准备处理 args

# 兼容性处理：将中划线风格子命令映射到下划线脚本
RAW_ACTION=$ACTION
ACTION=$(echo "$RAW_ACTION" | tr '-' '_')

SCRIPT_PATH="$SCRIPTS_DIR/$ACTION.py"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "[ERROR] 子命令 '$ACTION' 不存在 (未找到文件: $SCRIPT_PATH)"
    exit 1
fi

# --- 2. 子命令帮助前缀处理 ---
IS_HELP=false
for arg in "$@"; do
    if [[ "$arg" == "--help" ]] || [[ "$arg" == "-h" ]]; then
        IS_HELP=true
        break
    fi
done

if [ "$IS_HELP" = true ]; then
    echo "[memocli] 正在获取子命令 '$ACTION' 的帮助信息..."
    echo "[memocli] 提示: 您可以直接运行 'memocli $ACTION <args...>' 来执行命令。"
    echo "----------------------------------------------------------------------"
    $PYTHON_CMD "$SCRIPT_PATH" --memo-cli-call --help
    exit 0
fi

# --- 3. 智能路径注入与转发 ---
HAS_PATH=false
for arg in "$@"; do
    if [[ "$arg" == "--path" ]] || [[ "$arg" == "-p" ]]; then
        HAS_PATH=true
        break
    fi
done

if [ "$HAS_PATH" = false ] && [ -f "meta.md" ]; then
    $PYTHON_CMD "$SCRIPT_PATH" --memo-cli-call --path . "$@"
else
    $PYTHON_CMD "$SCRIPT_PATH" --memo-cli-call "$@"
fi
"""

    # 5. 写入文件并赋予权限
    try:
        with open(install_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        os.chmod(install_path, 0o755)
        
        print(f"[SUCCESS] memocli 已安装到: {install_path}")
        print("您可以运行 'memocli --help' 查看详细说明。")
    except Exception as e:
        print(f"[ERROR] 安装失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_memocli()
