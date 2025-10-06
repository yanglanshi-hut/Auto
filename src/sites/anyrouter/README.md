# AnyRouter 自动登录脚本

使用 Playwright 通过 LinuxDO OAuth 实现 AnyRouter 的自动登录，支持 Cookie 保存和快速登录功能。

## 功能特性

- ✅ 通过 LinuxDO OAuth 自动登录 AnyRouter
- ✅ 保存登录 Cookie 到本地
- ✅ 支持 Cookie 快速登录（无需重复授权）
- ✅ Cookie 过期自动重新登录
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

### 首次登录

确保您已经在浏览器中登录了 LinuxDO（可以先运行 `linuxdo_login.py` 登录 LinuxDO）。

然后运行脚本：

```bash
python anyrouter_login.py
```

首次运行会：
1. 访问 AnyRouter 登录页面
2. 点击"使用 LinuxDO 继续"
3. 在 LinuxDO 授权页面自动点击"允许"
4. 完成登录并保存 Cookie 到 `anyrouter_cookies.json`

### 快速登录

第二次及以后运行时，脚本会自动使用保存的 Cookie 进行快速登录，无需重新授权。

如果 Cookie 过期，脚本会自动重新进行 OAuth 登录并更新 Cookie。

## 配置说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `USE_COOKIE` | 是否优先使用 Cookie 登录 | `True` |
| `HEADLESS` | 是否以无头模式运行浏览器 | `False` |
| `COOKIE_FILE` | Cookie 保存文件路径 | `anyrouter_cookies.json` |

## 文件说明

- `anyrouter_login.py` - 主脚本文件
- `anyrouter_cookies.json` - Cookie 保存文件（首次登录后自动生成）
- `anyrouter_error_screenshot.png` - 错误截图（发生错误时自动生成）

## 工作流程

1. **Cookie 登录（如果可用）**
   - 加载保存的 Cookie
   - 直接访问控制台页面
   - 验证登录状态

2. **OAuth 登录（Cookie 失效或首次登录）**
   - 访问 AnyRouter 登录页面
   - 关闭系统公告弹窗
   - 点击"使用 LinuxDO 继续"
   - 等待 LinuxDO 授权页面打开
   - 自动点击"允许"按钮
   - 完成授权并跳转回 AnyRouter
   - 保存新的 Cookie

3. **登录后操作**
   - 自动跳转到 API 令牌页面
   - 显示已有令牌数量
   - 保持浏览器打开便于查看

## 注意事项

1. **LinuxDO 登录状态**：本脚本依赖 LinuxDO 的登录状态，请确保 LinuxDO 账号处于登录状态
2. **安全提示**：请妥善保管 `anyrouter_cookies.json` 文件，不要泄露给他人
3. **Git 提交**：建议将 `anyrouter_cookies.json` 添加到 `.gitignore` 避免提交敏感信息
4. **Cookie 有效期**：Cookie 会在一定时间后过期，过期后会自动重新登录

## 与 LinuxDO 脚本配合使用

推荐先运行 LinuxDO 登录脚本确保 LinuxDO 处于登录状态：

```bash
# 1. 先登录 LinuxDO
cd ../linuxdo
python linuxdo_login.py

# 2. 再登录 AnyRouter
cd ../anyrouter
python anyrouter_login.py
```

这样可以确保 OAuth 授权流程顺利完成。

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

