# 站点集成指南

## 目录
- [支持的站点](#支持的站点)
- [LinuxDO](#linuxdo)
- [AnyRouter](#anyrouter)
- [OpenI](#openi)
- [GitHub](#github)
- [ShareYourCC](#shareyourcc)
- [站点特性对比](#站点特性对比)
- [常见问题](#常见问题)

## 支持的站点

| 站点 | 登录方式 | Cookie 支持 | 自动化任务 | 多账号 |
|------|----------|------------|------------|---------|
| LinuxDO | 账号密码 | ✅ | ❌ | ✅ |
| AnyRouter | OAuth/密码 | ✅ | ❌ | ✅ |
| OpenI | 账号密码 | ✅ | ✅ 云脑任务 | ✅ |
| GitHub | 账号密码+2FA | ✅ | ❌ | ✅ |
| ShareYourCC | OAuth/邮箱 | ✅ | ✅ 签到/抽奖 | ✅ |

## LinuxDO

### 概述
Linux.do 是一个技术社区论坛，支持账号密码登录。

### 功能特性
- ✅ Cookie 快速登录
- ✅ 自动处理登录表单
- ✅ 多账号支持
- ❌ 自动签到（站点不支持）

### 配置示例
```json
{
  "site": "linuxdo",
  "email": "your_email@example.com",
  "password": "your_password"
}
```

### 使用方法
```bash
# 基本登录
python -m src linuxdo

# 无头模式
python -m src linuxdo --headless

# 不使用 Cookie
python -m src linuxdo --no-cookie
```

### 登录流程
1. 尝试使用已保存的 Cookie
2. 如果 Cookie 无效，导航到登录页面
3. 填写邮箱和密码
4. 点击登录按钮
5. 验证登录状态
6. 保存 Cookie 供下次使用

### 注意事项
- 首次登录可能需要验证码
- Cookie 有效期约 30 天
- 建议定期刷新 Cookie

### 故障排除

**问题**: 登录失败提示"用户名或密码错误"
- 检查邮箱和密码是否正确
- 确认账号未被锁定
- 尝试手动登录确认凭据

**问题**: Cookie 登录失败
- 删除过期的 Cookie 文件：`data/cookies/linuxdo_cookies.json`
- 使用 `--no-cookie` 参数重新登录

## AnyRouter

### 概述
AnyRouter 是一个 API 管理平台，支持多种登录方式。

### 功能特性
- ✅ 多种登录方式（密码、LinuxDO OAuth、GitHub OAuth）
- ✅ Cookie 快速登录
- ✅ 自动处理 OAuth 流程
- ✅ 智能复用 LinuxDO 登录状态

### 配置示例

**密码登录**:
```json
{
  "site": "anyrouter",
  "login_type": "credentials",
  "email": "your_email@example.com",
  "password": "your_password"
}
```

**LinuxDO OAuth**:
```json
{
  "site": "anyrouter",
  "login_type": "linuxdo_oauth"
}
```
注意：需要同时配置 LinuxDO 账号

**GitHub OAuth**:
```json
{
  "site": "anyrouter",
  "login_type": "github_oauth"
}
```

### 使用方法
```bash
# 默认登录（使用配置文件中的 login_type）
python -m src anyrouter

# 指定登录方式
python -m src anyrouter --login-type credentials
python -m src anyrouter --login-type linuxdo_oauth
python -m src anyrouter --login-type github_oauth
```

### OAuth 流程
1. 点击对应的 OAuth 按钮
2. 跳转到第三方登录页面
3. 如果已登录第三方，直接授权
4. 如果未登录，先登录第三方
5. 授权后返回 AnyRouter
6. 自动导航到 API 令牌页面

### 技术细节
- OAuth 登录会复用第三方站点的 Cookie
- 支持中英文界面的弹窗关闭
- 自动处理授权确认
- Cookie 分离存储（避免混淆）

### 注意事项
- OAuth 登录需要先配置对应的第三方账号
- GitHub OAuth 可能需要 2FA 验证
- 建议使用 LinuxDO OAuth（最稳定）

## OpenI

### 概述
OpenI（启智）是一个 AI 开发平台，支持云脑任务自动化。

### 功能特性
- ✅ 账号密码登录
- ✅ Cookie 快速登录
- ✅ 多账号批量管理
- ✅ 云脑任务自动化（启动/停止）
- ✅ 自动关闭弹窗
- ✅ 积分任务执行

### 配置示例
```json
{
  "site": "openi",
  "username": "your_username",
  "password": "your_password",
  "run_cloud_task": true,
  "task_config": {
    "task_name": "gpu_task",
    "duration": 20
  }
}
```

### 使用方法
```bash
# 运行所有配置的用户
python -m src openi

# 只运行指定用户
python -m src openi --user specific_username

# 跳过云脑任务
python -m src openi --no-task
```

### 云脑任务流程
1. 登录 OpenI 平台
2. 导航到云脑任务页面
3. 检查现有任务状态
4. 如果没有运行中的任务，创建新任务
5. 等待任务运行指定时间
6. 停止任务
7. 记录任务执行日志

### 多用户管理
```json
{
  "users": [
    {"site": "openi", "username": "user1", "password": "pass1"},
    {"site": "openi", "username": "user2", "password": "pass2"},
    {"site": "openi", "username": "user3", "password": "pass3"}
  ]
}
```

批量执行：
```bash
# 执行所有用户
python -m src openi

# 并行执行（限制并发数）
python -m src openi --parallel 3
```

### 任务配置
| 参数 | 默认值 | 说明 |
|------|--------|------|
| task_name | "image" | 任务类型 |
| run_duration | 15 | 运行时长（分钟） |
| auto_stop | true | 自动停止任务 |

### 注意事项
- 每个用户的 Cookie 独立存储
- 任务执行有配额限制
- 建议错峰运行避免资源竞争
- 定期检查任务执行日志

## GitHub

### 概述
GitHub 代码托管平台，支持 2FA 双因素认证。

### 功能特性
- ✅ 账号密码登录
- ✅ 2FA 支持（手动/自动）
- ✅ Cookie 快速登录
- ✅ 多种登录入口兼容

### 配置示例

**基本配置**:
```json
{
  "site": "github",
  "username": "github_username",
  "password": "github_password"
}
```

**带 2FA TOTP**:
```json
{
  "site": "github",
  "username": "github_username",
  "password": "github_password",
  "totp_secret": "YOUR_TOTP_SECRET_KEY"
}
```

### 使用方法
```bash
# 基本登录
python -m src github

# 手动处理 2FA
python -m src github --manual-2fa

# 跳过 2FA（如果账号未启用）
python -m src github --skip-2fa
```

### 2FA 处理

**手动输入**:
1. 程序在 2FA 页面暂停
2. 用户手动输入验证码
3. 等待 60 秒超时

**自动处理**（需要 TOTP 密钥）:
```python
# 使用 pyotp 库自动生成验证码
import pyotp
totp = pyotp.TOTP(totp_secret)
code = totp.now()
```

### 登录流程
1. 检查 Cookie 有效性
2. 导航到登录页面
3. 输入用户名
4. 点击继续
5. 输入密码
6. 点击登录
7. 处理 2FA（如果需要）
8. 验证登录状态
9. 保存 Cookie

### 选择器兼容性
支持多种按钮选择器确保兼容性：
- `input[type="submit"][value="Sign in"]`
- `button[type="submit"]:has-text("Sign in")`
- `button.btn-primary:has-text("Sign in")`
- 更多备用选择器...

### 注意事项
- GitHub 有登录频率限制
- 2FA 验证码有效期 30 秒
- 建议使用 Cookie 减少登录次数
- 企业账号可能有额外的 SSO 流程

## ShareYourCC

### 概述
ShareYourCC 是一个内容分享平台，支持每日签到和抽奖。

### 功能特性
- ✅ 多种登录方式（邮箱、OAuth）
- ✅ 自动每日签到
- ✅ 自动抽奖
- ✅ 智能弹窗处理
- ✅ OAuth 状态复用

### 配置示例

**邮箱登录**:
```json
{
  "site": "shareyourcc",
  "login_type": "email",
  "email": "your_email@example.com",
  "password": "your_password",
  "auto_checkin": true,
  "auto_lottery": true
}
```

**LinuxDO OAuth**:
```json
{
  "site": "shareyourcc",
  "login_type": "linuxdo_oauth",
  "auto_checkin": true,
  "auto_lottery": true
}
```

**GitHub OAuth**:
```json
{
  "site": "shareyourcc",
  "login_type": "github_oauth"
}
```

**Google OAuth**:
```json
{
  "site": "shareyourcc",
  "login_type": "google_oauth"
}
```

### 使用方法
```bash
# 默认：登录 + 签到 + 抽奖
python -m src shareyourcc

# 只登录，不执行任务
python -m src shareyourcc --no-checkin --no-lottery

# 指定登录方式
python -m src shareyourcc --login-type email
```

### 自动化任务

**每日签到**:
- 自动检测签到按钮（12个选择器）
- 智能滚动到可见区域
- 遍历所有可能的签到元素
- 记录签到结果

**每日抽奖**:
- 导航到抽奖页面
- 点击"开始抽奖"按钮
- 等待 3 秒查看结果
- 自动返回仪表板

### 弹窗处理
自动检测并关闭 19 种弹窗：
- 系统公告
- 活动通知
- Cookie 提示
- 更新提醒
- 其他模态框

### 登录流程

**OAuth 流程**:
1. 检查第三方登录状态
2. 点击对应 OAuth 按钮
3. 处理授权页面
4. 返回 ShareYourCC
5. 执行自动化任务

**邮箱登录流程**:
1. 填写邮箱密码
2. 点击登录
3. 处理可能的验证
4. 执行自动化任务

### UI 适配
支持两种界面布局：
- 现代卡片式布局
- 传统按钮式布局

### 注意事项
- 签到和抽奖每日限一次
- OAuth 会复用第三方登录状态
- 建议使用 LinuxDO OAuth（最稳定）
- 签到奖励可能有延迟到账

## 站点特性对比

### 登录方式对比

| 站点 | 账号密码 | OAuth | 2FA | Cookie |
|------|---------|--------|-----|---------|
| LinuxDO | ✅ | ❌ | ❌ | ✅ |
| AnyRouter | ✅ | ✅ | ❌ | ✅ |
| OpenI | ✅ | ❌ | ❌ | ✅ |
| GitHub | ✅ | ❌ | ✅ | ✅ |
| ShareYourCC | ✅ | ✅ | ❌ | ✅ |

### 自动化功能对比

| 站点 | 签到 | 任务 | 抽奖 | 批量 |
|------|------|------|------|------|
| LinuxDO | ❌ | ❌ | ❌ | ✅ |
| AnyRouter | ❌ | ❌ | ❌ | ✅ |
| OpenI | ❌ | ✅ | ❌ | ✅ |
| GitHub | ❌ | ❌ | ❌ | ✅ |
| ShareYourCC | ✅ | ❌ | ✅ | ✅ |

### Cookie 管理对比

| 站点 | 独立存储 | 自动刷新 | 元数据 | 有效期 |
|------|----------|----------|---------|---------|
| LinuxDO | ✅ | ✅ | ✅ | 30天 |
| AnyRouter | ✅ | ✅ | ✅ | 30天 |
| OpenI | ✅ 按用户 | ✅ | ✅ | 30天 |
| GitHub | ✅ | ✅ | ✅ | 90天 |
| ShareYourCC | ✅ | ✅ | ✅ | 30天 |

## 常见问题

### Q1: 如何添加新站点支持？

参考[开发指南](DEVELOPMENT.md#添加新站点)中的详细步骤。

### Q2: OAuth 登录失败怎么办？

1. 确认第三方账号配置正确
2. 手动登录第三方平台确认账号正常
3. 清除相关 Cookie 重试
4. 检查网络连接

### Q3: 多账号如何管理？

在配置文件中添加多个相同站点的条目：
```json
{
  "users": [
    {"site": "openi", "username": "user1", "password": "pass1"},
    {"site": "openi", "username": "user2", "password": "pass2"}
  ]
}
```

### Q4: Cookie 过期如何处理？

1. 使用 `--no-cookie` 参数强制密码登录
2. 运行 Cookie 刷新脚本：`./scripts/refresh_cookies.sh`
3. 删除过期 Cookie 文件重新登录

### Q5: 如何调试登录问题？

1. 关闭无头模式：去掉 `--headless` 参数
2. 启用调试日志：`--debug`
3. 查看错误截图：`data/screenshots/`
4. 检查日志文件：`data/logs/<site>.log`

### Q6: 站点登录规则变化怎么办？

1. 更新选择器（在对应的 login.py 中）
2. 提交 Issue 报告问题
3. 贡献代码修复

### Q7: 如何处理验证码？

- 手动模式：程序暂停等待用户输入
- 自动模式：集成第三方 OCR 服务（需自行实现）
- 使用 Cookie 避免频繁登录触发验证码

### Q8: 批量执行的最佳实践？

1. 设置合理的并发限制
2. 添加随机延迟避免被识别
3. 错峰执行避免资源竞争
4. 定期监控执行日志

## 高级功能

### 自定义登录后操作

在站点类中覆盖 `after_login` 方法：

```python
def after_login(self, page: Page, **credentials):
    # 自定义操作
    page.goto("https://site.com/special-page")
    # 执行特定任务
```

### 条件执行

使用标签系统：
```json
{
  "users": [
    {"site": "openi", "username": "user1", "tags": ["daily"]},
    {"site": "openi", "username": "user2", "tags": ["weekly"]}
  ]
}
```

执行特定标签：
```bash
python -m src openi --tag daily
```

### 自定义超时和重试

```json
{
  "config": {
    "timeout": 120000,
    "retry_count": 5,
    "retry_delay": 5000
  }
}
```

## 维护和更新

### 定期维护

1. **每日**：检查执行日志，确认任务正常
2. **每周**：清理过期日志和截图
3. **每月**：更新依赖，检查站点变化
4. **每季度**：审查和优化配置

### 监控指标

- 登录成功率
- Cookie 命中率
- 任务完成率
- 平均执行时间
- 错误频率

### 更新通知

关注项目更新：
- GitHub Release
- 更新日志
- Issue 追踪