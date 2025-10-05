# OpenI 平台自动登录脚本

这是一个使用 Playwright 自动登录启智AI开源社区（OpenI）平台的 Python 脚本。

## 安装步骤

### 1. 安装依赖包

```bash
pip install -r requirements.txt
```

### 2. 安装浏览器驱动

```bash
playwright install chromium
```

## 使用方法

### 方式一：直接运行（使用脚本中的默认账号）

```bash
python openi_login.py
```

### 方式二：修改脚本中的账号信息

编辑 `openi_login.py` 文件，修改以下部分：

```python
if __name__ == "__main__":
    # 配置登录信息
    USERNAME = "your_username"  # 修改为你的用户名
    PASSWORD = "your_password"  # 修改为你的密码

    # 执行登录
    login_to_openi(USERNAME, PASSWORD)
```

### 方式三：从命令行传入参数

可以修改脚本添加命令行参数支持：

```python
import sys

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        USERNAME = sys.argv[1]
        PASSWORD = sys.argv[2]
    else:
        USERNAME = "your_username"
        PASSWORD = "your_password"

    login_to_openi(USERNAME, PASSWORD)
```

然后运行：
```bash
python openi_login.py your_username your_password
```

## 脚本功能

该脚本会自动执行以下操作：

1. ✓ 打开浏览器访问 OpenI 平台首页
2. ✓ 点击"登录"按钮
3. ✓ 填写用户名/邮箱/手机号
4. ✓ 填写密码
5. ✓ 提交登录表单
6. ✓ 等待跳转到用户仪表盘
7. ✓ 自动关闭可能出现的弹窗提示
8. ✓ 验证登录状态
9. ✓ 显示用户信息（贡献数、项目列表等）

## 配置选项

### 无头模式运行

如果不想看到浏览器界面，可以修改 `headless` 参数：

```python
browser = p.chromium.launch(headless=True)  # 改为 True
```

### 调整超时时间

如果网络较慢，可以调整等待时间：

```python
page.wait_for_url('**/dashboard', timeout=120000)  # 增加到 120 秒
```

### 使用其他浏览器

可以使用 Firefox 或 WebKit：

```python
browser = p.firefox.launch(headless=False)  # Firefox
# 或
browser = p.webkit.launch(headless=False)   # WebKit
```

## 注意事项

1. **安全性**: 不要将包含真实密码的脚本提交到公开代码仓库
2. **网络延迟**: 如果网络较慢，可能需要增加等待时间
3. **验证码**: 如果平台启用验证码，需要手动处理或使用验证码识别服务
4. **错误处理**: 脚本会在出错时自动截图保存为 `error_screenshot.png`

## 故障排除

### 问题：浏览器未安装

**解决方案**：
```bash
playwright install chromium
```

### 问题：超时错误

**解决方案**：增加超时时间或检查网络连接

### 问题：元素未找到

**解决方案**：网站可能更新了，需要更新选择器

## 扩展功能建议

可以在此基础上添加：

- 自动创建项目
- 自动上传数据集
- 自动创建云脑任务
- 定期检查任务状态
- 批量操作管理

## 许可证

MIT License
