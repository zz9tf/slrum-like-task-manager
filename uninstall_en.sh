#!/bin/bash
# Task Manager Uninstall Script

echo "🗑️  Starting task manager uninstallation..."

# Check if installed
if ! command -v task > /dev/null 2>&1; then
    echo "❌ Task manager not installed or not found in PATH"
    echo "Please check installation status or manually clean up files"
    exit 1
fi

echo "✅ Detected installed task manager"

# Stop all running tasks
echo "🛑 Stopping all running tasks..."
task kill --all 2>/dev/null || true

# Uninstall Python package
echo "📦 Uninstalling Python package..."
pip3 uninstall task-manager -y 2>/dev/null || {
    echo "⚠️  pip uninstall failed, trying alternative method..."
    # Try uninstalling from user directory
    pip3 uninstall task-manager --user -y 2>/dev/null || {
        echo "⚠️  Unable to automatically uninstall Python package, please run manually:"
        echo "   pip3 uninstall task-manager"
    }
}

# Delete configuration files (optional)
echo ""
echo "📁 Configuration directory: ~/.task_manager/"
echo "Delete configuration files? (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "🗑️  Deleting configuration files..."
    rm -rf ~/.task_manager/
    echo "✅ Configuration files deleted"
else
    echo "ℹ️  Keeping configuration files"
fi

# Check and prompt for manual cleanup
echo ""
echo "🔍 Checking for remaining files..."

# Check bash wrapper
if [ -f ~/.local/bin/task ]; then
    echo "⚠️  Found bash wrapper: ~/.local/bin/task"
    echo "Delete it? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -f ~/.local/bin/task
        echo "✅ Bash wrapper deleted"
    fi
fi

# Check other possible installation locations
if [ -f /usr/local/bin/task ]; then
    echo "⚠️  Found system-level installation: /usr/local/bin/task"
    echo "Requires admin privileges to delete, please run manually:"
    echo "   sudo rm /usr/local/bin/task"
fi

echo ""
echo "🎉 Uninstallation completed!"
echo ""
echo "If you encounter issues, please manually check the following locations:"
echo "  - Python package: pip3 list | grep task-manager"
echo "  - Configuration files: ~/.task_manager/"
echo "  - Executable: which task"
echo ""
echo "Thank you for using Task Manager!"
