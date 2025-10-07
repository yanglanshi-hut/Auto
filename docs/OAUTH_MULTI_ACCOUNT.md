# OAuth 多账号配置指南

## 概述

ShareYourCC 和其他站点支持多种 OAuth 登录方式，并且支持同一 OAuth 方式的多个账号。

## ShareYourCC 支持的 OAuth 方式

1. **LinuxDo OAuth** - 使用 LinuxDo 账号登录
2. **Google OAuth** - 使用 Google 账号登录
3. **GitHub OAuth** - 使用 GitHub 账号登录

## 配置方式

### 1. 单个 OAuth 账号

```json
{
  "users": [
    {
      "site": "shareyourcc",
      "login_type": "linuxdo_oauth"
    }
  ]
}
```

### 2. 多种 OAuth 方式

```json
{
  "users": [
    {
      "site": "shareyourcc",
      "login_type": "linuxdo_oauth"
    },
    {
      "site": "shareyourcc",
      "login_type": "google_oauth"
    },
    {
      "site": "shareyourcc",
      "login_type": "github_oauth"
    }
  ]
}
```

### 3. 同一 OAuth 方式多个账号

通过配置对应 OAuth 提供商的多个账号来实现：

```json
{
  "users": [
    // LinuxDo 账号 1
    {
      "site": "linuxdo",
      "email": "user1@example.com",
      "password": "password1"
    },
    // ShareYourCC 使用 LinuxDo 账号 1
    {
      "site": "shareyourcc",
      "login_type": "linuxdo_oauth"
    },
    
    // LinuxDo 账号 2
    {
      "site": "linuxdo",
      "email": "user2@example.com",
      "password": "password2"
    },
    // ShareYourCC 使用 LinuxDo 账号 2（需要编程方式指定）
    {
      "site": "shareyourcc",
      "login_type": "linuxdo_oauth"
    }
  ]
}
```

## Cookie 元数据匹配

系统会自动保存登录方式到 Cookie 元数据：

```json
{
  "cookies": [...],
  "saved_at": "2025-10-07T18:00:00",
  "login_type": "google_oauth"
}
```

下次登录时，系统会自动匹配：
- ✅ Cookie 的 `login_type` 与配置的 `login_type` 一致 → 使用 Cookie
- ❌ Cookie 的 `login_type` 与配置不一致 → 重新登录

## 使用方法

### 命令行

```bash
# 使用默认配置（读取 config/users.json 的第一个 shareyourcc 配置）
python -m src.sites.shareyourcc.login

# 使用环境变量指定登录方式
export SHAREYOURCC_LOGIN_TYPE='google_oauth'
python -m src.sites.shareyourcc.login
```

### 编程方式

```python
from src.sites.shareyourcc.login import ShareyourccLogin

# LinuxDo OAuth
automation = ShareyourccLogin(headless=False)
automation.run(
    use_cookie=True,
    login_type='linuxdo_oauth'
)

# Google OAuth
automation.run(
    use_cookie=True,
    login_type='google_oauth'
)

# GitHub OAuth  
automation.run(
    use_cookie=True,
    login_type='github_oauth'
)
```

## 多账号管理

### 方法 1: 使用不同的 Cookie 目录

```python
from pathlib import Path
from src.sites.shareyourcc.login import ShareyourccLogin

# 账号 1
automation1 = ShareyourccLogin(
    headless=False,
    cookie_dir=Path("data/cookies/account1")
)
automation1.run(login_type='linuxdo_oauth')

# 账号 2
automation2 = ShareyourccLogin(
    headless=False,
    cookie_dir=Path("data/cookies/account2")
)
automation2.run(login_type='linuxdo_oauth')
```

### 方法 2: 使用配置索引

```python
from src.core.config import UnifiedConfigManager

cfg = UnifiedConfigManager()

# 获取第一个 shareyourcc 配置
creds1 = cfg.get_credentials('shareyourcc', index=0)

# 获取第二个 shareyourcc 配置
creds2 = cfg.get_credentials('shareyourcc', index=1)
```

## OAuth 依赖

不同的 OAuth 方式需要不同的依赖账号：

| OAuth 类型 | 依赖配置 | 说明 |
|-----------|---------|------|
| `linuxdo_oauth` | `linuxdo` 账号 | 需在 config/users.json 配置 LinuxDo 凭据 |
| `google_oauth` | 无 | OAuth 流程会自动处理 Google 登录 |
| `github_oauth` | `github` 账号（可选） | 如果未登录，需配置 GitHub 凭据 |

## 完整配置示例

```json
{
  "config": {
    "headless": false,
    "use_cookies": true,
    "cookie_expire_days": 30
  },
  "users": [
    // LinuxDo 账号配置
    {
      "site": "linuxdo",
      "email": "user@example.com",
      "password": "password123"
    },
    
    // GitHub 账号配置
    {
      "site": "github",
      "username": "github_user",
      "password": "github_pass"
    },
    
    // ShareYourCC - LinuxDo OAuth
    {
      "site": "shareyourcc",
      "login_type": "linuxdo_oauth"
    },
    
    // ShareYourCC - Google OAuth
    {
      "site": "shareyourcc",
      "login_type": "google_oauth"
    },
    
    // ShareYourCC - GitHub OAuth
    {
      "site": "shareyourcc",
      "login_type": "github_oauth"
    },
    
    // AnyRouter - 同样支持三种 OAuth
    {
      "site": "anyrouter",
      "login_type": "linuxdo_oauth"
    },
    {
      "site": "anyrouter",
      "login_type": "github_oauth"
    },
    {
      "site": "anyrouter",
      "login_type": "google_oauth"
    }
  ]
}
```

## 故障排除

### Cookie 不匹配

如果看到 "Cookie 不匹配" 的日志：
```
Cookie 不匹配或已过期（需要: {'login_type': 'google_oauth'}），需要重新登录
```

这是正常的，说明之前使用的是不同的登录方式，系统会自动重新登录。

### OAuth 授权失败

1. 确保对应的 OAuth 账号已配置（LinuxDo、GitHub）
2. Google OAuth 通常不需要额外配置，OAuth 流程会自动处理
3. 检查网络连接
4. 清除浏览器缓存后重试

## 优势

✅ **灵活切换** - 可以轻松切换不同的 OAuth 方式  
✅ **Cookie 隔离** - 不同 OAuth 方式的 Cookie 互不干扰  
✅ **多账号支持** - 支持同一站点多个账号  
✅ **自动匹配** - Cookie 会自动匹配登录方式，避免冲突  
✅ **通用设计** - 适用于所有支持 OAuth 的站点
