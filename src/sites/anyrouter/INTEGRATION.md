# LinuxDO + AnyRouter 集成使用指南

本文档说明如何配合使用 LinuxDO 和 AnyRouter 自动登录脚本。

## 项目结构

```
Auto/
├── linuxdo/                    # LinuxDO 登录脚本
│   ├── linuxdo_login.py       # 主脚本
│   ├── linuxdo_cookies.json   # Cookie 文件（自动生成）
│   └── README.md              # 使用说明
├── anyrouter/                  # AnyRouter 登录脚本
│   ├── anyrouter_login.py     # 主脚本
│   ├── anyrouter_cookies.json # Cookie 文件（自动生成）
│   ├── test_login.py          # 测试脚本
│   └── README.md              # 使用说明
└── openi/                      # OpenI 登录脚本
    └── openi_login.py         # 主脚本
```

## 快速开始

### 方案一：分别运行（推荐）

适合首次使用或需要单独登录某个平台的场景。

```bash
# 1. 先登录 LinuxDO
cd linuxdo
python linuxdo_login.py

# 2. 再登录 AnyRouter（使用 LinuxDO OAuth）
cd ../anyrouter
python anyrouter_login.py
```

### 方案二：使用测试脚本

```bash
cd anyrouter
python test_login.py
```

## 工作原理

### LinuxDO 登录

1. 访问 https://linux.do/
2. 使用账号密码登录
3. 保存 Cookie 到 `linuxdo_cookies.json`
4. 后续访问自动使用 Cookie 登录

### AnyRouter 登录

1. **依赖 LinuxDO 登录状态**
2. 访问 https://anyrouter.top/
3. 点击"使用 LinuxDO 继续"
4. LinuxDO 授权页面自动点击"允许"
5. 完成 OAuth 授权
6. 保存 Cookie 到 `anyrouter_cookies.json`
7. 后续访问自动使用 Cookie 登录

## Cookie 管理

### Cookie 有效期

- LinuxDO Cookie：通常有效期较长，建议 7 天后重新登录
- AnyRouter Cookie：依赖 LinuxDO 登录状态

### Cookie 失效处理

**LinuxDO Cookie 失效**：
```bash
# 删除旧 Cookie
rm linuxdo/linuxdo_cookies.json

# 重新登录
cd linuxdo
python linuxdo_login.py
```

**AnyRouter Cookie 失效**：
```bash
# 删除旧 Cookie
rm anyrouter/anyrouter_cookies.json

# 确保 LinuxDO 已登录，然后重新登录
cd anyrouter
python anyrouter_login.py
```

**两者都失效**：
```bash
# 清除所有 Cookie
rm linuxdo/linuxdo_cookies.json anyrouter/anyrouter_cookies.json

# 重新登录
cd linuxdo
python linuxdo_login.py

cd ../anyrouter
python anyrouter_login.py
```

## 自动化场景

### 场景 1：定期刷新 AnyRouter 登录状态

创建一个脚本来定期刷新登录状态：

```python
# refresh_login.py
import subprocess
import time

def refresh_all():
    """刷新所有平台的登录状态"""
    # 登录 LinuxDO
    print("正在登录 LinuxDO...")
    subprocess.run(['python', 'linuxdo/linuxdo_login.py'])

    time.sleep(2)

    # 登录 AnyRouter
    print("正在登录 AnyRouter...")
    subprocess.run(['python', 'anyrouter/anyrouter_login.py'])

if __name__ == "__main__":
    refresh_all()
```

### 场景 2：批量操作

如果需要在登录后执行特定操作：

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()

    # 加载 LinuxDO Cookie
    with open('linuxdo/linuxdo_cookies.json', 'r') as f:
        cookies = json.load(f)
        context.add_cookies(cookies)

    # 加载 AnyRouter Cookie
    with open('anyrouter/anyrouter_cookies.json', 'r') as f:
        cookies = json.load(f)
        context.add_cookies(cookies)

    page = context.new_page()

    # 访问 AnyRouter API 令牌页面
    page.goto('https://anyrouter.top/console/token')

    # 执行你的操作...

    browser.close()
```

## 常见问题

### Q: AnyRouter 登录失败，提示"未找到授权页面"

**A:** 确保 LinuxDO 处于登录状态。建议先运行 `linuxdo_login.py`。

### Q: Cookie 经常失效怎么办？

**A:** 这是正常现象，Cookie 都有有效期。建议：
1. 定期（如每周）重新运行登录脚本
2. 在脚本中添加 Cookie 有效期检查
3. 使用 cron 或计划任务自动刷新

### Q: 能否在无头模式下运行？

**A:** 可以，但首次登录建议使用有界面模式确保登录成功。之后可以使用无头模式：

```python
# LinuxDO
login_to_linuxdo(
    email="your_email",
    password="your_password",
    use_cookie=True,
    headless=True  # 无头模式
)

# AnyRouter
login_to_anyrouter(
    use_cookie=True,
    headless=True  # 无头模式
)
```

### Q: 如何在 Docker 中使用？

**A:** 需要安装依赖并配置：

```dockerfile
FROM python:3.10

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

RUN pip install playwright && playwright install chromium

COPY . /app
WORKDIR /app
CMD ["python", "anyrouter/anyrouter_login.py"]
```

## 安全建议

1. **不要提交 Cookie 文件**：已在 `.gitignore` 中配置
2. **定期更换密码**：建议定期更新 LinuxDO 密码
3. **使用环境变量**：不要在代码中硬编码密码
4. **限制文件权限**：

```bash
chmod 600 linuxdo/linuxdo_cookies.json
chmod 600 anyrouter/anyrouter_cookies.json
```

## 许可证

MIT License

