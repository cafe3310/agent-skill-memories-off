#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys
import subprocess
import glob
import io

def create_memocli():
    """
    创建并安装 memocli 包装器，支持自动发现子命令描述。
    兼顾 Python 2 环境，自动识别 Python 3。
    """
    # 1. 获取路径
    script_dir = os.path.abspath(os.path.dirname(__file__))
    skill_root = os.path.dirname(script_dir)
    skill_md_path = os.path.join(skill_root, "SKILL.md")
    
    # 0. Check python version to find a suitable python3 for subcommands
    python_cmd = sys.executable
    if sys.version_info < (3, 8):
        print("[INFO] 当前运行环境低于 Python 3.8，尝试寻找系统中的 Python 3 环境以解析子命令...")
        found_python3 = None
        for cmd in ["python3", "python3.11", "python3.10", "python3.9", "python3.8", "python"]:
            try:
                with open(os.devnull, 'w') as devnull:
                    if subprocess.call([cmd, "-c", "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)"], stdout=devnull, stderr=devnull) == 0:
                        found_python3 = cmd
                        break
            except Exception:
                pass
        if not found_python3:
            print("[WARN] 未能找到 Python 3.8+，子命令解析可能会失败。生成的 memocli 会在运行时重试。")
        else:
            print("[INFO] 找到 Python 3: " + found_python3)
            python_cmd = found_python3
    
    # 2. 自动获取子命令列表及其描述
    subcommands_info = []
    valid_subcommands = []
    # 扫描 commands 目录下的所有子命令
    commands_dir = os.path.join(script_dir, "commands")
    py_files = sorted(glob.glob(os.path.join(commands_dir, "*.py")))
    
    for py_file in py_files:
        name = os.path.splitext(os.path.basename(py_file))[0]
        if name.startswith("_"):
            continue
            
        # 优先使用中划线展示
        display_name = name.replace("_", "-")
        valid_subcommands.append(display_name)
            
        try:
            # 运行脚本获取描述和示例，设置 PYTHONPATH 以便脚本可以找到 utility.schema_define
            env = os.environ.copy()
            env["PYTHONPATH"] = script_dir + os.pathsep + env.get("PYTHONPATH", "")
            
            proc = subprocess.Popen(
                [python_cmd, py_file, "--memo-cli-info"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            stdout, stderr = proc.communicate()
            
            if sys.version_info[0] >= 3:
                stdout_str = stdout.decode('utf-8')
            else:
                stdout_str = stdout # string in py2
                
            if proc.returncode == 0:
                desc = "无说明"
                example = ""
                enum_info = []
                for line in stdout_str.splitlines():
                    if line.startswith("Description:"):
                        desc = line.replace("Description:", "").strip()
                    elif line.startswith("Example:"):
                        example = line.replace("Example:", "").strip()
                    elif line.startswith("Enum (") or line.strip().startswith("- "):
                        enum_info.append(line)
                
                # 转义描述和示例中的双引号，防止破坏 Bash 脚本语法
                safe_desc = desc.replace('"', '\"')
                subcommands_info.append('    echo "  %-20s - %s"' % (display_name, safe_desc))
                
                if example:
                    safe_example = example.replace('"', '\"')
                    subcommands_info.append('    echo "    Example: %s"' % safe_example)
                
                if enum_info:
                    for enum_line in enum_info:
                        safe_enum = enum_line.replace('"', '\"')
                        subcommands_info.append('    echo "    %s"' % safe_enum)
                
                subcommands_info.append('    echo ""')
            else:
                subcommands_info.append('    echo "  %-20s - (无法获取描述)"' % display_name)
        except Exception as e:
            subcommands_info.append('    echo "  %-20s - (加载失败: %s)"' % (name, str(e)))

    subcommands_list_bash = "\n".join(subcommands_info)
    subcommands_joined = ",".join(valid_subcommands)

    # 3. 确定安装路径
    target_bin = "/usr/local/bin"
    if not os.access(target_bin, os.W_OK):
        target_bin = os.path.join(os.path.expanduser("~"), ".local", "bin")
        if not os.path.exists(target_bin):
            os.makedirs(target_bin)

        path_env = os.environ.get("PATH", "")
        if target_bin not in path_env:
            print("[WARN] %s 不在 PATH 中，请手动添加。" % target_bin)

    install_path = os.path.join(target_bin, "memocli")

    # 4. 构造 memocli 脚本内容
    content = """#!/bin/bash
# memocli: memories-off 技能的命令行包装器

SCRIPTS_DIR="{script_dir}"
SKILL_MD="{skill_md_path}"
VALID_SUBS="{subcommands_joined}"

# 设置 PYTHONPATH 以便子命令可以找到 utility 模块
export PYTHONPATH="$SCRIPTS_DIR:$PYTHONPATH"

# --- 0. 环境检查: 寻找 Python 3 ---
PYTHON_CMD=""
for cmd in python3 python3.11 python3.10 python3.9 python3.8 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
        VER=$("$cmd" -c 'import sys; print(1 if sys.version_info >= (3,8) else 0)' 2>/dev/null)
        if [ "$VER" = "1" ]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "[错误] memocli 需要 Python 3.8+ 环境。未找到有效的 python 执行路径。"
    exit 1
fi

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

# 子命令现在存放在 commands 目录下
SCRIPT_PATH="$SCRIPTS_DIR/commands/$ACTION.py"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "[错误] 子命令 '$RAW_ACTION' 不存在。"
    
    # 模糊匹配建议
    SUGGESTION=$($PYTHON_CMD -c "import difflib; matches = difflib.get_close_matches('$RAW_ACTION', '$VALID_SUBS'.split(','), n=1, cutoff=0.5); print(matches[0]) if matches else print('')")
    
    if [ -n "$SUGGESTION" ]; then
        echo "您是不是想运行: memocli $SUGGESTION ?"
    fi
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
""".format(
        script_dir=script_dir,
        skill_md_path=skill_md_path,
        subcommands_joined=subcommands_joined,
        subcommands_list_bash=subcommands_list_bash
    )

    # 5. 写入文件并赋予权限
    try:
        # 兼容 Python 2 的 io.open 写入中文字符串
        if sys.version_info[0] < 3:
            content = content.decode('utf-8')
        with io.open(install_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        os.chmod(install_path, 0o755)
        
        print("[SUCCESS] memocli 已安装到: %s" % install_path)
        print("您可以运行 'memocli --help' 查看详细说明。")
    except Exception as e:
        print("[ERROR] 安装失败: %s" % e)
        sys.exit(1)

if __name__ == "__main__":
    create_memocli()
