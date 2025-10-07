# ShareYourCC 自动化登录

ShareYourCC (https://shareyour.cc/) 自动化登录脚本，支持邮箱密码和 LinuxDo OAuth 登录。

## 功能特性

### 1. Cookie 自动登录
- 优先使用保存的 Cookie 进行快速登录
- Cookie 过期后自动重新登录
- 默认 Cookie 有效期检查

### 2. 邮箱密码登录
- 支持邮箱和密码直接登录
- 适配对话框和独立页面两种登录界面
- 智能表单元素查找

### 3. LinuxDo OAuth 登录
- 支持使用 LinuxDo 账号 OAuth 授权登录
- 自动复用 LinuxDo 登录状态
- 处理新窗口和当前页面跳转两种方式
- 自动授权确认流程

### 4. 智能跳转处理
- 自动检测页面跳转或对话框
- 等待 OAuth 回调完成
- 多重登录状态验证

## 使用方法

### 方式一：配置文件

在 `config/users.json` 中添加：

```json
{
  "site": "shareyourcc",
  "email": "your_email@example.com",
  "password": "your_password"
}
```

### 方式二：环境变量

```bash
# ShareYourCC 邮箱密码登录
export SHAREYOURCC_EMAIL='your_email@example.com'
export SHAREYOURCC_PASSWORD='your_password'

# 或使用 LinuxDo OAuth 登录（需要 LinuxDo 凭据）
export LINUXDO_EMAIL='your_linuxdo_email'
export LINUXDO_PASSWORD='your_linuxdo_password'
```

### 方式三：代码调用

```python
from src.sites.shareyourcc.login import login_to_shareyourcc

# 使用邮箱密码登录
login_to_shareyourcc(
    email="your_email@example.com",
    password="your_password"
)

# 使用 LinuxDo OAuth 登录（不提供邮箱密码，将自动使用 OAuth）
login_to_shareyourcc()  # 需要配置 LinuxDo 凭据

# 跳过 Cookie 登录
login_to_shareyourcc(
    email="your_email@example.com",
    password="your_password",
    use_cookie=False
)

# 无头模式运行
login_to_shareyourcc(
    email="your_email@example.com",
    password="your_password",
    headless=True
)
```

### 方式四：直接运行

```bash
python -m src.sites.shareyourcc.login
```

## 登录流程

### 邮箱密码登录流程
1. 检查是否有有效 Cookie（如果 `use_cookie=True`）
2. 打开 ShareYourCC 首页
3. 点击登录按钮（处理页面跳转或对话框）
4. 填写邮箱和密码
5. 提交登录
6. 验证登录状态
7. 保存 Cookie（下次可快速登录）

### LinuxDo OAuth 登录流程
1. 检查是否有有效 Cookie
2. 确保 LinuxDo 已登录（复用 LinuxDo Cookie 或执行登录）
3. 打开 ShareYourCC 首页
4. 点击登录按钮
5. 点击 "使用 LINUX DO 登录" 按钮
6. 跳转到 LinuxDo OAuth 授权页面
7. 自动确认授权（勾选"记住授权"并点击"允许"）
8. 等待 OAuth 回调完成
9. 验证登录状态
10. 保存 Cookie

## 登录后自动化操作

登录成功后，脚本会自动执行以下操作：

### 1. 关闭弹窗
- 自动检测并关闭页面上的所有弹窗
- 支持多种弹窗关闭按钮（关闭、×、Close 等）
- 只点击可见的关闭按钮，避免误操作
- 详细日志显示关闭了多少个弹窗

### 2. 每日签到
- 自动查找并点击签到按钮/卡片
- 支持卡片式和按钮式两种布局
- 支持"每日签到"、"签到"、"已签到"等多种文本
- 自动滚动到元素位置确保可见
- 智能遍历多个匹配元素，点击第一个可点击的
- 如果今日已签到，会跳过并记录日志

### 3. 刷新页面
- 签到完成后自动刷新页面

### 4. 幸运抽奖
- 刷新后自动查找并点击抽奖按钮/卡片
- 支持卡片式和按钮式两种布局
- 优先匹配"幸运抽奖"+"赠送公益余额"组合
- 自动滚动到元素位置确保可见
- 智能遍历多个匹配元素，点击第一个可点击的
- 如果今日已抽奖，会跳过并记录日志

### 操作流程
```
登录 → 导航到仪表板 → 关闭弹窗 → 签到 → 刷新 → 抽奖 → 完成
```

## 登录状态验证

脚本会通过以下方式验证登录成功：

1. 检查 URL 是否在仪表板页面（`/dashboard` 或 `/console`）
2. 检查是否有用户菜单按钮
3. 检查顶部导航栏是否没有"登录"按钮
4. 检查是否在 API 密钥页面

## Cookie 管理

- Cookie 保存位置：`data/cookies/shareyourcc_cookies.json`
- LinuxDo Cookie：`data/cookies/linuxdo_cookies.json`
- Cookie 默认有效期：30 天（可配置）

## 故障排除

### 问题：登录按钮点击后无响应
- 原因：页面加载未完成或元素选择器变化
- 解决：检查日志，脚本会自动尝试多种选择器

### 问题：OAuth 授权失败
- 原因：LinuxDo 未登录或 Cookie 过期
- 解决：脚本会自动执行 LinuxDo 完整登录流程

### 问题：登录验证失败
- 原因：页面加载慢或登录状态检测不准确
- 解决：脚本会自动刷新页面重新验证

## 日志位置

- 日志文件：`logs/shareyourcc.log`
- 错误截图：`logs/screenshots/shareyourcc_*.png`

## 技术特性

- **智能等待**：根据页面加载状态动态等待
- **多选择器**：使用多种选择器确保元素查找成功
- **错误处理**：完善的异常捕获和错误日志
- **状态复用**：复用 LinuxDo 登录状态，减少重复登录
- **跳转适配**：同时支持对话框和页面跳转两种登录方式
- **自动化操作**：登录后自动执行签到和抽奖
- **智能重试**：多种按钮选择器确保操作成功

## 注意事项

1. ShareYourCC 主要使用 OAuth 登录，建议优先配置 LinuxDo 凭据
2. 首次运行时会打开浏览器窗口，建议非无头模式观察流程
3. Cookie 会定期过期，脚本会自动重新登录
4. 登录成功后会自动执行：导航到仪表板 → 关闭弹窗 → 签到 → 抽奖
5. 如果今日已签到或已抽奖，脚本会记录日志并跳过
6. 建议每天运行一次脚本以完成签到和抽奖

## 依赖项

- Playwright
- 项目基础模块（LoginAutomation、CookieManager等）
- LinuxDo 登录模块（用于 OAuth 登录）
