# AnyRouter 自动登录脚本

使用 Playwright 实现 AnyRouter 的自动登录，支持多种登录方式、Cookie 保存和快速登录功能。

## 功能特性

- ✅ **多种登录方式**：邮箱密码、GitHub OAuth、LinuxDO OAuth
- ✅ 保存登录 Cookie 到本地
- ✅ 支持 Cookie 快速登录（无需重复授权）
- ✅ Cookie 过期自动重新登录
- ✅ 自动复用 GitHub/LinuxDO 登录状态
- ✅ 支持无头模式运行
- ✅ 自动跳转到 API 令牌页面

## 前置要求

- 需要有 LinuxDO 账号（已登录状态）
- Python 3.7+
- Playwright

## 安装步骤

1. 安装 Python 依赖：

```bash
pip install playwright
```

2. 安装浏览器驱动：

```bash
playwright install chromium
```

## 使用方法

### 方式一：配置文件（推荐）

在 `config/users.json` 中添加：

#### 选项1: 使用邮箱密码登录

```json
{
  "site": "anyrouter",
  "login_type": "credentials",
  "email": "your_email@example.com",
  "password": "your_password"
}
```

#### 选项2: 使用 GitHub OAuth 登录

```json
{
  "site": "anyrouter",
  "login_type": "github_oauth"
}
```

**注意**: 使用 GitHub OAuth 时，需确保配置文件中有 GitHub 账号：

```json
{
  "site": "github",
  "username": "your_github_username",
  "password": "your_github_password"
}
```

#### 选项3: 使用 LinuxDo OAuth 登录（默认）

```json
{
  "site": "anyrouter",
  "login_type": "linuxdo_oauth"
}
```

**注意**: 使用 LinuxDo OAuth 时，需确保配置文件中有 LinuxDo 账号：

```json
{
  "site": "linuxdo",
  "email": "your_linuxdo_email@example.com",
  "password": "your_linuxdo_password"
}
```

#### login_type 说明

- `credentials`: 直接使用 AnyRouter 邮箱密码登录
- `github_oauth`: 使用 GitHub OAuth 授权登录（自动复用 GitHub 登录状态）
- `linuxdo_oauth`: 使用 LinuxDo OAuth 授权登录（自动复用 LinuxDo 登录状态，默认）

### 方式二：环境变量

```bash
# AnyRouter 邮箱密码登录
export ANYROUTER_EMAIL='your_email@example.com'
export ANYROUTER_PASSWORD='your_password'
export ANYROUTER_LOGIN_TYPE='credentials'

# 使用 GitHub OAuth 登录
export ANYROUTER_LOGIN_TYPE='github_oauth'
# 需要额外配置 GitHub 凭据：
export GITHUB_USERNAME='your_github_username'
export GITHUB_PASSWORD='your_github_password'

# 使用 LinuxDo OAuth 登录
export ANYROUTER_LOGIN_TYPE='linuxdo_oauth'
# 需要额外配置 LinuxDo 凭据：
export LINUXDO_EMAIL='your_linuxdo_email'
export LINUXDO_PASSWORD='your_linuxdo_password'
```

### 方式三：代码调用

```python
from src.sites.anyrouter.login import login_to_anyrouter, AnyrouterLogin

# 1. 使用默认配置（从 config/users.json 读取）
login_to_anyrouter()

# 2. 无头模式运行
login_to_anyrouter(headless=True)

# 3. 跳过 Cookie 登录
login_to_anyrouter(use_cookie=False)

# 4. 高级用法 - 使用类实例
automation = AnyrouterLogin(headless=False)

# 邮箱密码登录
automation.run(
    use_cookie=True,
    email="user@example.com",
    password="password",
    login_type="credentials"
)

# GitHub OAuth 登录
automation.run(
    use_cookie=True,
    login_type="github_oauth"
)

# LinuxDo OAuth 登录
automation.run(
    use_cookie=True,
    login_type="linuxdo_oauth"
)
```

### 方式四：命令行运行（推荐）

