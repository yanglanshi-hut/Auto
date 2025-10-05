# Auto - Web 自动化登录工具集 V2

基于 Playwright 的多站点自动化登录工具，支持 Cookie 持久化和快速登录。

**当前版本**: V2（2025-10-05）- 优化架构，提升代码质量

## 特性

- 🎯 **多站点支持**: AnyRouter、Linux.do、OpenI 三个平台
- 🍪 **Cookie 持久化**: 自动保存和加载 Cookie，支持快速登录
- 🔧 **统一 CLI**: 简洁的命令行界面
- 📦 **清晰架构**: 代码、配置、数据完全分离
- 🛡️ **类型安全**: 完善的错误处理和日志记录
- ⚡ **V2 优化**:
  - 统一路径管理（ProjectPaths）
  - 模块化设计（单一职责原则）
  - 修复已知 BUG，提升代码质量

## 项目结构

```
Auto/
├── src/                      # 源代码
│   ├── core/                 # 核心模块
│   │   ├── base.py           # LoginAutomation 基类
│   │   ├── browser.py        # 浏览器管理
│   │   ├── cookies.py        # Cookie 管理
│   │   ├── paths.py          # 🆕 统一路径管理（V2）
│   │   └── logger.py         # 🆕 统一日志配置（V2）
│   ├── sites/                # 站点登录模块
│   │   ├── anyrouter/        # AnyRouter (LinuxDO OAuth)
│   │   ├── linuxdo/          # Linux.do 论坛
│   │   └── openi/            # OpenI 平台（V2 模块化拆分）
│   │       ├── login.py      # 登录逻辑
│   │       ├── popup.py      # 🆕 弹窗处理（V2）
│   │       ├── cloud_task.py # 🆕 任务管理（V2）
│   │       ├── config.py     # 🆕 配置加载（V2）
│   │       └── runner.py     # 🆕 多用户执行（V2）
│   └── __main__.py           # 统一 CLI 入口
├── config/                   # 配置文件
│   ├── users.json.example    # 配置模板
│   └── users.json            # 用户配置（gitignore）
├── data/                     # 运行时数据（gitignore）
│   ├── cookies/              # Cookie 存储
│   ├── logs/                 # 日志文件
│   └── screenshots/          # 错误截图
├── docs/                     # 🆕 文档目录（V2）
│   ├── README.md             # 文档索引
│   └── history/              # 重构历史
├── .gitignore
├── requirements.txt
└── README.md
```

## 快速开始

### 安装依赖

```bash
cd auto-refactored
pip install -r requirements.txt
playwright install chromium
```

### 配置

1. 复制配置模板：
```bash
cp config/users.json.example config/users.json
```

2. 编辑 `config/users.json` 填写 OpenI 用户信息（其他站点暂时使用硬编码凭证）

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

## 从旧项目迁移

如果你有旧的 Cookie 和配置文件，使用迁移脚本：

```bash
# 在旧项目根目录运行
cd /path/to/old/Auto
python auto-refactored/scripts/migrate.py --dry-run  # 预览
python auto-refactored/scripts/migrate.py            # 执行迁移
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

### AnyRouter
- **登录方式**: LinuxDO OAuth 授权
- **特性**: 自动处理授权弹窗、记住授权、导航到 API 令牌页

### Linux.do
- **登录方式**: 账号密码表单登录
- **特性**: Cookie 快速登录、自动处理登录表单

### OpenI
- **登录方式**: 账号密码登录
- **特性**:
  - 多用户批量处理
  - 云脑任务自动化（启动/停止任务赚取积分）
  - 每用户独立 Cookie 管理
  - 详细日志记录
- **V2 改进**: 模块化拆分（login.py + popup.py + cloud_task.py），代码复杂度降低 68%

## V2 改进说明

V2 版本（2025-10-05）基于 Linus Torvalds 的工程哲学进行了深度优化：

### 核心改进

1. **修复 BUG**
   - 修复截图路径错误（从 `data/cookies/` 修正为 `data/screenshots/`）

2. **统一路径管理**
   - 新增 `src/core/paths.py`：ProjectPaths dataclass
   - 消除分散的路径计算逻辑，导入时检测一次

3. **统一日志配置**
   - 新增 `src/core/logger.py`：setup_logger() 工具函数
   - 避免重复的日志配置代码

4. **OpeniLogin 职责分离**
   - 从 443 行拆分为 5 个模块（login.py、popup.py、cloud_task.py、config.py、runner.py）
   - 每个模块 <160 行，符合单一职责原则
   - 代码复杂度降低 68%

5. **100% 向后兼容**
   - API 和 CLI 完全保持兼容
   - 配置文件格式不变
   - 无需迁移，直接升级

### 重构历史

详细的重构过程和设计决策，请参阅：
- [V1 重构总结](docs/history/PROJECT_REFACTORING_SUMMARY.md) - 2025-10-03
- [V2 重构总结](docs/history/REFACTORING_V2_SUMMARY.md) - 2025-10-05

## 许可证

MIT License

