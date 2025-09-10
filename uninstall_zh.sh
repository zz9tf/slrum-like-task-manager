#!/bin/bash
# 任务管理器卸载脚本

echo "🗑️  开始卸载任务管理器..."

# 检查是否已安装
if ! command -v task > /dev/null 2>&1; then
    echo "❌ 任务管理器未安装或未在PATH中找到"
    echo "请检查安装状态或手动清理文件"
    exit 1
fi

echo "✅ 检测到已安装的任务管理器"

# 停止所有运行中的任务
echo "🛑 停止所有运行中的任务..."
task kill --all 2>/dev/null || true

# 卸载Python包
echo "📦 卸载Python包..."
pip3 uninstall task-manager -y 2>/dev/null || {
    echo "⚠️  使用pip卸载失败，尝试其他方法..."
    # 尝试从用户目录卸载
    pip3 uninstall task-manager --user -y 2>/dev/null || {
        echo "⚠️  无法自动卸载Python包，请手动执行:"
        echo "   pip3 uninstall task-manager"
    }
}

# 删除配置文件（可选）
echo ""
echo "📁 配置文件位置: ~/.task_manager/"
echo "是否删除配置文件？(y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "🗑️  删除配置文件..."
    rm -rf ~/.task_manager/
    echo "✅ 配置文件已删除"
else
    echo "ℹ️  保留配置文件"
fi

# 检查并提示手动清理
echo ""
echo "🔍 检查剩余文件..."

# 检查bash包装器
if [ -f ~/.local/bin/task ]; then
    echo "⚠️  发现bash包装器: ~/.local/bin/task"
    echo "是否删除？(y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -f ~/.local/bin/task
        echo "✅ bash包装器已删除"
    fi
fi

# 检查其他可能的安装位置
if [ -f /usr/local/bin/task ]; then
    echo "⚠️  发现系统级安装: /usr/local/bin/task"
    echo "需要管理员权限删除，请手动执行:"
    echo "   sudo rm /usr/local/bin/task"
fi

echo ""
echo "🎉 卸载完成！"
echo ""
echo "如果遇到问题，请手动检查以下位置："
echo "  - Python包: pip3 list | grep task-manager"
echo "  - 配置文件: ~/.task_manager/"
echo "  - 可执行文件: which task"
echo ""
echo "感谢使用任务管理器！"
