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

