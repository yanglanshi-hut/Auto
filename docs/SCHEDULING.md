# 定时任务设置指南

本指南介绍如何在 Linux 和 Windows 系统上设置每日自动运行 AnyRouter、OpenI 和 ShareYourCC。

## 目录

- [脚本说明](#脚本说明)
- [Linux 设置 (Cron)](#linux-设置-cron)
- [Windows 设置 (任务计划程序)](#windows-设置-任务计划程序)
- [Docker 设置](#docker-设置)
- [日志管理](#日志管理)
- [故障排查](#故障排查)

---

## 脚本说明

项目提供了两个定时运行脚本：

- **Linux/macOS**: `scripts/daily_run.sh`
- **Windows**: `scripts/daily_run.ps1`

两个脚本都会：
1. 依次运行 AnyRouter、OpenI、ShareYourCC（使用 `--headless` 模式）
2. 将每次运行的日志保存到 `data/logs/` 目录
3. 自动清理 30 天前的旧日志
4. 汇总运行结果

---

## Linux 设置 (Cron)

### 1. 添加执行权限

```bash
chmod +x scripts/daily_run.sh
```

### 2. 测试脚本

```bash
# 手动运行测试
./scripts/daily_run.sh
```

### 3. 编辑 Crontab

```bash
crontab -e
```

### 4. 添加定时任务

```bash
# 每天早上 9:00 运行
0 9 * * * /path/to/Auto/scripts/daily_run.sh >> /path/to/Auto/data/logs/cron.log 2>&1

# 每天凌晨 2:00 运行（推荐，网络较好）
0 2 * * * /path/to/Auto/scripts/daily_run.sh >> /path/to/Auto/data/logs/cron.log 2>&1

# 每 12 小时运行一次
0 */12 * * * /path/to/Auto/scripts/daily_run.sh >> /path/to/Auto/data/logs/cron.log 2>&1
```

**重要**：将 `/path/to/Auto` 替换为实际路径！

### 5. 查看定时任务

```bash
crontab -l
```

### 6. Cron 时间格式说明

```
┌───────────── 分钟 (0 - 59)
│ ┌───────────── 小时 (0 - 23)
│ │ ┌───────────── 日期 (1 - 31)
│ │ │ ┌───────────── 月份 (1 - 12)
│ │ │ │ ┌───────────── 星期 (0 - 6, 0=周日)
│ │ │ │ │
* * * * * command
```

**示例**：
- `0 9 * * *` - 每天 9:00
- `0 */6 * * *` - 每 6 小时
- `0 9,21 * * *` - 每天 9:00 和 21:00
- `0 9 * * 1-5` - 周一到周五 9:00

### 7. 使用虚拟环境

如果使用 Python 虚拟环境，修改 `daily_run.sh`：

```bash
# 取消注释这一行
source /path/to/Auto/venv/bin/activate
```

---

## Windows 设置 (任务计划程序)

### 方法 1: 使用 GUI（推荐）

#### 1. 打开任务计划程序

- 按 `Win + R`，输入 `taskschd.msc`，回车

#### 2. 创建基本任务

1. 点击右侧 **"创建基本任务"**
2. **名称**: `Auto Daily Run`
3. **描述**: `每日运行 AnyRouter, OpenI, ShareYourCC`
4. 点击 **"下一步"**

#### 3. 触发器设置

1. 选择 **"每天"**
2. 设置开始时间（例如：上午 9:00）
3. 点击 **"下一步"**

#### 4. 操作设置

1. 选择 **"启动程序"**
2. **程序或脚本**: `powershell.exe`
3. **添加参数**:
   ```
   -ExecutionPolicy Bypass -File "D:\yanglanshi\Code\Auto\scripts\daily_run.ps1"
   ```
4. **起始于**: `D:\yanglanshi\Code\Auto`
5. 点击 **"下一步"**

#### 5. 高级设置（可选）

- 勾选 **"使用最高权限运行"**（如果需要管理员权限）
- 勾选 **"如果过了计划开始时间，立即启动任务"**
- 配置为 **Windows 10/11**

#### 6. 完成并测试

1. 点击 **"完成"**
2. 在任务列表中找到 `Auto Daily Run`
3. 右键选择 **"运行"** 测试

### 方法 2: 使用 PowerShell 命令

```powershell
# 以管理员身份运行 PowerShell

# 创建定时任务
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"D:\yanglanshi\Code\Auto\scripts\daily_run.ps1`"" -WorkingDirectory "D:\yanglanshi\Code\Auto"

$trigger = New-ScheduledTaskTrigger -Daily -At "09:00"

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "Auto Daily Run" -Action $action -Trigger $trigger -Settings $settings -Description "每日运行 AnyRouter, OpenI, ShareYourCC"
```

### 方法 3: 使用 XML 导入

创建 `daily_task.xml`：

```xml
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>2024-01-01T00:00:00</Date>
    <Description>每日运行 AnyRouter, OpenI, ShareYourCC</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2024-01-01T09:00:00</StartBoundary>
      <ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-ExecutionPolicy Bypass -File "D:\yanglanshi\Code\Auto\scripts\daily_run.ps1"</Arguments>
      <WorkingDirectory>D:\yanglanshi\Code\Auto</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
```

导入任务：

```powershell
schtasks /create /tn "Auto Daily Run" /xml daily_task.xml
```

---

## Docker 设置

### 1. 创建 Dockerfile

```dockerfile
FROM python:3.11-slim

# 安装 Playwright 依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 浏览器
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

# 运行脚本
CMD ["bash", "scripts/daily_run.sh"]
```

### 2. 构建镜像

```bash
docker build -t auto-daily .
```

### 3. 使用 Cron 在容器中运行

在宿主机的 crontab 中：

```bash
0 9 * * * docker run --rm -v /path/to/data:/app/data -v /path/to/config:/app/config auto-daily
```

### 4. 使用 Docker Compose + Cron

`docker-compose.yml`:

```yaml
version: '3.8'

services:
  auto-daily:
    build: .
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - TZ=Asia/Shanghai
    profiles:
      - cron
```

宿主机 crontab：

```bash
0 9 * * * cd /path/to/Auto && docker-compose run --rm auto-daily
```

---

## 日志管理

### 日志位置

- **任务日志**: `data/logs/anyrouter_YYYY-MM-DD_HH-mm-ss.log`
- **Cron 日志** (Linux): `data/logs/cron.log`
- **应用日志**: `data/logs/anyrouter.log`, `data/logs/openi.log`, `data/logs/shareyourcc.log`

### 日志保留

脚本自动清理 30 天前的日志。如需修改保留时间：

**Linux** (`daily_run.sh`):
```bash
# 保留 7 天
find "$LOG_DIR" -name "*.log" -type f -mtime +7 -delete
```

**Windows** (`daily_run.ps1`):
```powershell
# 保留 7 天
Get-ChildItem -Path $LOG_DIR -Filter "*.log" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Remove-Item
```

### 查看日志

```bash
# Linux
tail -f data/logs/anyrouter_*.log

# Windows
Get-Content data/logs/anyrouter_*.log -Tail 50 -Wait
```

---

## 故障排查

### 1. 任务未执行

**Linux**:
```bash
# 检查 cron 服务
sudo systemctl status cron

# 查看 cron 日志
grep CRON /var/log/syslog
```

**Windows**:
- 打开 **任务计划程序**
- 查看 **"任务计划程序库"** → **历史记录**
- 检查任务状态和最后运行结果

### 2. 权限问题

**Linux**:
```bash
# 检查脚本权限
ls -la scripts/daily_run.sh

# 添加执行权限
chmod +x scripts/daily_run.sh
```

**Windows**:
```powershell
# 允许 PowerShell 脚本执行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. 路径问题

确保使用**绝对路径**：

```bash
# ❌ 错误
0 9 * * * ./scripts/daily_run.sh

# ✅ 正确
0 9 * * * /home/user/Auto/scripts/daily_run.sh
```

### 4. Python 环境问题

在脚本中指定完整的 Python 路径：

```bash
# Linux
/usr/bin/python3 -m src anyrouter --headless

# Windows
C:\Python311\python.exe -m src anyrouter --headless
```

### 5. 浏览器无法启动

**Linux** (headless 服务器):
```bash
# 安装必要的依赖
sudo apt-get install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgbm1 \
    libasound2
```

### 6. 手动测试

在添加定时任务前，先手动测试脚本：

```bash
# Linux
./scripts/daily_run.sh

# Windows
powershell -ExecutionPolicy Bypass -File scripts/daily_run.ps1
```

---

## 最佳实践

### 1. 选择合适的运行时间

- **凌晨 2:00-4:00**: 网络流量低，服务器负载小
- **避免整点**: 如 2:13 而不是 2:00（分散负载）

### 2. 监控执行结果

设置邮件通知（如果任务失败）：

**Linux** (使用 `mail` 命令):
```bash
0 2 * * * /path/to/daily_run.sh || echo "Auto Daily Run Failed" | mail -s "Automation Failed" your@email.com
```

**Windows** (PowerShell 发送邮件):
```powershell
# 在 daily_run.ps1 末尾添加
if ($LASTEXITCODE -ne 0) {
    Send-MailMessage -To "your@email.com" -From "auto@yourdomain.com" -Subject "Auto Daily Run Failed" -Body "Check logs for details" -SmtpServer "smtp.gmail.com" -Port 587 -UseSsl -Credential (Get-Credential)
}
```

### 3. 使用日志轮转

**Linux logrotate** (`/etc/logrotate.d/auto-daily`):
```
/path/to/Auto/data/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 user user
}
```

### 4. 资源限制

**Linux**:
```bash
# 限制 CPU 使用率（50%）
cpulimit -l 50 -e python &
./scripts/daily_run.sh
```

### 5. 备份 Cookie

定期备份 Cookie 文件：

```bash
# 每周备份
0 0 * * 0 tar -czf /backup/cookies_$(date +\%Y\%m\%d).tar.gz /path/to/Auto/data/cookies/
```

---

## 快速参考

### Linux Cron 示例

```bash
# 每天 2:13 运行
13 2 * * * /home/user/Auto/scripts/daily_run.sh >> /home/user/Auto/data/logs/cron.log 2>&1

# 每 12 小时运行
0 */12 * * * /home/user/Auto/scripts/daily_run.sh >> /home/user/Auto/data/logs/cron.log 2>&1

# 工作日 9:00 运行
0 9 * * 1-5 /home/user/Auto/scripts/daily_run.sh >> /home/user/Auto/data/logs/cron.log 2>&1
```

### Windows 任务计划程序快捷命令

```powershell
# 查看所有任务
schtasks /query

# 运行任务
schtasks /run /tn "Auto Daily Run"

# 停止任务
schtasks /end /tn "Auto Daily Run"

# 删除任务
schtasks /delete /tn "Auto Daily Run" /f

# 导出任务
schtasks /query /tn "Auto Daily Run" /xml > task_backup.xml

# 导入任务
schtasks /create /tn "Auto Daily Run" /xml task_backup.xml
```

---

## 技术支持

如果遇到问题，请检查：

1. 日志文件: `data/logs/`
2. Cron 日志 (Linux): `/var/log/syslog`
3. 任务计划程序历史记录 (Windows)
4. Python 和 Playwright 版本兼容性

如需帮助，请查看项目文档或提交 Issue。
