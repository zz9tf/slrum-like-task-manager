#!/bin/bash
# Task Manager Installation Script

echo "🚀 Installing Task Manager..."

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.7"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.7 or higher required, current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Check tmux
echo "🔍 Checking tmux..."
if command -v tmux > /dev/null 2>&1; then
    echo "✅ tmux check passed: $(tmux -V 2>/dev/null || echo 'tmux installed')"
else
    echo "❌ Error: tmux is required to use this package"
    echo ""
    echo "Please install tmux first:"
    echo "  Ubuntu/Debian: sudo apt-get install tmux"
    echo "  CentOS/RHEL:   sudo yum install tmux"
    echo "  macOS:         brew install tmux"
    echo ""
    echo "After installing tmux, please run this installation script again"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Dependency installation failed"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Install package
echo "📦 Installing task manager package..."
pip3 install -e .

if [ $? -ne 0 ]; then
    echo "❌ Package installation failed"
    exit 1
fi

echo "✅ Package installed successfully"

# Initialize configuration
echo "📁 Initializing configuration..."
task config init

echo ""
echo "🎉 Installation completed!"
echo ""
echo "Usage:"
echo "  task --help          # View help"
echo "  task run 'Task Name' 'command'  # Run task"
echo "  task list            # List tasks"
echo ""
echo "Configure email notifications:"
echo "  1. Prepare email config file (email_config.json format)"
echo "  2. Prepare Gmail token file (token.json format)"
echo "  3. Import configuration:"
echo "     task config email <config_file>"
echo "     task config token <token_file>"
echo "  4. Test configuration:"
echo "     task config test"
echo ""
echo "Configuration directory: ~/.task_manager/"
echo "Log directory: ~/.task_manager/logs/"
echo ""
echo "For detailed configuration instructions, see: task config --help"
