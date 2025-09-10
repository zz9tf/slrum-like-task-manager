#!/bin/bash
# 任务管理器安装脚本

echo "🚀 安装任务管理器..."

# 检查Python版本
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.7"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ 错误: 需要Python 3.7或更高版本，当前版本: $python_version"
    exit 1
fi

echo "✅ Python版本检查通过: $python_version"

# 检查tmux
echo "🔍 检查tmux..."
if command -v tmux > /dev/null 2>&1; then
    echo "✅ tmux检查通过: $(tmux -V 2>/dev/null || echo 'tmux已安装')"
else
    echo "❌ 错误: 需要安装tmux才能使用此包"
    echo ""
    echo "请先安装tmux:"
    echo "  Ubuntu/Debian: sudo apt-get install tmux"
    echo "  CentOS/RHEL:   sudo yum install tmux"
    echo "  macOS:         brew install tmux"
    echo ""
    echo "安装tmux后，请重新运行此安装脚本"
    exit 1
fi

# 安装依赖
echo "📦 安装依赖包..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败"
    exit 1
fi

echo "✅ 依赖安装完成"

# 安装包
echo "📦 安装任务管理器包..."
pip3 install -e .

if [ $? -ne 0 ]; then
    echo "❌ 包安装失败"
    exit 1
fi

echo "✅ 包安装完成"

# 初始化配置
echo "📁 初始化配置..."
task config init

echo ""
echo "🎉 安装完成！"
echo ""
echo "使用方法:"
echo "  task --help          # 查看帮助"
echo "  task run '任务名' '命令'  # 运行任务"
echo "  task list            # 列出任务"
echo ""
echo "配置邮件通知:"
echo "  1. 准备邮件配置文件 (email_config.json 格式)"
echo "  2. 准备Gmail token文件 (token.json 格式)"
echo "  3. 导入配置:"
echo "     task config email <config_file>"
echo "     task config token <token_file>"
echo "  4. 测试配置:"
echo "     task config test"
echo ""
echo "配置目录: ~/.task_manager/"
echo "日志目录: ~/.task_manager/logs/"
echo ""
echo "详细配置说明请查看: task config --help"
