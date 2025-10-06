# Auto - Web 自动化登录工具集

基于 Playwright 的多站点自动化登录工具，支持 Cookie 持久化和快速登录。

## 特性

- 🎯 **多站点支持**: AnyRouter、Linux.do、OpenI
- 🍪 **Cookie 持久化**: 自动保存和加载，支持快速登录
- 🔧 **统一 CLI**: 简洁的命令行界面
- 📦 **清晰架构**: 代码、配置、数据完全分离
- 🛡️ **完善日志**: 每站点独立日志，错误自动截图

## 项目结构

```
Auto/
├── src/                      # 源代码
│   ├── core/                 # 核心模块
│   │   ├── base.py           # LoginAutomation 基类
│   │   ├── browser.py        # 浏览器管理
│   │   ├── cookies.py        # Cookie 管理
│   │   ├── paths.py          # 统一路径管理
│   │   └── logger.py         # 日志配置
│   ├── sites/                # 站点登录模块
│   │   ├── anyrouter/        # AnyRouter (LinuxDO OAuth)
│   │   ├── linuxdo/          # Linux.do 论坛
│   │   └── openi/            # OpenI 平台
│   │       ├── login.py      # 登录逻辑
│   │       ├── popup.py      # 弹窗处理
│   │       ├── cloud_task.py # 任务管理
│   │       ├── config.py     # 配置加载
│   │       └── runner.py     # 多用户执行
│   └── __main__.py           # 统一 CLI 入口
├── config/                   # 配置文件
│   ├── users.json.example    # 配置模板
│   └── users.json            # 用户配置（gitignore）
├── data/                     # 运行时数据（gitignore）
│   ├── cookies/              # Cookie 存储
│   ├── logs/                 # 日志文件
│   └── screenshots/          # 错误截图
├── docs/                     # 文档
│   └── history/              # 重构历史
├── .gitignore
├── requirements.txt
└── README.md
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

### 配置

推荐使用统一配置文件方式（所有站点均支持）。环境变量仍保留作为向后兼容的备用方案。

**推荐方式**：使用 `config/users.json` 统一配置（所有站点）

1. 复制配置模板：
```bash
cp config/users.json.example config/users.json
```

2. 编辑 `config/users.json`：
```json
{
  "config": {
    "task_name": "image",
    "run_duration": 15,
    "headless": false,
    "use_cookies": true,
    "cookie_expire_days": 7
  },
  "users": [
    {"site": "openi", "username": "用户名1", "password": "密码1"},
    {"site": "linuxdo", "email": "邮箱@example.com", "password": "密码"},
    {"site": "anyrouter", "email": "邮箱@example.com", "password": "密码"}
  ]
}
```

**备选方式**：环境变量（向后兼容）

```bash
# LinuxDO / AnyRouter（任一可用）
export LINUXDO_EMAIL="your_email@example.com"
export LINUXDO_PASSWORD="your_password"

# 或 AnyRouter 专用
export ANYROUTER_EMAIL="your_email@example.com"
export ANYROUTER_PASSWORD="your_password"
```

### 使用

```bash
# AnyRouter 登录（LinuxDO OAuth）
python -m src anyrouter

# Linux.do 论坛登录
python -m src linuxdo

# OpenI 平台登录（所有用户）
python -m src openi

# OpenI 平台登录（指定用户）
python -m src openi --user yls

# 无头模式运行
python -m src anyrouter --headless

# 不使用 Cookie
python -m src linuxdo --no-cookie

# 查看帮助
python -m src --help
```

## 架构设计

### 核心原则

- **职责分离**: 代码、配置、数据完全隔离
- **继承复用**: 基于 `LoginAutomation` 基类消除重复代码
- **路径统一**: 所有运行时数据存放在 `data/` 目录
- **配置集中**: 所有配置文件存放在 `config/` 目录

### 添加新站点

1. 在 `src/sites/` 下创建新目录
2. 创建 `login.py` 继承 `LoginAutomation`
3. 实现 `verify_login()` 和 `do_login()` 方法
4. 在 `src/__main__.py` 中添加命令

示例：

```python
from src.core.base import LoginAutomation
from playwright.sync_api import Page

class NewSiteLogin(LoginAutomation):
    def __init__(self, *, headless: bool = False):
        super().__init__('newsite', headless=headless)

    def verify_login(self, page: Page) -> bool:
        # 检查登录状态
        return page.locator('.user-avatar').count() > 0

    def do_login(self, page: Page, **credentials) -> bool:
        # 执行登录逻辑
        page.goto('https://newsite.com/login')
        # ...
        return self.verify_login(page)
```

## 站点说明

### LinuxDO
- **登录方式**: 账号密码表单登录
- **凭据配置**:
  1. 优先：`config/users.json` - `users` 数组（`site: "linuxdo"`）
  2. 回退：环境变量 `LINUXDO_EMAIL` / `LINUXDO_PASSWORD`
- **特性**: Cookie 快速登录、自动处理登录表单

### AnyRouter
- **登录方式**: LinuxDO OAuth 授权
- **凭据配置**:
  1. 优先：`config/users.json` - `users` 数组（`site: "anyrouter"`）
  2. 回退：环境变量 `ANYROUTER_EMAIL` / `ANYROUTER_PASSWORD` 或 `LINUXDO_EMAIL` / `LINUXDO_PASSWORD`
- **特性**: 自动处理授权弹窗、记住授权、导航到 API 令牌页

### OpenI
- **登录方式**: 账号密码登录
- **凭据配置**: `config/users.json` - `users` 数组（`site: "openi"`）
- **特性**:
  - 多用户批量处理
  - 云脑任务自动化（启动/停止任务赚取积分）
  - 每用户独立 Cookie 管理
  - 详细日志记录

## 配置说明

### 配置格式

**当前格式**（推荐 - 最简洁）：
```json
{
  "config": {
    "task_name": "image",
    "run_duration": 15,
    "headless": false,
    "use_cookies": true,
    "cookie_expire_days": 7
  },
  "users": [
    {"site": "openi", "username": "u", "password": "p"},
    {"site": "linuxdo", "email": "e", "password": "p"},
    {"site": "anyrouter", "email": "e", "password": "p"}
  ]
}
```

**说明**：
- `config`: 全局配置项（所有站点共享）
- `users`: 用户凭据列表，通过 `site` 字段区分站点
- 支持同站点多账号：添加多个相同 `site` 的条目即可

### 环境变量回退说明

- **LinuxDO**: 优先读取 `config/users.json`，缺失时回退到 `LINUXDO_EMAIL` / `LINUXDO_PASSWORD`
- **AnyRouter**: 优先读取 `config/users.json`，缺失时回退到 `ANYROUTER_EMAIL` / `ANYROUTER_PASSWORD`，再回退到 `LINUXDO_EMAIL` / `LINUXDO_PASSWORD`
- **优先级总原则**: 配置文件 > 环境变量（向后兼容）

### 多用户配置示例

```json
{
  "config": {
    "task_name": "image",
    "run_duration": 15,
    "headless": false,
    "use_cookies": true,
    "cookie_expire_days": 7
  },
  "users": [
    {"site": "openi", "username": "user1", "password": "pass1"},
    {"site": "openi", "username": "user2", "password": "pass2"},
    {"site": "openi", "username": "user3", "password": "pass3"},
    {"site": "linuxdo", "email": "user@example.com", "password": "pass"}
  ]
}
```

**使用**：
- `python -m src openi` - 批量运行所有 OpenI 用户（user1, user2, user3）
- `python -m src openi --user user1` - 只运行指定用户

## 许可证

MIT License