```bash
# 登录所有 AnyRouter 用户（从 config/users.json 读取）
python -m src anyrouter

# 只登录指定 login_type 的用户
python -m src anyrouter --user github_oauth
python -m src anyrouter --user linuxdo_oauth
python -m src anyrouter --user credentials

# 无头模式运行
python -m src anyrouter --headless

# 跳过 Cookie 登录
python -m src anyrouter --no-cookie

# 组合使用
python -m src anyrouter --user github_oauth --headless
```

### 方式五：直接运行模块

```bash
python -m src.sites.anyrouter.login
```

## 配置说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `use_cookie` | 是否优先使用 Cookie 登录 | `True` |
| `headless` | 是否以无头模式运行浏览器 | `False` |
| `login_type` | 登录方式 | `linuxdo_oauth` |

## 文件说明

- `anyrouter_login.py` - 主脚本文件
- `anyrouter_cookies.json` - Cookie 保存文件（首次登录后自动生成）
- `anyrouter_error_screenshot.png` - 错误截图（发生错误时自动生成）

## 工作流程

1. **Cookie 登录（如果可用）**
   - 加载保存的 AnyRouter Cookie
   - 直接访问控制台页面
   - 验证登录状态

2. **OAuth 登录（Cookie 失效或首次登录）**
   
   **阶段 0: 确保 LinuxDO 已登录**
   - 尝试加载 LinuxDO Cookie（如果存在）
   - 验证 LinuxDO Cookie 是否有效
   - 如果 Cookie 无效或不存在，调用 LinuxDO 登录流程
   - 保存 LinuxDO Cookie 供下次使用
   
   **阶段 1: 打开 OAuth 窗口**
   - 访问 AnyRouter 登录页面
   - 关闭系统公告弹窗（支持中英文）
   - 点击"使用 LinuxDO 继续"按钮
   - 如果找不到按钮，自动刷新页面重试
   
   **阶段 2: OAuth 授权**
   - OAuth 窗口打开时，LinuxDO 已处于登录状态
   - 自动点击"允许"按钮并勾选"记住授权"
   - 等待跳转回 AnyRouter
   
   **阶段 3: 验证与保存**
   - 验证登录成功
   - 保存 AnyRouter Cookie

3. **登录后操作**
   - 自动跳转到 API 令牌页面
   - 显示已有令牌数量
   - 保持浏览器打开便于查看

## 技术亮点

### 智能 Cookie 复用
- **自动检测 LinuxDO Cookie**：优先使用已保存的 LinuxDO Cookie
- **无缝回退**：Cookie 无效时自动调用完整登录流程
- **双重缓存**：同时保存 LinuxDO 和 AnyRouter 的 Cookie

### 模块化设计
- **复用 LinuxDO 登录**：直接调用 `LinuxdoLogin` 类，避免重复代码
- **职责分离**：OAuth 流程、LinuxDO 登录、Cookie 管理完全解耦

### 容错能力
- **页面刷新重试**：找不到 OAuth 按钮时自动刷新
- **多选择器支持**：支持中英文弹窗关闭按钮
- **详细日志**：每个步骤都有清晰的日志记录

## 注意事项

1. **自动处理 LinuxDO 登录**：无需手动登录 LinuxDO，脚本会自动处理
2. **配置凭据**：确保在 `config/users.json` 中配置了 `anyrouter` 站点的凭据
3. **安全提示**：请妥善保管 Cookie 文件，不要泄露给他人
4. **Git 提交**：Cookie 文件已添加到 `.gitignore`，不会被提交
5. **Cookie 有效期**：Cookie 会在一定时间后过期，过期后会自动重新登录

## 故障排除

### Cookie 登录失败

如果 Cookie 登录一直失败，可以：
1. 删除 `anyrouter_cookies.json` 文件
2. 确保 LinuxDO 处于登录状态
3. 重新运行脚本进行 OAuth 登录

### 授权页面未找到

如果提示"未找到授权页面"：
1. 检查 LinuxDO 是否处于登录状态
2. 尝试手动登录 LinuxDO
3. 清除浏览器缓存后重试

### 登录超时

如果遇到登录超时：
1. 检查网络连接
2. 确保能正常访问 anyrouter.top 和 linux.do
3. 增加等待时间后重试

## 许可证

MIT License

