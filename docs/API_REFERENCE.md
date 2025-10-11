# API 参考文档

## 目录
- [核心基类](#核心基类)
- [浏览器管理](#浏览器管理)
- [Cookie 管理](#cookie-管理)
- [配置管理](#配置管理)
- [日志管理](#日志管理)
- [路径管理](#路径管理)
- [站点实现](#站点实现)

## 核心基类

### `LoginAutomation`
基类，所有站点登录自动化类的父类。提供统一的登录流程框架。

**位置**: `src/core/base.py`

#### 构造函数
```python
def __init__(
    self,
    site_name: str,
    *,
    headless: bool = False,
    cookie_dir: Optional[Path] = None,
    browser_kwargs: Optional[Dict[str, Any]] = None,
    context_kwargs: Optional[Dict[str, Any]] = None,
    cookie_expire_days: int = 30,
) -> None
```

**参数**:
- `site_name` (str): 站点名称标识符
- `headless` (bool): 是否运行无头模式，默认 False
- `cookie_dir` (Optional[Path]): Cookie 存储目录，默认使用系统路径
- `browser_kwargs` (Optional[Dict]): 传递给浏览器启动的额外参数
- `context_kwargs` (Optional[Dict]): 传递给浏览器上下文的额外参数
- `cookie_expire_days` (int): Cookie 有效期（天），默认 30

#### 核心方法

##### `run()`
```python
def run(
    self,
    *,
    use_cookie: bool = True,
    verify_url: Optional[str] = None,
    cookie_expire_days: Optional[int] = None,
    **credentials,
) -> bool
```
执行完整的登录流程。

**参数**:
- `use_cookie` (bool): 是否使用 Cookie 快速登录，默认 True
- `verify_url` (Optional[str]): 验证登录的 URL
- `cookie_expire_days` (Optional[int]): 覆盖默认的 Cookie 有效期
- `**credentials`: 登录凭据（如 username, password, email 等）

**返回**: bool - 登录是否成功

##### `try_cookie_login()`
```python
def try_cookie_login(
    self,
    page: Page,
    *,
    verify_url: Optional[str] = None,
    expire_days: Optional[int] = None,
    required_metadata: Optional[Dict[str, Any]] = None,
) -> bool
```
尝试使用已保存的 Cookie 进行登录。

**参数**:
- `page` (Page): Playwright 页面对象
- `verify_url` (Optional[str]): 验证 URL
- `expire_days` (Optional[int]): Cookie 有效期
- `required_metadata` (Optional[Dict]): 必需的元数据匹配

**返回**: bool - Cookie 登录是否成功

#### 抽象方法（子类必须实现）

##### `verify_login()`
```python
@abc.abstractmethod
def verify_login(self, page: Page) -> bool
```
验证当前页面是否已登录。

**参数**:
- `page` (Page): Playwright 页面对象

**返回**: bool - 是否已登录

##### `do_login()`
```python
@abc.abstractmethod
def do_login(self, page: Page, **credentials) -> bool
```
执行实际的登录操作。

**参数**:
- `page` (Page): Playwright 页面对象
- `**credentials`: 登录凭据

**返回**: bool - 登录是否成功

#### 钩子方法

##### `after_login()`
```python
def after_login(self, page: Page, **credentials) -> None
```
登录成功后的钩子，可在子类中覆盖以执行额外操作。

**参数**:
- `page` (Page): Playwright 页面对象
- `**credentials`: 登录凭据

## 浏览器管理

### `BrowserManager`
管理 Playwright 浏览器实例的生命周期。

**位置**: `src/core/browser.py`

#### 方法

##### `launch()`
```python
def launch(
    self,
    headless: bool = False,
    **kwargs
) -> Browser
```
启动浏览器实例。

**参数**:
- `headless` (bool): 是否无头模式
- `**kwargs`: 传递给 playwright.chromium.launch() 的额外参数

**返回**: Browser - Playwright 浏览器对象

##### `close()`
```python
def close(self, browser: Optional[Browser]) -> None
```
安全关闭浏览器实例。

**参数**:
- `browser` (Optional[Browser]): 要关闭的浏览器实例

##### `save_error_screenshot()`
```python
def save_error_screenshot(
    self,
    page: Optional[Page],
    path: str
) -> None
```
保存错误截图。

**参数**:
- `page` (Optional[Page]): 页面对象
- `path` (str): 截图保存路径

## Cookie 管理

### `CookieManager`
处理 Cookie 的保存、加载和管理。

**位置**: `src/core/cookies.py`

#### 构造函数
```python
def __init__(self, cookie_dir: Optional[Path] = None)
```

**参数**:
- `cookie_dir` (Optional[Path]): Cookie 存储目录

#### 方法

##### `save_cookies()`
```python
def save_cookies(
    self,
    context: BrowserContext,
    site_name: str,
    username: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None
```
保存浏览器上下文的 Cookie。

**参数**:
- `context` (BrowserContext): 浏览器上下文
- `site_name` (str): 站点名称
- `username` (Optional[str]): 用户名（用于多账号）
- `metadata` (Optional[Dict]): 额外的元数据

##### `load_cookies()`
```python
def load_cookies(
    self,
    context: BrowserContext,
    site_name: str,
    expire_days: int = 30,
    username: Optional[str] = None,
    required_metadata: Optional[Dict[str, Any]] = None
) -> bool
```
加载已保存的 Cookie。

**参数**:
- `context` (BrowserContext): 浏览器上下文
- `site_name` (str): 站点名称
- `expire_days` (int): Cookie 有效期
- `username` (Optional[str]): 用户名
- `required_metadata` (Optional[Dict]): 必需的元数据

**返回**: bool - 是否成功加载

##### `check_cookie_expiry()`
```python
def check_cookie_expiry(
    self,
    site_name: str,
    username: Optional[str] = None,
    expire_days: int = 30
) -> bool
```
检查 Cookie 是否过期。

**参数**:
- `site_name` (str): 站点名称
- `username` (Optional[str]): 用户名
- `expire_days` (int): 有效期天数

**返回**: bool - Cookie 是否有效

##### `get_all_cookies()`
```python
def get_all_cookies(self) -> List[Path]
```
获取所有 Cookie 文件路径。

**返回**: List[Path] - Cookie 文件路径列表

## 配置管理

### `ConfigLoader`
处理配置文件的加载和管理。

**位置**: `src/core/config.py`

#### 方法

##### `load_config()`
```python
@staticmethod
def load_config() -> Dict[str, Any]
```
加载主配置文件。

**返回**: Dict - 配置字典

##### `get_site_users()`
```python
@staticmethod
def get_site_users(site: str) -> List[Dict[str, Any]]
```
获取指定站点的用户配置列表。

**参数**:
- `site` (str): 站点名称

**返回**: List[Dict] - 用户配置列表

##### `get_global_config()`
```python
@staticmethod
def get_global_config() -> Dict[str, Any]
```
获取全局配置项。

**返回**: Dict - 全局配置

##### `migrate_config()`
```python
@staticmethod
def migrate_config(config: Dict[str, Any]) -> Dict[str, Any]
```
迁移旧版本配置到新格式。

**参数**:
- `config` (Dict): 原始配置

**返回**: Dict - 迁移后的配置

## 日志管理

### `setup_logger()`
设置和配置日志记录器。

**位置**: `src/core/logger.py`

```python
def setup_logger(
    name: str,
    log_file: Path,
    level: int = logging.INFO
) -> logging.Logger
```

**参数**:
- `name` (str): 日志记录器名称
- `log_file` (Path): 日志文件路径
- `level` (int): 日志级别，默认 INFO

**返回**: Logger - 配置好的日志记录器

### 日志格式
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## 路径管理

### `ProjectPaths`
管理项目中所有路径的数据类。

**位置**: `src/core/paths.py`

#### 属性
- `root` (Path): 项目根目录
- `config` (Path): 配置目录
- `data` (Path): 数据目录
- `cookies` (Path): Cookie 存储目录
- `logs` (Path): 日志目录
- `screenshots` (Path): 截图目录
- `scripts` (Path): 脚本目录
- `src` (Path): 源代码目录

### `get_project_paths()`
```python
def get_project_paths() -> ProjectPaths
```
获取项目路径配置（单例模式）。

**返回**: ProjectPaths - 路径配置对象

## 站点实现

### 通用接口
所有站点实现都继承自 `LoginAutomation` 基类，必须实现以下方法：

1. `verify_login(page: Page) -> bool`
2. `do_login(page: Page, **credentials) -> bool`

### 站点特定参数

#### LinuxDO
```python
class LinuxdoLogin(LoginAutomation):
    def do_login(self, page: Page, email: str, password: str) -> bool
```

#### AnyRouter
```python
class AnyrouterLogin(LoginAutomation):
    def do_login(
        self,
        page: Page,
        email: Optional[str] = None,
        password: Optional[str] = None,
        login_type: str = "credentials"
    ) -> bool
```

#### OpenI
```python
class OpeniLogin(LoginAutomation):
    def do_login(self, page: Page, username: str, password: str) -> bool
```

#### GitHub
```python
class GithubLogin(LoginAutomation):
    def do_login(self, page: Page, username: str, password: str) -> bool
```

#### ShareYourCC
```python
class ShareYourCCLogin(LoginAutomation):
    def do_login(
        self,
        page: Page,
        email: Optional[str] = None,
        password: Optional[str] = None,
        login_type: str = "linuxdo_oauth"
    ) -> bool
```

## 使用示例

### 基本登录流程
```python
from src.sites.linuxdo.login import LinuxdoLogin

# 创建登录实例
login = LinuxdoLogin(headless=False)

# 执行登录
success = login.run(
    email="user@example.com",
    password="password123"
)

if success:
    print("登录成功")
else:
    print("登录失败")
```

### 自定义站点实现
```python
from src.core.base import LoginAutomation
from playwright.sync_api import Page

class CustomSiteLogin(LoginAutomation):
    def __init__(self, headless: bool = False):
        super().__init__('customsite', headless=headless)

    def verify_login(self, page: Page) -> bool:
        # 检查是否存在用户头像元素
        return page.locator('.user-avatar').count() > 0

    def do_login(self, page: Page, username: str, password: str) -> bool:
        # 导航到登录页
        page.goto('https://customsite.com/login')

        # 填写表单
        page.fill('input[name="username"]', username)
        page.fill('input[name="password"]', password)

        # 提交
        page.click('button[type="submit"]')

        # 等待登录完成
        page.wait_for_load_state('networkidle')

        # 验证登录
        return self.verify_login(page)

    def after_login(self, page: Page, **credentials) -> None:
        # 登录后执行额外操作
        print("执行登录后的自动化任务...")
```

### 批量用户处理
```python
from src.core.config import ConfigLoader
from src.sites.openi.runner import run_all_users

# 获取所有 OpenI 用户
users = ConfigLoader.get_site_users('openi')

# 批量执行
for user in users:
    print(f"处理用户: {user['username']}")
    # 执行登录和任务...
```

## 错误处理

所有 API 方法都包含异常处理机制：

1. **超时处理**: 所有网络操作都有超时设置
2. **截图保存**: 发生错误时自动保存页面截图
3. **日志记录**: 所有操作都记录到日志文件
4. **优雅降级**: Cookie 失败时回退到密码登录

## 性能考虑

1. **Cookie 缓存**: 减少重复登录
2. **并发限制**: 避免触发反爬虫机制
3. **智能等待**: 使用 Playwright 的智能等待机制
4. **资源管理**: 自动清理浏览器资源

## 安全最佳实践

1. **凭据存储**: 敏感信息不应硬编码
2. **Cookie 安全**: Cookie 文件应设置适当权限
3. **日志脱敏**: 日志中不记录密码等敏感信息
4. **HTTPS 强制**: 始终使用 HTTPS 连接