# 任务管理系统

基于tmux的任务调度和监控工具，支持并发执行、实时监控、邮件通知等功能。

## 功能特性

- 🚀 **并发执行**: 支持多个任务同时运行
- 📊 **实时监控**: 实时查看任务状态和输出
- 🛠️ **资源监控**: CPU、内存、磁盘使用率监控
- 📝 **日志管理**: 自动记录任务输出和日志
- 🔧 **配置管理**: 简单的配置文件管理
- 📧 **邮件通知**: 任务完成时自动发送邮件（需要配置）

## 安装

### 系统要求

- Python 3.7+
- tmux (必需)

### 检查tmux

在安装前，请确保系统已安装tmux：

```bash
# 检查tmux是否已安装
tmux --version

# 如果没有安装，请先安装tmux
# Ubuntu/Debian:
sudo apt-get install tmux

# CentOS/RHEL:
sudo yum install tmux

# macOS:
brew install tmux
```

### 快速安装

```bash
# 克隆仓库
git clone <repository-url>
cd task_manager

# 运行安装脚本
chmod +x install.sh
./install.sh
```

### 手动安装

```bash
# 安装Python包
pip install .

# 初始化配置
task config init
```

## 使用方法

### 基本命令

```bash
# 运行新任务
task run <name> <command> [priority] [max_retries]

# 查看任务列表
task list

# 停止任务
task kill <task_id>

# 实时监控
task monitor

# 查看任务状态
task status <task_id>

# 查看任务输出
task output <task_id>

# 清理已完成任务
task cleanup [days]

# 查看任务日志
task logs <task_id>

# 配置管理
task config <action>
```

### 示例

```bash
# 运行一个简单任务
task run "测试任务" "echo 'Hello World' && sleep 5"

# 运行高优先级任务
task run "重要任务" "python train.py" 10

# 查看所有任务
task list

# 停止特定任务
task kill 00001

# 停止所有运行中的任务
task kill --all
```

## 邮件通知配置

**注意**: 任务管理系统在安装后可以立即使用所有功能，但邮件通知需要额外配置。如果不配置邮件，系统仍可正常监控和管理任务，只是不会发送邮件通知。

### 配置邮件功能需要三个文件

要启用邮件通知功能，需要配置以下三个文件：

1. **email_config.json** - 邮件配置文件
2. **credentials.json** - Google API凭据文件  
3. **token.json** - Gmail访问令牌文件

### 方法一：完整配置流程（推荐）

#### 第一步：配置邮件设置

创建 `email_config.json` 文件：

```json
{
    "enabled": true,
    "to_email": "your-email@example.com"
}
```

**配置说明**:
- `enabled`: 是否启用邮件通知 (true/false)
- `to_email`: 接收通知的邮箱地址

**命令**:
```bash
# 创建邮件配置文件
echo '{"enabled": true, "to_email": "your-email@example.com"}' > email_config.json

# 导入邮件配置
task config email email_config.json
```

#### 第二步：获取Google API凭据

1. **访问Google Cloud Console**
   - 打开 [Google Cloud Console](https://console.cloud.google.com/)

2. **创建或选择项目**
   - 创建新项目或选择现有项目

3. **启用Gmail API**
   - 在"API和服务" > "库"中搜索"Gmail API"
   - 点击"启用"

4. **创建OAuth 2.0凭据**
   - 在"API和服务" > "凭据"中点击"创建凭据"
   - 选择"OAuth 2.0客户端ID"
   - 应用类型选择"桌面应用程序"
   - 下载凭据文件（通常命名为 `credentials.json`）

**命令**:
```bash
# 导入Google API凭据
task config google_api file /path/to/your/credentials.json
```

#### 第三步：获取访问令牌

通过OAuth登录获取token文件：

**命令**:
```bash
# 通过浏览器登录获取token
task config google_api login
```

#### 第四步：测试邮件功能

验证邮件配置是否成功：

**命令**:
```bash
# 测试邮件发送
task config test
```

#### 可选：配置不同机器的token文件

如果需要在不同机器上使用，可以复制token文件：

**命令**:
```bash
# 导入已有的token文件
task config token /path/to/your/token.json
```

### 方法二：使用现有文件（快速配置）

如果你已经有 `email_config.json`、`credentials.json` 和 `token.json` 文件：

```bash
# 1. 初始化配置
task config init

# 2. 导入邮件配置
task config email /path/to/your/email_config.json

# 3. 导入Google API凭据
task config google_api file /path/to/your/credentials.json

# 4. 导入Gmail token
task config token /path/to/your/token.json

# 5. 测试邮件发送
task config test
```

### 配置管理命令

```bash
# 初始化配置
task config init

# 邮件配置
task config email <config_file>

# Google API凭据
task config google_api file <credentials_file>
task config google_api login

# Gmail token
task config token <token_file>

# 查看和测试
task config show
task config test
```

### 配置文件格式

**Gmail Token文件** (`token.json`):
```json
{
    "token": "your-token",
    "refresh_token": "your-fresh-token",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": "your-client-id",
    "client_secret": "your-client-secret",
    "scopes": ["https://www.googleapis.com/auth/gmail.send"],
    "universe_domain": "googleapis.com",
    "account": "",
    "expiry": "your-expiry-date"
}
```

**Google API凭据文件** (`credentials.json`):
```json
{
    "installed": {
        "client_id": "your-client-id.apps.googleusercontent.com",
        "project_id": "your-project-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "your-client-secret",
        "redirect_uris": ["http://localhost"]
    }
}
```

### 日志管理

```bash
# 查看任务日志
task logs <task_id>

# 查看所有日志文件
ls ~/.task_manager/logs/
```

### 高级功能

#### 任务优先级

```bash
# 运行高优先级任务（数字越大优先级越高）
task run "重要任务" "python train.py" 10

# 运行低优先级任务
task run "后台任务" "python data_process.py" 1
```

#### 任务重试

```bash
# 设置最大重试次数
task run "可能失败的任务" "python unstable_script.py" 0 3
```

#### 资源监控

```bash
# 实时监控所有任务
task monitor

# 查看特定任务状态
task status 00001
```

## 项目结构

```
task_manager/
├── task_manager/           # 核心模块
│   ├── __init__.py
│   ├── cli.py             # 命令行接口
│   ├── core.py            # 核心任务管理
│   ├── email.py           # 邮件通知
│   ├── config.py          # 配置管理
│   └── monitor.py         # 监控功能
├── setup.py               # 包配置
├── requirements.txt       # 依赖列表
├── install.sh            # 安装脚本
└── README.md             # 项目文档
```

## 配置目录

```
~/.task_manager/
├── config/
│   ├── email_config.json              # 邮件配置
│   ├── credentials.json               # Google API凭据
│   └── token.json                     # Gmail token
├── tasks.json                         # 任务数据
└── logs/                              # 任务日志
```

## 依赖

- Python 3.7+
- tmux
- psutil
- google-auth
- google-auth-oauthlib
- google-api-python-client

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

### v1.0.0
- 初始版本发布
- 支持基本任务管理功能
- 支持邮件通知
- 支持Google API OAuth
- 支持配置管理
