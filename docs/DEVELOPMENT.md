# 开发指南

## 目录
- [环境准备](#环境准备)
- [项目设置](#项目设置)
- [添加新站点](#添加新站点)
- [代码规范](#代码规范)
- [测试策略](#测试策略)
- [调试技巧](#调试技巧)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

## 环境准备

### 系统要求
- Python 3.8 或更高版本
- Git
- 支持的操作系统：Windows、Linux、macOS

### 开发工具推荐
- **IDE**: VSCode、PyCharm
- **版本控制**: Git
- **代码格式化**: Black
- **代码检查**: Pylint、Flake8
- **类型检查**: mypy

### 环境设置

1. **克隆仓库**
```bash
git clone https://github.com/yourusername/Auto.git
cd Auto
```

2. **创建虚拟环境**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖（如果有）
```

4. **安装 Playwright 浏览器**
```bash
playwright install chromium
# 或安装所有浏览器
playwright install
```

5. **配置 Git hooks**（可选）
```bash
pre-commit install
```

## 项目设置

### 目录结构理解
```
Auto/
├── src/                    # 源代码
│   ├── core/              # 核心模块
│   │   ├── base.py       # 基类定义
│   │   ├── browser.py    # 浏览器管理
│   │   ├── cookies.py    # Cookie管理
│   │   ├── config.py     # 配置加载
│   │   ├── logger.py     # 日志设置
│   │   └── paths.py      # 路径管理
│   ├── sites/            # 站点实现
│   │   └── <site_name>/  # 具体站点
│   └── __main__.py       # CLI入口
├── config/               # 配置文件
├── data/                 # 运行时数据
├── docs/                 # 文档
├── scripts/              # 辅助脚本
└── tests/                # 测试文件
```

### 配置开发环境

1. **复制配置模板**
```bash
cp config/users.json.example config/users.json
```

2. **编辑配置文件**
```json
{
  "config": {
    "headless": false,  // 开发时建议关闭无头模式
    "use_cookies": true,
    "cookie_expire_days": 30
  },
  "users": [
    {
      "site": "test_site",
      "username": "test_user",
      "password": "test_pass"
    }
  ]
}
```

3. **设置环境变量**（可选）
```bash
export DEBUG=True
export LOG_LEVEL=DEBUG
```

## 添加新站点

### 步骤 1: 创建站点目录

```bash
mkdir -p src/sites/newsite
touch src/sites/newsite/__init__.py
touch src/sites/newsite/login.py
```

### 步骤 2: 实现登录类

创建 `src/sites/newsite/login.py`:

```python
"""NewSite 登录自动化实现。"""

from typing import Optional
from playwright.sync_api import Page
from src.core.base import LoginAutomation
from src.core.logger import setup_logger
from src.core.paths import get_project_paths


class NewSiteLogin(LoginAutomation):
    """NewSite 登录自动化类。"""

    def __init__(self, headless: bool = False):
        """初始化 NewSite 登录实例。

        参数:
            headless: 是否运行无头模式
        """
        super().__init__('newsite', headless=headless)

        # 设置站点特定的日志
        self.logger = setup_logger(
            'newsite',
            get_project_paths().logs / 'newsite.log'
        )

        # 站点特定配置
        self.login_url = 'https://newsite.com/login'
        self.home_url = 'https://newsite.com'

    def verify_login(self, page: Page) -> bool:
        """验证是否已登录。

        参数:
            page: Playwright 页面对象

        返回:
            bool: 如果已登录返回 True
        """
        try:
            # 方法1: 检查特定元素
            if page.locator('.user-avatar').count() > 0:
                self.logger.info("检测到用户头像，已登录")
                return True

            # 方法2: 检查 URL
            if '/dashboard' in page.url:
                self.logger.info("已在仪表板页面，已登录")
                return True

            # 方法3: 检查 Cookie
            cookies = page.context.cookies()
            for cookie in cookies:
                if cookie['name'] == 'session_token':
                    self.logger.info("检测到会话 Cookie，已登录")
                    return True

            return False

        except Exception as e:
            self.logger.error(f"验证登录状态时出错: {e}")
            return False

    def do_login(
        self,
        page: Page,
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ) -> bool:
        """执行登录操作。

        参数:
            page: Playwright 页面对象
            username: 用户名
            password: 密码
            **kwargs: 其他参数

        返回:
            bool: 登录是否成功
        """
        try:
            self.logger.info(f"开始登录用户: {username}")

            # 导航到登录页面
            page.goto(self.login_url, wait_until='domcontentloaded')
            self.logger.debug("已导航到登录页面")

            # 等待登录表单加载
            page.wait_for_selector('input[name="username"]', timeout=10000)

            # 填写登录表单
            page.fill('input[name="username"]', username)
            page.fill('input[name="password"]', password)
            self.logger.debug("已填写登录凭据")

            # 处理可能的验证码（示例）
            if page.locator('#captcha').count() > 0:
                self.logger.warning("检测到验证码，需要手动处理")
                # 等待用户手动输入验证码
                page.wait_for_timeout(30000)

            # 点击登录按钮
            page.click('button[type="submit"]')
            self.logger.debug("已点击登录按钮")

            # 等待登录完成
            page.wait_for_load_state('networkidle')

            # 处理可能的弹窗
            self._handle_popups(page)

            # 验证登录结果
            if self.verify_login(page):
                self.logger.info("登录成功")
                return True
            else:
                self.logger.error("登录失败：未能验证登录状态")
                return False

        except Exception as e:
            self.logger.error(f"登录过程中出错: {e}")
            return False

    def after_login(self, page: Page, **credentials) -> None:
        """登录成功后的操作。

        参数:
            page: Playwright 页面对象
            **credentials: 登录凭据
        """
        try:
            self.logger.info("执行登录后任务")

            # 示例：导航到特定页面
            page.goto(f"{self.home_url}/dashboard")

            # 示例：执行签到
            if page.locator('.sign-in-button').count() > 0:
                page.click('.sign-in-button')
                self.logger.info("已完成每日签到")

            # 示例：收集用户信息
            user_info = self._get_user_info(page)
            if user_info:
                self.logger.info(f"用户信息: {user_info}")

        except Exception as e:
            self.logger.error(f"执行登录后任务时出错: {e}")

    def _handle_popups(self, page: Page) -> None:
        """处理可能的弹窗。

        参数:
            page: Playwright 页面对象
        """
        popup_selectors = [
            '.modal-close',
            '.popup-dismiss',
            'button:has-text("Close")',
            'button:has-text("关闭")',
        ]

        for selector in popup_selectors:
            try:
                if page.locator(selector).count() > 0:
                    page.click(selector)
                    self.logger.debug(f"已关闭弹窗: {selector}")
                    page.wait_for_timeout(500)
            except Exception:
                pass

    def _get_user_info(self, page: Page) -> Optional[dict]:
        """获取用户信息。

        参数:
            page: Playwright 页面对象

        返回:
            dict: 用户信息字典
        """
        try:
            user_info = {}

            # 获取用户名
            username_elem = page.locator('.username')
            if username_elem.count() > 0:
                user_info['username'] = username_elem.inner_text()

            # 获取其他信息...

            return user_info
        except Exception:
            return None
```

### 步骤 3: 添加 CLI 命令

编辑 `src/__main__.py`，添加新站点命令：

```python
# 导入新站点
from src.sites.newsite.login import NewSiteLogin

# 在 main 函数中添加命令
@click.command()
@click.option('--headless', is_flag=True, help='Run in headless mode')
@click.option('--no-cookie', is_flag=True, help='Don\'t use cookies')
@click.option('--user', help='Specify username')
def newsite(headless, no_cookie, user):
    """NewSite login automation."""
    # 加载配置
    config = ConfigLoader.load_config()
    users = ConfigLoader.get_site_users('newsite')

    # 如果指定了用户，过滤用户列表
    if user:
        users = [u for u in users if u.get('username') == user]

    # 执行登录
    for user_config in users:
        login = NewSiteLogin(headless=headless)
        success = login.run(
            use_cookie=not no_cookie,
            **user_config
        )

        if success:
            click.echo(f"✓ NewSite login successful for {user_config.get('username')}")
        else:
            click.echo(f"✗ NewSite login failed for {user_config.get('username')}")

# 注册命令
cli.add_command(newsite)
```

### 步骤 4: 更新配置模板

编辑 `config/users.json.example`，添加新站点示例：

```json
{
  "users": [
    {
      "site": "newsite",
      "username": "your_username",
      "password": "your_password"
    }
  ]
}
```

### 步骤 5: 添加测试

创建 `tests/test_newsite.py`:

```python
import pytest
from unittest.mock import Mock, patch
from src.sites.newsite.login import NewSiteLogin


class TestNewSiteLogin:
    """NewSite 登录测试。"""

    @pytest.fixture
    def login_instance(self):
        """创建登录实例。"""
        return NewSiteLogin(headless=True)

    def test_verify_login_with_avatar(self, login_instance):
        """测试通过头像验证登录。"""
        page = Mock()
        page.locator.return_value.count.return_value = 1

        assert login_instance.verify_login(page) is True
        page.locator.assert_called_with('.user-avatar')

    def test_verify_login_not_logged_in(self, login_instance):
        """测试未登录状态。"""
        page = Mock()
        page.locator.return_value.count.return_value = 0
        page.url = 'https://newsite.com/login'
        page.context.cookies.return_value = []

        assert login_instance.verify_login(page) is False

    @patch('src.sites.newsite.login.NewSiteLogin.verify_login')
    def test_do_login_success(self, mock_verify, login_instance):
        """测试成功登录。"""
        mock_verify.return_value = True
        page = Mock()

        result = login_instance.do_login(
            page,
            username='test_user',
            password='test_pass'
        )

        assert result is True
        page.goto.assert_called()
        page.fill.assert_called()
        page.click.assert_called()
```

### 步骤 6: 文档更新

更新 `README.md`，添加新站点说明：

```markdown
### NewSite
- **登录方式**: 用户名密码登录
- **配置方式**: `config/users.json` - `users` 数组（`site: "newsite"`）
- **特性**:
  - Cookie 快速登录
  - 自动签到
  - 弹窗处理

**使用示例**:
```bash
python -m src newsite
python -m src newsite --headless
python -m src newsite --user specific_user
```
```

## 代码规范

### Python 风格指南

遵循 PEP 8 规范，主要原则：

1. **缩进**: 使用 4 个空格
2. **行长度**: 最大 100 字符（文档字符串 72 字符）
3. **空行**:
   - 顶级函数和类之间空 2 行
   - 类方法之间空 1 行
4. **导入顺序**:
   ```python
   # 标准库
   import os
   import sys

   # 第三方库
   from playwright.sync_api import Page

   # 本地模块
   from src.core.base import LoginAutomation
   ```

### 命名约定

```python
# 模块名: 小写，下划线分隔
login_automation.py

# 类名: PascalCase
class LoginAutomation:
    pass

# 函数和方法: snake_case
def verify_login():
    pass

# 常量: 大写，下划线分隔
MAX_RETRY_COUNT = 3

# 私有方法: 前缀单下划线
def _internal_method():
    pass
```

### 文档字符串

使用 Google 风格的文档字符串：

```python
def function_name(param1: str, param2: int = None) -> bool:
    """函数的简短描述。

    更详细的描述（如需要）。
    可以多行。

    参数:
        param1: 第一个参数的描述
        param2: 第二个参数的描述，默认为 None

    返回:
        返回值的描述

    Raises:
        ValueError: 如果 param1 为空

    示例:
        >>> function_name("test", 42)
        True
    """
    pass
```

### 类型注解

使用类型注解提高代码可读性：

```python
from typing import Optional, List, Dict, Any, Union

def process_data(
    data: List[Dict[str, Any]],
    filter_key: Optional[str] = None
) -> Union[List[Dict], None]:
    """处理数据的函数。"""
    pass
```

## 测试策略

### 测试结构

```
tests/
├── unit/              # 单元测试
│   ├── test_core/
│   └── test_sites/
├── integration/       # 集成测试
├── e2e/              # 端到端测试
└── conftest.py       # pytest 配置
```

### 编写测试

1. **单元测试示例**:
```python
import pytest
from src.core.cookies import CookieManager

def test_cookie_expiry():
    """测试 Cookie 过期检查。"""
    manager = CookieManager()

    # 测试过期的 Cookie
    assert manager.check_cookie_expiry('test', expire_days=0) is False

    # 测试有效的 Cookie
    assert manager.check_cookie_expiry('test', expire_days=30) is True
```

2. **集成测试示例**:
```python
@pytest.mark.integration
def test_login_flow():
    """测试完整登录流程。"""
    login = TestSiteLogin(headless=True)

    # 不使用 Cookie 的登录
    success = login.run(
        use_cookie=False,
        username='test',
        password='test'
    )

    assert success is True
```

3. **Mock 测试示例**:
```python
from unittest.mock import patch, Mock

@patch('src.sites.test.login.TestLogin.verify_login')
def test_with_mock(mock_verify):
    """使用 Mock 的测试。"""
    mock_verify.return_value = True

    # 测试代码...
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_core/test_base.py

# 运行带覆盖率的测试
pytest --cov=src --cov-report=html

# 运行特定标记的测试
pytest -m "not integration"
```

## 调试技巧

### 1. 使用非无头模式

开发时关闭无头模式以便观察浏览器行为：

```python
login = SiteLogin(headless=False)
```

### 2. 添加调试断点

使用 Python 调试器：

```python
import pdb

def do_login(self, page, **credentials):
    pdb.set_trace()  # 设置断点
    # 代码继续...
```

或使用 IPython：

```python
from IPython import embed

def do_login(self, page, **credentials):
    embed()  # 进入 IPython shell
    # 代码继续...
```

### 3. Playwright 调试模式

```python
# 启用 Playwright 调试
page.pause()  # 暂停执行，打开 Playwright Inspector
```

### 4. 慢速执行

```python
# 减慢执行速度
page.set_default_timeout(60000)  # 60秒超时
page.wait_for_timeout(2000)      # 等待 2 秒
```

### 5. 截图调试

```python
# 在关键步骤截图
page.screenshot(path='debug_step1.png')
```

### 6. 网络调试

```python
# 监听网络请求
def log_request(request):
    print(f">> {request.method} {request.url}")

page.on("request", log_request)
```

### 7. 日志调试

```python
import logging

# 设置详细日志级别
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("详细调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
```

## 最佳实践

### 1. 错误处理

```python
def do_login(self, page, **credentials):
    try:
        # 主要逻辑
        pass
    except TimeoutError:
        self.logger.error("登录超时")
        return False
    except Exception as e:
        self.logger.error(f"未预期的错误: {e}")
        # 保存截图用于调试
        page.screenshot(path=self._error_screenshot_path())
        raise
```

### 2. 等待策略

```python
# 不好的做法
page.wait_for_timeout(5000)  # 固定等待

# 好的做法
page.wait_for_selector('.element', state='visible')
page.wait_for_load_state('networkidle')
```

### 3. 选择器最佳实践

```python
# 优先级（从高到低）
1. page.get_by_test_id("login-button")  # 测试 ID
2. page.get_by_role("button", name="Login")  # 角色
3. page.get_by_text("Login")  # 文本
4. page.locator("#login-btn")  # ID
5. page.locator(".login-button")  # 类名
6. page.locator("button[type='submit']")  # 属性
7. page.locator("div > button")  # 结构（最不稳定）
```

### 4. 资源管理

```python
def run(self):
    browser = None
    try:
        browser = self.browser_manager.launch()
        # 使用浏览器...
    finally:
        if browser:
            browser.close()
```

### 5. 配置管理

```python
# 使用配置类而不是硬编码
class SiteConfig:
    LOGIN_URL = os.getenv('SITE_LOGIN_URL', 'https://default.com/login')
    TIMEOUT = int(os.getenv('SITE_TIMEOUT', '30000'))
```

### 6. 代码复用

```python
# 创建通用工具函数
def safe_click(page: Page, selector: str, timeout: int = 5000) -> bool:
    """安全地点击元素。"""
    try:
        page.wait_for_selector(selector, timeout=timeout)
        page.click(selector)
        return True
    except Exception:
        return False
```

## 常见问题

### Q1: 如何处理验证码？

**方案 1**: 等待手动输入
```python
if page.locator('#captcha').count() > 0:
    print("请手动输入验证码...")
    page.wait_for_timeout(30000)  # 等待 30 秒
```

**方案 2**: 使用 OCR 服务
```python
# 集成第三方 OCR 服务
from some_ocr_service import solve_captcha

captcha_image = page.locator('#captcha-img').screenshot()
captcha_text = solve_captcha(captcha_image)
page.fill('#captcha-input', captcha_text)
```

### Q2: 如何处理动态加载的内容？

```python
# 等待元素出现
page.wait_for_selector('.dynamic-content', state='visible')

# 或等待网络空闲
page.wait_for_load_state('networkidle')

# 或使用自定义等待
page.wait_for_function("document.querySelector('.content').innerText.length > 0")
```

### Q3: 如何处理多个弹窗或标签页？

```python
# 处理新标签页
with page.expect_popup() as popup_info:
    page.click('.open-new-tab')
popup = popup_info.value

# 在新标签页操作
popup.fill('input', 'value')
popup.close()

# 处理多个弹窗
pages = context.pages
for p in pages[1:]:  # 跳过主页面
    p.close()
```

### Q4: 如何模拟更真实的用户行为？

```python
# 添加随机延迟
import random

def random_delay():
    delay = random.uniform(0.5, 2.0)
    page.wait_for_timeout(delay * 1000)

# 模拟打字
page.type('input', 'text', delay=100)  # 每个字符延迟 100ms

# 模拟鼠标移动
page.mouse.move(100, 200)
page.mouse.click(100, 200)
```

### Q5: 如何处理请求拦截和修改？

```python
def handle_route(route):
    # 修改请求头
    headers = route.request.headers
    headers['User-Agent'] = 'Custom User Agent'
    route.continue_(headers=headers)

page.route('**/*', handle_route)
```

### Q6: 如何优化性能？

```python
# 1. 禁用图片加载
context = browser.new_context(
    viewport={'width': 1280, 'height': 720},
    ignore_https_errors=True,
    # 禁用图片
    extra_http_headers={'Accept': 'text/html'}
)

# 2. 复用浏览器上下文
# 不要为每个操作创建新的浏览器

# 3. 并行处理
import asyncio
from playwright.async_api import async_playwright

async def process_user(user):
    # 异步处理用户
    pass

async def main():
    tasks = [process_user(user) for user in users]
    await asyncio.gather(*tasks)
```

## 进阶主题

### 自定义中间件

```python
class LoginMiddleware:
    """登录中间件基类。"""

    def before_login(self, page: Page, credentials: dict):
        """登录前执行。"""
        pass

    def after_login(self, page: Page, result: bool):
        """登录后执行。"""
        pass

# 使用中间件
class CustomLogin(LoginAutomation):
    def __init__(self):
        self.middlewares = [
            LoggingMiddleware(),
            MetricsMiddleware(),
        ]
```

### 插件系统

```python
# 定义插件接口
class Plugin:
    def on_init(self, automation):
        pass

    def on_login_start(self, page):
        pass

    def on_login_complete(self, success):
        pass

# 加载插件
def load_plugins():
    plugins = []
    for entry_point in pkg_resources.iter_entry_points('auto.plugins'):
        plugin_class = entry_point.load()
        plugins.append(plugin_class())
    return plugins
```

### 分布式执行

```python
# 使用 Celery 实现分布式任务
from celery import Celery

app = Celery('auto', broker='redis://localhost:6379')

@app.task
def login_task(site, username, password):
    login = create_login_instance(site)
    return login.run(username=username, password=password)
```

## 资源链接

- [Playwright 文档](https://playwright.dev/python/)
- [Python 最佳实践](https://docs.python-guide.org/)
- [PEP 8 风格指南](https://www.python.org/dev/peps/pep-0008/)
- [pytest 文档](https://docs.pytest.org/)
- [Type Hints 文档](https://docs.python.org/3/library/typing.html)