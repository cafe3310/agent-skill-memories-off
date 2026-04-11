#!/bin/bash

# 辅助函数：让用户从存在的目录中选择，优先非空
choose_base_dir() {
    local label=$1
    shift
    local candidates=("$@")
    
    local existing_non_empty=()
    local existing_empty=()

    # 分类存在的目录
    for dir in "${candidates[@]}"; do
        local expanded_dir="${dir/#\~/$HOME}"
        if [ -d "$expanded_dir" ]; then
            if [ "$(ls -A "$expanded_dir" 2>/dev/null)" ]; then
                existing_non_empty+=("$dir")
            else
                existing_empty+=("$dir")
            fi
        fi
    done

    # 合并后的有效选项（非空在前，空在后）
    local valid_options=("${existing_non_empty[@]}" "${existing_empty[@]}")

    # 检查是否有可用选项
    if [ ${#valid_options[@]} -eq 0 ]; then
        echo "错误：未找到任何有效的候选目录 (${candidates[*]})" >&2
        exit 1
    fi

    echo -e "\033[1;36m请选择 $label 的基础安装目录 (推荐使用非空目录)：\033[0m" >&2
    for i in "${!valid_options[@]}"; do
        local suffix=""
        # 标记非空目录
        for ne in "${existing_non_empty[@]}"; do
            if [ "$ne" == "${valid_options[$i]}" ]; then
                suffix=" (当前非空，优先推荐)"
                break
            fi
        done
        echo "$((i+1))) ${valid_options[$i]}$suffix" >&2
    done

    local default_choice=1
    while true; do
        read -p "选择 (1-${#valid_options[@]}, 默认为 $default_choice): " choice <&2
        [ -z "$choice" ] && choice=$default_choice
        
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#valid_options[@]}" ]; then
            local selected="${valid_options[$((choice-1))]}"
            echo "${selected/#\~/$HOME}"
            return 0
        fi
        echo "无效选择，请重试。" >&2
    done
}

# 目标基础目录选择
echo "--- 配置安装路径 ---"
# skills 优先顺序: ~/.agents ~/.claude ~/.gemini
SKILLS_BASE=$(choose_base_dir "Skills" "~/.agents" "~/.claude" "~/.gemini")
TARGET_SKILLS="$SKILLS_BASE/skills"

# 当前目录下的 memories-off-skill 路径
SOURCE_DIR="$(pwd)/memories-off-skill"
SKILL_NAME="memories-off"  # 用户要求重命名为 memories-off

# 确保目标基础目录存在
mkdir -p "$TARGET_SKILLS"

if [ ! -d "$SOURCE_DIR" ]; then
    echo "错误：当前目录下未找到 'memories-off-skill' 文件夹。"
    exit 1
fi

# --- 增加全局确认逻辑 ---
echo "即将执行以下操作："
echo "1. 将 $SOURCE_DIR 软链接到 $TARGET_SKILLS/$SKILL_NAME (注意：已重命名)"
echo "2. 将 $SKILL_NAME 添加到 $TARGET_SKILLS/.gitignore"
echo "3. 尝试从 Git 版本控制中移除已有的软链接（git rm --cached）"
echo
read -p "是否确定继续？(y/N) " global_confirm
if [[ "$global_confirm" != "y" && "$global_confirm" != "Y" ]]; then
    echo "操作已取消。"
    exit 0
fi

echo "正在从 $SOURCE_DIR 链接技能到 $TARGET_SKILLS/$SKILL_NAME ..."
echo "------------------------------------------------"

# 检查目标目录是否在 Git 管理下
IS_GIT_REPO=false
if [ -d "$(dirname "$TARGET_SKILLS")/.git" ] || [ -d "$TARGET_SKILLS/.git" ]; then
    IS_GIT_REPO=true
fi

target_link="$TARGET_SKILLS/$SKILL_NAME"

# 检查技能目录链接 (包含损坏链接覆盖逻辑)
if [ -L "$target_link" ] && [ ! -e "$target_link" ]; then
    # 如果是损坏的软链接，则直接覆盖
    ln -sf "$SOURCE_DIR" "$target_link"
    echo " [覆盖无效链接] $SKILL_NAME -> $target_link"
elif [ -e "$target_link" ] || [ -L "$target_link" ]; then
    echo " [跳过技能] $SKILL_NAME (目标已存在)"
else
    ln -s "$SOURCE_DIR" "$target_link"
    echo " [创建技能] $SKILL_NAME -> $target_link"
fi

# --- 增加 Git 忽略和清理逻辑 ---
if [ "$IS_GIT_REPO" = true ]; then
    # 添加到 .gitignore (如果不存在)
    GITIGNORE_PATH="$TARGET_SKILLS/.gitignore"
    if ! grep -qxF "$SKILL_NAME" "$GITIGNORE_PATH" 2>/dev/null; then
        echo "$SKILL_NAME" >> "$GITIGNORE_PATH"
        echo " [Git] 已将 $SKILL_NAME 添加到 .gitignore"
    fi
    # 从 Git 缓存中移除 (防止之前已被提交)
    (cd "$TARGET_SKILLS" && git rm --cached -r "$SKILL_NAME" 2>/dev/null && echo " [Git] 已从缓存中移除 $SKILL_NAME") || true
fi

echo "------------------------------------------------"
echo "处理完成。"
