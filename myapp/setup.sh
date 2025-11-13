#!/bin/bash

# MyApp 项目初始化脚本
# 用于快速设置开发环境（仅使用 uv）

set -e  # 遇到错误立即退出

echo "🚀 开始初始化 MyApp 项目..."

# 检查是否在项目根目录
if [ ! -f "requirements.txt" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.bashrc
fi

echo "✅ uv 版本: $(uv --version)"

# 删除旧的虚拟环境（如果存在）
if [ -d ".venv" ]; then
    echo "🗑️  删除旧的虚拟环境..."
    rm -rf .venv
fi

# 创建虚拟环境
echo "📦 使用 uv 创建虚拟环境..."
uv venv --python 3.11

# 激活虚拟环境
echo "🔌 激活虚拟环境..."
source .venv/bin/activate

# 安装依赖
echo "📦 使用 uv 安装依赖（使用清华镜像源）..."
uv pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 验证安装
echo ""
echo "🔍 验证安装..."
if python src/main.py --help &> /dev/null; then
    echo "✅ 初始化开发环境成功！"
else 
    echo "⚠️  警告: 无法验证安装，请手动检查"
fi
