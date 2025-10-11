# 配置参考

## 目录
- [配置概述](#配置概述)
- [配置文件结构](#配置文件结构)
- [全局配置选项](#全局配置选项)
- [站点配置](#站点配置)
- [环境变量](#环境变量)
- [命令行参数](#命令行参数)
- [配置优先级](#配置优先级)
- [配置示例](#配置示例)
- [安全建议](#安全建议)

## 配置概述

Auto 支持多种配置方式，按优先级从高到低：
1. 命令行参数
2. 配置文件 (`config/users.json`)
3. 环境变量
4. 默认值

## 配置文件结构

主配置文件: `config/users.json`

```json
{
  "config": {
    // 全局配置选项
  },
  "users": [
    // 用户账号列表
  ]
}
```

### 完整配置示例

```json
{
  "config": {
    "task_name": "image",
    "run_duration": 15,
    "headless": false,
    "use_cookies": true,
    "cookie_expire_days": 30,
    "timeout": 60000,
    "retry_count": 3,
    "proxy": null,
    "user_agent": null,
    "viewport": {
      "width": 1280,
      "height": 720
    },
    "log_level": "INFO",
    "screenshot_on_error": true,
    "parallel_limit": 3
  },
  "users": [
    {
      "site": "linuxdo",
      "email": "user@example.com",
      "password": "password123",
      "enabled": true,
      "tags": ["daily", "important"]
    }
  ]
}
```

## 全局配置选项

### 基础配置

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `headless` | boolean | false | 是否运行无头模式（无图形界面） |
| `use_cookies` | boolean | true | 是否使用 Cookie 快速登录 |
| `cookie_expire_days` | integer | 30 | Cookie 有效期（天） |
| `timeout` | integer | 60000 | 默认超时时间（毫秒） |
| `retry_count` | integer | 3 | 失败重试次数 |
| `log_level` | string | "INFO" | 日志级别：DEBUG, INFO, WARNING, ERROR |
| `screenshot_on_error` | boolean | true | 错误时是否保存截图 |

### OpenI 特定配置

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `task_name` | string | "image" | OpenI 云脑任务类型 |
| `run_duration` | integer | 15 | OpenI 任务运行时长（分钟） |

### 浏览器配置

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `proxy` | string/object | null | 代理设置 |
| `user_agent` | string | null | 自定义 User-Agent |
| `viewport` | object | {width: 1280, height: 720} | 浏览器视口大小 |
| `locale` | string | "zh-CN" | 浏览器语言设置 |
| `timezone` | string | "Asia/Shanghai" | 时区设置 |

### 性能配置

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `parallel_limit` | integer | 3 | 并行执行的最大用户数 |
| `delay_between_actions` | integer | 1000 | 操作之间的延迟（毫秒） |
| `page_load_timeout` | integer | 30000 | 页面加载超时（毫秒） |

## 站点配置

### 通用字段

所有站点都支持的字段：

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `site` | string | ✅ | 站点标识符 |
| `enabled` | boolean | ❌ | 是否启用该账号（默认 true） |
| `tags` | array | ❌ | 标签，用于分组执行 |
| `comment` | string | ❌ | 备注信息 |

### LinuxDO

```json
{
  "site": "linuxdo",
  "email": "user@example.com",
  "password": "password123",
  "enabled": true,
  "auto_reply": false,
  "reply_keywords": ["关键词1", "关键词2"]
}
```

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `email` | string | ✅ | 登录邮箱 |
| `password` | string | ✅ | 登录密码 |
| `auto_reply` | boolean | ❌ | 是否自动回复 |
| `reply_keywords` | array | ❌ | 回复关键词 |

### AnyRouter

```json
{
  "site": "anyrouter",
  "login_type": "credentials",
  "email": "user@example.com",
  "password": "password123"
}
```

支持多种登录方式：

**凭据登录**:
```json
{
  "site": "anyrouter",
  "login_type": "credentials",
  "email": "user@example.com",
  "password": "password123"
}
```

**OAuth 登录**:
```json
{
  "site": "anyrouter",
  "login_type": "linuxdo_oauth"
}
```

```json
{
  "site": "anyrouter",
  "login_type": "github_oauth"
}
```

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `login_type` | string | ✅ | 登录方式：credentials, linuxdo_oauth, github_oauth |
| `email` | string | 条件 | 凭据登录时必需 |
| `password` | string | 条件 | 凭据登录时必需 |

### OpenI

```json
{
  "site": "openi",
  "username": "username",
  "password": "password123",
  "run_cloud_task": true,
  "task_config": {
    "task_name": "custom_task",
    "duration": 20
  }
}
```

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `username` | string | ✅ | 用户名 |
| `password` | string | ✅ | 密码 |
| `run_cloud_task` | boolean | ❌ | 是否运行云脑任务 |
| `task_config` | object | ❌ | 任务配置（覆盖全局配置） |

### GitHub

```json
{
  "site": "github",
  "username": "github_user",
  "password": "password123",
  "totp_secret": "JBSWY3DPEHPK3PXP",
  "skip_2fa": false
}
```

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `username` | string | ✅ | GitHub 用户名 |
| `password` | string | ✅ | 密码 |
| `totp_secret` | string | ❌ | 2FA TOTP 密钥（自动处理2FA） |
| `skip_2fa` | boolean | ❌ | 跳过 2FA（如果已配置） |

### ShareYourCC

```json
{
  "site": "shareyourcc",
  "login_type": "linuxdo_oauth",
  "auto_checkin": true,
  "auto_lottery": true
}
```

支持多种登录方式：

```json
{
  "site": "shareyourcc",
  "login_type": "email",
  "email": "user@example.com",
  "password": "password123"
}
```

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `login_type` | string | ✅ | 登录方式：email, linuxdo_oauth, github_oauth, google_oauth |
| `email` | string | 条件 | 邮箱登录时必需 |
| `password` | string | 条件 | 邮箱登录时必需 |
| `auto_checkin` | boolean | ❌ | 自动签到（默认 true） |
| `auto_lottery` | boolean | ❌ | 自动抽奖（默认 true） |

## 环境变量

### 通用环境变量

```bash
# 调试模式
export DEBUG=true

# 日志级别
export LOG_LEVEL=DEBUG

# 代理设置
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080

# 配置文件路径
export AUTO_CONFIG_PATH=/custom/path/users.json

# 数据目录
export AUTO_DATA_DIR=/custom/data/directory
```

### 站点特定环境变量（已废弃，仅向后兼容）

```bash
# LinuxDO
export LINUXDO_EMAIL="user@example.com"
export LINUXDO_PASSWORD="password123"

# AnyRouter
export ANYROUTER_EMAIL="user@example.com"
export ANYROUTER_PASSWORD="password123"

# OpenI（不支持环境变量）
```

## 命令行参数

### 全局参数

```bash
python -m src [COMMAND] [OPTIONS]

选项：
  --help              显示帮助信息
  --version           显示版本号
  --config PATH       指定配置文件路径
  --headless          运行无头模式
  --no-cookie         不使用 Cookie
  --debug             启用调试模式
```

### 站点命令

```bash
# LinuxDO
python -m src linuxdo [OPTIONS]

# AnyRouter
python -m src anyrouter [OPTIONS]
  --login-type TYPE   指定登录方式

# OpenI
python -m src openi [OPTIONS]
  --user USERNAME     只运行指定用户
  --all               运行所有用户

# GitHub
python -m src github [OPTIONS]

# ShareYourCC
python -m src shareyourcc [OPTIONS]
  --no-checkin        跳过签到
  --no-lottery        跳过抽奖
```

### 参数示例

```bash
# 使用自定义配置文件
python -m src --config /path/to/config.json linuxdo

# 无头模式不使用 Cookie
python -m src linuxdo --headless --no-cookie

# 只运行特定用户
python -m src openi --user specific_username

# 调试模式
python -m src --debug github

# 指定登录方式
python -m src anyrouter --login-type github_oauth
```

## 配置优先级

配置按以下优先级加载（高优先级覆盖低优先级）：

1. **命令行参数**
   ```bash
   python -m src linuxdo --headless  # 最高优先级
   ```

2. **配置文件**
   ```json
   {
     "config": {
       "headless": false  // 中等优先级
     }
   }
   ```

3. **环境变量**
   ```bash
   export HEADLESS=false  # 较低优先级
   ```

4. **代码默认值**
   ```python
   headless = False  # 最低优先级
   ```

## 配置示例

### 最小配置

```json
{
  "users": [
    {
      "site": "linuxdo",
      "email": "user@example.com",
      "password": "password"
    }
  ]
}
```

### 多用户配置

```json
{
  "config": {
    "headless": true,
    "use_cookies": true
  },
  "users": [
    {
      "site": "openi",
      "username": "user1",
      "password": "pass1"
    },
    {
      "site": "openi",
      "username": "user2",
      "password": "pass2"
    },
    {
      "site": "linuxdo",
      "email": "user@example.com",
      "password": "pass"
    }
  ]
}
```

### 生产环境配置

```json
{
  "config": {
    "headless": true,
    "use_cookies": true,
    "cookie_expire_days": 20,
    "timeout": 120000,
    "retry_count": 5,
    "log_level": "INFO",
    "screenshot_on_error": true,
    "parallel_limit": 5,
    "proxy": {
      "server": "http://proxy.company.com:8080",
      "username": "proxy_user",
      "password": "proxy_pass"
    }
  },
  "users": [
    {
      "site": "openi",
      "username": "prod_user",
      "password": "secure_password",
      "enabled": true,
      "tags": ["production", "daily"],
      "task_config": {
        "task_name": "gpu_task",
        "duration": 30
      }
    }
  ]
}
```

### 开发环境配置

```json
{
  "config": {
    "headless": false,
    "use_cookies": false,
    "log_level": "DEBUG",
    "screenshot_on_error": true,
    "delay_between_actions": 2000,
    "viewport": {
      "width": 1920,
      "height": 1080
    }
  },
  "users": [
    {
      "site": "linuxdo",
      "email": "test@example.com",
      "password": "test_password",
      "enabled": true,
      "comment": "测试账号"
    }
  ]
}
```

### 标签分组执行

```json
{
  "users": [
    {
      "site": "openi",
      "username": "user1",
      "password": "pass1",
      "tags": ["group_a", "daily"]
    },
    {
      "site": "openi",
      "username": "user2",
      "password": "pass2",
      "tags": ["group_b", "daily"]
    },
    {
      "site": "openi",
      "username": "user3",
      "password": "pass3",
      "tags": ["group_a", "weekly"]
    }
  ]
}
```

使用标签执行：
```bash
# 只执行 group_a 的用户
python -m src openi --tag group_a

# 执行所有 daily 标签的用户
python -m src openi --tag daily
```

## 安全建议

### 1. 文件权限

```bash
# 限制配置文件权限（仅所有者可读写）
chmod 600 config/users.json

# Linux/macOS
ls -la config/users.json
# 应显示: -rw------- 1 user user
```

### 2. 密码管理

**不要**:
- 在代码中硬编码密码
- 将包含密码的配置文件提交到版本控制
- 使用明文存储敏感信息

**推荐**:
- 使用环境变量传递敏感信息
- 使用密钥管理服务
- 加密敏感配置文件

### 3. 使用密钥管理

```python
# 使用 python-dotenv 管理环境变量
from dotenv import load_dotenv
load_dotenv()

# 使用加密存储
from cryptography.fernet import Fernet

# 生成密钥
key = Fernet.generate_key()

# 加密密码
cipher = Fernet(key)
encrypted_password = cipher.encrypt(password.encode())

# 解密密码
decrypted_password = cipher.decrypt(encrypted_password).decode()
```

### 4. Git 忽略

确保 `.gitignore` 包含：
```gitignore
# 配置文件
config/users.json
config/*.json
!config/*.example

# 数据文件
data/
*.cookie
*.log

# 环境文件
.env
.env.*
```

### 5. 环境隔离

为不同环境使用不同配置：

```bash
# 开发环境
cp config/users.dev.json config/users.json

# 测试环境
cp config/users.test.json config/users.json

# 生产环境
cp config/users.prod.json config/users.json
```

### 6. 定期轮换

- 定期更新密码
- 定期刷新 Cookie
- 定期审查配置文件

### 7. 审计日志

启用详细日志记录：
```json
{
  "config": {
    "log_level": "DEBUG",
    "audit_log": true,
    "log_sensitive": false
  }
}
```

## 配置验证

### 验证工具

```bash
# 验证配置文件格式
python scripts/validate_config.py

# 测试配置是否有效
python -m src --validate-config
```

### 常见配置错误

1. **JSON 格式错误**
   - 缺少逗号
   - 多余的逗号
   - 引号不匹配

2. **必需字段缺失**
   - 缺少 site 字段
   - 缺少认证信息

3. **类型错误**
   - 布尔值使用字符串
   - 数字使用字符串

4. **路径错误**
   - 配置文件路径不存在
   - 数据目录无权限

## 配置迁移

从旧版本迁移配置：

```bash
# 自动迁移
python scripts/migrate_config.py

# 手动迁移
python scripts/migrate_config.py --input old_config.json --output new_config.json
```

迁移脚本会：
1. 备份原配置
2. 转换到新格式
3. 验证新配置
4. 保存迁移日志