# 用 Spec Kit 优化 Auto 项目的实战案例（详细流程）

本案例将以 Auto（多站点 Web 自动化登录工具）为对象，采用 Spec‑Driven Development（SDD，规格驱动开发）流程，引入“日常批量运行 + 汇总报告”的能力，形成可审阅、可追踪、可复用的工程闭环。

## 1. 背景与目标
- 现状：
  - 已有清晰的架构与 CLI，支持 AnyRouter、Linux.do、OpenI、GitHub、ShareYourCC 等站点登录与任务。
  - 生产脚本完善（init/refresh），但“跨站点/多用户的每日批量运行 + 汇总报告”能力尚未固化为产品特性。
- 目标：
  - 引入规范化的“规格→计划→任务→实现→报告”闭环；
  - 新增“每日批量运行 + 汇总报告（JSON + 文本）”，并内建 Cookie 生命周期策略与容错；
  - 不破坏现有命令与脚本，增量集成，可随时回滚。

## 2. 前置条件
- 开发环境与依赖：已按项目 README 安装（Python、Playwright、浏览器内核等）。
- 建议在新分支上实施：`feature/spec-kit-optimization`。
- IDE/AI 工具：建议使用 Claude Code（已提供初始 /speckit.* 命令文件）。

## 3. 工作流总览（SDD）
1. 宪章（/speckit.constitution）：确立质量、测试、安全、性能、易用性原则。
2. 规格（/speckit.specify）：定义“批量运行 + 报告”的产品需求与验收标准。
3. 澄清（/speckit.clarify）：系统化补齐不明确点（并发、重试、超时、2FA、脱敏等）。
4. 计划（/speckit.plan）：技术架构与实现方案（模块、CLI 变更、数据结构、日志策略）。
5. 任务（/speckit.tasks）：将计划分解为可执行任务，带依赖与并行/串行标记。
6. 实施（/speckit.implement）：按任务落地代码与文档。
7. 检查（/speckit.checklist、/speckit.analyze）：质量清单与一致性检查。

> 本仓库已在 `.claude/commands/` 提供初始命令文件，可直接在 Claude Code 聊天框输入 `/speckit.*` 触发。

## 4. 详细流程（可直接照做）

### Step 0：确认分支
```bash
# 已由本提交创建：
# git checkout -b feature/spec-kit-optimization
```

### Step 1：设定项目宪章
在 Claude Code 聊天框输入：
```text
/speckit.constitution 请为 Auto 项目建立一份简明的开发宪章，重点覆盖：
- 质量：结构化日志、关键失败点截图、报告可复现
- 测试：关键登录/选择器路径有“检查清单+干跑验证”
- 安全：凭据与 Cookie 不入库；报告与日志脱敏
- 性能：并发≤N，单账号超时≤T，失败重试≤R
- 易用性：产生日报/周报（JSON+TXT），含“自助修复建议”
- 变更最小化：保留现有命令与脚本，增量集成
```
输出保存为 `docs/sdd/constitution.md`（若无该路径，命令会引导创建）。

### Step 2：撰写“批量运行 + 报告”规格（Spec）
```text
/speckit.specify 产出一个“每日批量运行 + 汇总报告”的规格：
- 范围：anyrouter、linuxdo、openi、github、shareyourcc；用户来自 config/users.json
- 行为：
  1) 按 Cookie 有效期判定是否需要刷新；
  2) Cookie 失效/缺失则交互式登录，成功后保存 Cookie；
  3) 登录成功后执行站点特定任务（如 ShareYourCC 签到+抽奖、OpenI 云脑任务）；
  4) 记录成功/失败、耗时、关键日志片段；
  5) 生成 JSON + 文本报告（可附简报统计）；
- 验收：
  - data/reports/YYYY-MM-DD.json 与 .txt 均存在且结构正确；
  - README/Scripts 更新了“如何运行与部署”的示例；
  - 有 2FA 的站点给出可操作指引（必要时人工输入）。
```
将输出保存为：`specs/001-batch-reporting/spec.md`。

