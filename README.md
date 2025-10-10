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

使用 `config/users.json` 统一配置所有站点的凭据和参数。

1. 复制配置模板：
```bash
cp config/users.json.example config/users.json
```

2. 编辑 `config/users.json`：
```json
{
  "users": [
    {"site": "openi", "username": "用户名1", "password": "密码1"},
    {"site": "linuxdo", "email": "邮箱@example.com", "password": "密码"},
    {"site": "anyrouter", "email": "邮箱@example.com", "password": "密码"}
  ],
  "defaults": {
    "cookie_expire_days": 30,
    "headless": true
  },
  "sites": {
    "openi": {
      "task_name": "image",
      "run_duration": 15
    }
  }
}
```
### 从旧格式迁移

如果你使用的是旧版配置格式，可以使用迁移脚本自动转换：

```bash
# 查看迁移后的结果（不写入）
python scripts/migrate_config.py --dry-run

# 正式迁移（自动备份为 users.json.backup）
python scripts/migrate_config.py

# 查看帮助
python scripts/migrate_config.py --help
```

支持迁移的旧格式：
- 旧版 users + config 格式
- credentials 格式
- 旧版 OpenI 单站点格式


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

## 生产环境部署

- 目标：多用户 Cookie 批量管理与定时刷新，便于无人值守运行。

### 初始化 Cookie（一次性/按需）

```bash
./scripts/init_cookies.sh                # 初始化所有站点（OpenI 全部用户 + LinuxDO）
./scripts/init_cookies.sh --site openi   # 仅初始化 OpenI
./scripts/init_cookies.sh --site linuxdo # 仅初始化 LinuxDO
./scripts/init_cookies.sh --user yls     # 仅初始化指定 OpenI 用户
```

脚本将日志写入 `data/logs/cookie_init_<timestamp>.log`，每行包含时间/站点/用户/状态。

### 刷新 Cookie（周期性）

```bash
./scripts/refresh_cookies.sh                 # 检测并刷新超过 20 天的 Cookie
./scripts/refresh_cookies.sh --dry-run       # 仅查看将要刷新哪些
./scripts/refresh_cookies.sh --force         # 忽略阈值，强制刷新所有目标
./scripts/refresh_cookies.sh --workers 5     # 并发处理（默认 3）
./scripts/refresh_cookies.sh --site openi    # 仅处理 OpenI
./scripts/refresh_cookies.sh --site linuxdo  # 仅处理 LinuxDO
./scripts/refresh_cookies.sh --user yls      # 仅处理指定 OpenI 用户
```

刷新日志写入 `data/logs/cookie_refresh_<timestamp>.log`，统计刷新/跳过/失败数。

### 建议的 crontab

以每天凌晨 05:15 运行刷新为例（修改为你的仓库路径）：

```
15 5 * * * /bin/bash -lc 'cd /root/yls/code/Auto && ./scripts/refresh_cookies.sh >> /root/yls/code/Auto/data/logs/cron_refresh.log 2>&1'
```

Tips:
- 首次部署建议先执行 `./scripts/init_cookies.sh` 生成初始 Cookie
- 若服务器无物理显示，LinuxDO 由脚本自动使用 `xvfb-run` 包装 CLI
- OpenI 的 Cookie 已按用户隔离，文件名形如 `openi_<username>_cookies.json`
- 全局配置中的 `cookie_expire_days` 建议设置为 30（默认值已更新）

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
- **凭据配置**: `config/users.json` - `users` 数组（`site: "linuxdo"`）
- **特性**: Cookie 快速登录、自动处理登录表单

### AnyRouter
- **登录方式**: LinuxDO OAuth 授权
- **凭据配置**: `config/users.json` - `users` 数组（`site: "anyrouter"`）
- **特性**: 自动处理授权弹窗、记住授权、导航到 API 令牌页

### OpenI
- **登录方式**: 账号密码登录
- **凭据配置**: `config/users.json` - `users` 数组（`site: "openi"`）
- **特性**:
  - 多用户批量处理（支持并发）
  - 云脑任务自动化（启动/停止任务赚取积分）
  - 每用户独立 Cookie 管理
  - 详细日志记录
## 配置说明

### 配置格式

**新格式**（当前版本）：
```json
{
  "users": [
    {"site": "openi", "username": "u", "password": "p"},
    {"site": "linuxdo", "email": "e", "password": "p"},
    {"site": "anyrouter", "email": "e", "password": "p"}
  ],
  "defaults": {
    "cookie_expire_days": 30,
    "headless": true
  },
  "sites": {
    "openi": {
      "task_name": "image",
      "run_duration": 15
    }
  }
}
```

**说明**：
- `users`: 用户凭据列表，通过 `site` 字段区分站点
- `defaults`: 全局默认配置（cookie 过期时间、headless 模式等）
- `sites`: 站点特定配置（仅 OpenI 需要）
- 支持同站点多账号：添加多个相同 `site` 的条目即可

### 旧格式迁移

如果你使用的是旧版配置格式，使用迁移脚本：
```bash
python scripts/migrate_config.py
```
## 许可证

MIT License
