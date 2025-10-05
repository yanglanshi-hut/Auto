# Linux.do 论坛自动登录脚本
使用 Playwright 实现 Linux.do 论坛的自动登录，支持 Cookie 保存和快速登录功能。
## 功能特性
- ✅ 自动登录 Linux.do 论坛
- ✅ 保存登录 Cookie 到本地
- ✅ 支持 Cookie 快速登录（无需重复输入账号密码）
- ✅ Cookie 过期自动重新登录
- ✅ 支持无头模式运行
## 环境要求
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
### 首次登录
修改 `linuxdo_login.py` 中的配置参数：
```python
EMAIL = "your_email@example.com"  # 你的邮箱/用户名
PASSWORD = "your_password"         # 你的密码
USE_COOKIE = True                  # 是否优先使用 cookie 登录
HEADLESS = False                   # 是否无头模式运行
```
然后运行脚本：
```bash
python linuxdo_login.py
```
首次运行会使用账号密码登录，并将 Cookie 保存到 `linuxdo_cookies.json` 文件。
### 快速登录
第二次及以后运行时，脚本会自动使用保存的 Cookie 进行快速登录，无需重新输入账号密码。
如果 Cookie 过期，脚本会自动使用账号密码重新登录并更新 Cookie。
## 配置说明
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `EMAIL` | 登录邮箱/用户名 | - |
| `PASSWORD` | 登录密码 | - |
| `USE_COOKIE` | 是否优先使用 Cookie 登录 | `True` |
| `HEADLESS` | 是否以无头模式运行浏览器 | `False` |
| `COOKIE_FILE` | Cookie 保存文件路径 | `linuxdo_cookies.json` |
## 文件说明
- `linuxdo_login.py` - 主脚本文件
- `linuxdo_cookies.json` - Cookie 保存文件（首次登录后自动生成）
- `linuxdo_error_screenshot.png` - 错误截图（发生错误时自动生成）
## 注意事项
1. **安全提示**：请妥善保管 `linuxdo_cookies.json` 文件，不要泄露给他人
2. **Git 提交**：建议将 `linuxdo_cookies.json` 添加到 `.gitignore` 避免提交敏感信息
3. **Cookie 有效期**：Cookie 会在一定时间后过期，过期后会自动重新登录
## 故障排除
### Cookie 登录失败
如果 Cookie 登录一直失败，可以：
1. 删除 `linuxdo_cookies.json` 文件
2. 重新运行脚本进行账号密码登录
### 登录超时
如果遇到登录超时，可以：
1. 检查网络连接
2. 增加 `timeout` 参数的值
## 许可证
MIT License
