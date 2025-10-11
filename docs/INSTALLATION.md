# 安装指南

## 目录
- [系统要求](#系统要求)
- [快速安装](#快速安装)
- [详细安装步骤](#详细安装步骤)
- [平台特定说明](#平台特定说明)
- [Docker 安装](#docker-安装)
- [验证安装](#验证安装)
- [常见问题](#常见问题)
- [卸载说明](#卸载说明)

## 系统要求

### 最低要求
- **操作系统**: Windows 10+, Ubuntu 18.04+, macOS 10.15+
- **Python**: 3.8 或更高版本
- **内存**: 至少 2GB RAM
- **存储**: 至少 500MB 可用空间
- **网络**: 稳定的互联网连接

### 推荐配置
- **操作系统**: 最新版本的 Windows 11, Ubuntu 22.04, macOS 13+
- **Python**: 3.10 或 3.11
- **内存**: 4GB 或更多 RAM
- **存储**: 1GB 或更多可用空间
- **网络**: 高速互联网连接

### 依赖软件
- Git（用于克隆仓库）
- pip（Python 包管理器）
- 现代浏览器（Chromium 将自动安装）

## 快速安装

### 一键安装脚本

**Linux/macOS**:
```bash
curl -fsSL https://raw.githubusercontent.com/yourusername/Auto/main/install.sh | bash
```

**Windows PowerShell**:
```powershell
iwr -useb https://raw.githubusercontent.com/yourusername/Auto/main/install.ps1 | iex
```

### 使用 pip 安装（如果已发布到 PyPI）

```bash
pip install auto-login-tool
```

## 详细安装步骤

### 步骤 1: 安装 Python

#### Windows
1. 访问 [Python 官网](https://www.python.org/downloads/)
2. 下载 Python 3.8+ 安装程序
3. 运行安装程序，**勾选 "Add Python to PATH"**
4. 点击 "Install Now"
5. 验证安装：
   ```powershell
   python --version
   pip --version
   ```

#### macOS
使用 Homebrew:
```bash
# 安装 Homebrew（如果没有）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Python
brew install python@3.11

# 验证安装
python3 --version
pip3 --version
```

#### Linux (Ubuntu/Debian)
```bash
# 更新包管理器
sudo apt update

# 安装 Python 和 pip
sudo apt install python3 python3-pip python3-venv

# 验证安装
python3 --version
pip3 --version
```

#### Linux (CentOS/RHEL/Fedora)
```bash
# 安装 Python
sudo dnf install python3 python3-pip

# 验证安装
python3 --version
pip3 --version
```

### 步骤 2: 克隆项目仓库

```bash
# 使用 HTTPS
git clone https://github.com/yourusername/Auto.git

# 或使用 SSH
git clone git@github.com:yourusername/Auto.git

# 进入项目目录
cd Auto
```

如果没有安装 Git:

**Windows**: 下载并安装 [Git for Windows](https://gitforwindows.org/)

**macOS**:
```bash
brew install git
```

**Linux**:
```bash
sudo apt install git  # Ubuntu/Debian
sudo dnf install git  # CentOS/RHEL/Fedora
```

### 步骤 3: 创建虚拟环境（推荐）

#### Windows
```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\activate

# 验证激活（命令提示符前会显示 (venv)）
```

#### macOS/Linux
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 验证激活（命令提示符前会显示 (venv)）
```

### 步骤 4: 安装 Python 依赖

```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 如果遇到权限问题，使用：
pip install --user -r requirements.txt
```

### 步骤 5: 安装 Playwright 浏览器

```bash
# 安装 Chromium（默认）
playwright install chromium

# 或安装所有支持的浏览器
playwright install

# 安装系统依赖（Linux 需要）
playwright install-deps
```

**注意**: 首次安装可能需要下载约 100MB 的浏览器文件。

### 步骤 6: 配置环境

1. **复制配置模板**:
```bash
cp config/users.json.example config/users.json
```

2. **编辑配置文件**:
```bash
# Linux/macOS
nano config/users.json

# Windows
notepad config/users.json
```

3. **添加你的账号信息**:
```json
{
  "config": {
    "headless": false,
    "use_cookies": true,
    "cookie_expire_days": 30
  },
  "users": [
    {
      "site": "linuxdo",
      "email": "your_email@example.com",
      "password": "your_password"
    }
  ]
}
```

## 平台特定说明

### Windows

#### Windows Subsystem for Linux (WSL)
如果使用 WSL:
```bash
# 安装 WSL（如果未安装）
wsl --install

# 在 WSL 中安装项目
# 遵循 Linux 安装步骤
```

#### 防火墙和杀毒软件
- Windows Defender 可能会扫描 Playwright 下载的浏览器
- 添加项目目录到排除列表可以提高性能

### macOS

#### Apple Silicon (M1/M2)
```bash
# 确保使用 ARM64 版本的 Python
arch -arm64 python3 -m pip install -r requirements.txt
arch -arm64 playwright install chromium
```

#### 权限问题
首次运行可能需要允许终端访问:
- 系统偏好设置 → 安全性与隐私 → 隐私 → 完全磁盘访问权

### Linux

#### 无头服务器
在没有图形界面的服务器上:
```bash
# 安装 xvfb
sudo apt install xvfb  # Ubuntu/Debian
sudo dnf install xorg-x11-server-Xvfb  # CentOS/RHEL

# 使用 xvfb 运行
xvfb-run python -m src linuxdo --headless
```

#### 依赖问题
如果遇到依赖问题:
```bash
# Ubuntu/Debian
sudo apt install \
    libnss3 \
    libxss1 \
    libasound2 \
    libxrandr2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libatk-bridge2.0-0 \
    libgtk-3-0

# 或使用 Playwright 的自动安装
playwright install-deps
```

## Docker 安装

### 使用预构建镜像

```bash
# 拉取镜像
docker pull yourusername/auto-login-tool:latest

# 运行容器
docker run -it \
    -v $(pwd)/config:/app/config \
    -v $(pwd)/data:/app/data \
    yourusername/auto-login-tool
```

### 从 Dockerfile 构建

1. **创建 Dockerfile**:
```dockerfile
FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 和浏览器
RUN pip install playwright \
    && playwright install chromium \
    && playwright install-deps

# 复制项目文件
COPY . .

# 创建数据目录
RUN mkdir -p /app/data /app/config

# 设置环境变量
ENV PYTHONPATH=/app

# 默认命令
CMD ["python", "-m", "src", "--help"]
```

2. **构建镜像**:
```bash
docker build -t auto-login-tool .
```

3. **运行容器**:
```bash
docker run -it \
    -v $(pwd)/config:/app/config:ro \
    -v $(pwd)/data:/app/data \
    auto-login-tool linuxdo
```

### Docker Compose

创建 `docker-compose.yml`:
```yaml
version: '3.8'

services:
  auto:
    build: .
    volumes:
      - ./config:/app/config:ro
      - ./data:/app/data
    environment:
      - DISPLAY=${DISPLAY}
    network_mode: host
    stdin_open: true
    tty: true
```

运行:
```bash
docker-compose up
docker-compose run auto python -m src linuxdo
```

## 验证安装

### 基本验证

1. **检查 Python 安装**:
```bash
python --version
# 应显示 Python 3.8.x 或更高
```

2. **检查依赖安装**:
```bash
pip list | grep playwright
# 应显示 playwright==1.48.0 或类似版本
```

3. **检查 Playwright 浏览器**:
```bash
playwright --version
# 应显示版本信息
```

4. **运行帮助命令**:
```bash
python -m src --help
# 应显示可用命令列表
```

### 功能测试

1. **测试基本功能**:
```bash
# 测试单个站点（使用测试账号）
python -m src linuxdo --headless --no-cookie
```

2. **检查日志**:
```bash
# Windows
type data\logs\linuxdo.log

# Linux/macOS
cat data/logs/linuxdo.log
```

3. **检查截图**（如果有错误）:
```bash
ls data/screenshots/
```

## 常见问题

### 1. pip install 失败

**问题**: `error: Microsoft Visual C++ 14.0 or greater is required`

**解决方案** (Windows):
- 安装 [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

### 2. Playwright 安装失败

**问题**: `Playwright host validation failed`

**解决方案**:
```bash
# 清理并重新安装
pip uninstall playwright
pip install playwright
playwright install --with-deps
```

### 3. 权限错误

**问题**: `Permission denied` 错误

**解决方案**:
```bash
# Linux/macOS
sudo chown -R $USER:$USER ~/Auto
chmod -R 755 ~/Auto

# 或使用用户安装
pip install --user -r requirements.txt
```

### 4. Python 版本不兼容

**问题**: `Python 3.7 is not supported`

**解决方案**:
- 升级到 Python 3.8+
- 使用 pyenv 管理多个 Python 版本:
```bash
# 安装 pyenv
curl https://pyenv.run | bash

# 安装 Python 3.11
pyenv install 3.11.0
pyenv local 3.11.0
```

### 5. 虚拟环境激活失败

**问题**: `cannot be loaded because running scripts is disabled`

**解决方案** (Windows PowerShell):
```powershell
# 允许运行脚本
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 6. 浏览器启动失败

**问题**: `Browser closed unexpectedly`

**解决方案**:
```bash
# 安装缺失的系统依赖
playwright install-deps

# Linux 特定
sudo apt-get update
sudo apt-get install -y libgbm1
```

### 7. 代理问题

**问题**: 在公司网络或使用代理时无法下载

**解决方案**:
```bash
# 设置代理
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# pip 使用代理
pip install --proxy http://proxy.company.com:8080 -r requirements.txt
```

## 卸载说明

### 完全卸载

1. **删除虚拟环境**:
```bash
# 退出虚拟环境
deactivate

# 删除虚拟环境目录
rm -rf venv/  # Linux/macOS
rmdir /s venv  # Windows
```

2. **卸载 Python 包**:
```bash
pip uninstall -y playwright
pip uninstall -r requirements.txt
```

3. **删除 Playwright 浏览器**:
```bash
# Linux/macOS
rm -rf ~/Library/Caches/ms-playwright/  # macOS
rm -rf ~/.cache/ms-playwright/  # Linux

# Windows
rmdir /s "%USERPROFILE%\AppData\Local\ms-playwright"
```

4. **删除项目文件**:
```bash
cd ..
rm -rf Auto/  # Linux/macOS
rmdir /s Auto  # Windows
```

5. **清理配置和数据**（可选）:
```bash
# 备份重要数据后
rm -rf ~/.auto/  # 如果有全局配置
```

### 保留数据的卸载

如果想保留 Cookie 和日志:
```bash
# 备份数据
cp -r data/ ~/auto-backup/

# 只删除代码和依赖
rm -rf src/ venv/ node_modules/
```

## 升级指南

### 从旧版本升级

1. **备份数据**:
```bash
cp -r data/ data-backup/
cp config/users.json config/users.json.backup
```

2. **更新代码**:
```bash
git pull origin main
```

3. **更新依赖**:
```bash
pip install --upgrade -r requirements.txt
playwright install
```

4. **迁移配置**（如果需要）:
```bash
python scripts/migrate_config.py
```

### 自动更新脚本

创建 `update.sh` (Linux/macOS):
```bash
#!/bin/bash
set -e

echo "备份数据..."
cp -r data/ data-backup-$(date +%Y%m%d)

echo "更新代码..."
git pull

echo "更新依赖..."
pip install --upgrade -r requirements.txt

echo "更新浏览器..."
playwright install

echo "更新完成!"
```

使用:
```bash
chmod +x update.sh
./update.sh
```

## 下一步

安装完成后，请参考:
- [用户手册](USER_GUIDE.md) - 学习如何使用
- [配置参考](CONFIGURATION.md) - 详细配置说明
- [故障排除](TROUBLESHOOTING.md) - 解决常见问题