### Step 3：澄清不明确点
```text
/speckit.clarify 针对规格逐条澄清：并发度、重试策略、全局超时、2FA 与验证码处理、
日志脱敏与保留周期、报告推送渠道（邮件/IM）、失败是否影响后续任务、
站点任务超时策略与回滚策略、Cloudflare 环境下的处理等。
```
答案写入 `specs/001-batch-reporting/spec.md` 的“Clarifications”部分。

### Step 4：技术计划（Plan）
```text
/speckit.plan 
- CLI：在 src/__main__.py 增加 `report` 子命令（保留现有命令），参数：--site、--user、--concurrency、--retry、--timeout、--dry-run。
- 模块：
  - src/reporting/collector.py：run_one(site,user) → {status, time, detail, screenshot?}
  - src/reporting/aggregator.py：调度并发、失败重试、聚合
  - src/reporting/writer.py：写入 data/reports/YYYY-MM-DD.{json,txt}
- 配置：config/users.json 的 config 可追加报告相关默认项（可选）
- 日志：复用 src/core/logger.py；增加会话ID；失败时附截图路径
- 质量门：/speckit.checklist 与 /speckit.analyze 校验
```
将输出保存为：`specs/001-batch-reporting/plan.md`、`specs/001-batch-reporting/data-model.md`（如需）、`specs/001-batch-reporting/contracts/`（如需）。

### Step 5：任务分解（Tasks）
```text
/speckit.tasks 输出可执行任务清单：
- 新建 src/reporting/* 并实现核心逻辑
- 修改 src/__main__.py 增加子命令与参数
- 新增 data/reports 目录与命名规范
- 更新 README 与 scripts（daily_run.sh/.ps1）
- 编写干跑/自检脚本（不启动浏览器，校验配置与任务可达性）
- 生成 checklist 并打勾关键项（Cookie 策略、2FA、脱敏、并发限制等）
```
输出保存为：`specs/001-batch-reporting/tasks.md`。

### Step 6：实施（Implement）
```text
/speckit.implement 严守任务与依赖顺序：小步提交、逐项完成，确保回滚容易。
```
预期改动：新增 `src/reporting/*`、调整 `src/__main__.py`、新增 `data/reports/`、脚本与 README 更新。

### Step 7：检查（Checklist & Analyze）
```text
/speckit.checklist 生成质量检查清单，覆盖 Cookie 策略、2FA 提示、安全脱敏、
失败重试与并发限制、日志与报告可复现性等。

/speckit.analyze 交叉校验规范与实现，提示缺失与不一致项，给出修正建议。
```

### Step 8：运行与验证
```bash
# 干跑检查（如提供）
python -m src report --dry-run --site all --concurrency 2 --retry 1 --timeout 600

# 实际运行
python -m src report --concurrency 2 --retry 1 --timeout 600
ls -l data/reports
```
验证点：
- JSON 与 TXT 报告内容完整；
- 失败案例包含“如何自助修复”的提示；
- 截图路径与日志定位清晰可用。

### Step 9：生产化
- 更新 `scripts/daily_run.sh` / `.ps1` 调用 `python -m src report ...`，输出重定向到固定日志；
- crontab（示例）：
  ```
  10 5 * * * /bin/bash -lc 'cd /path/to/Auto && python -m src report --concurrency 2 --retry 1 --timeout 600 >> data/logs/cron_report.log 2>&1'
  ```

## 5. 交付物与验收
- 规范、计划、任务文档齐备（`specs/001-batch-reporting/*`）。
- 新增 `report` 子命令与报告产物目录（`data/reports/`）。
- 文档与脚本更新完备（README + scripts）。
- 质量清单通过，Analyze 无重大不一致项。

## 6. 回滚方案
- 全部在 `feature/spec-kit-optimization` 分支进行；如需回滚，切回 `main`/`master` 分支。
- 代码实现按任务小步提交，可选择性撤销。

---

如需我代为落地实现步骤 4–8 的代码骨架，请告知你偏好的并发上限、超时与重试策略；我将按既定规范输出最小可用实现与单点验证脚本。
