---
description: "Produce the technical implementation plan for the feature"
---

输出技术计划并创建/更新：
- `specs/001-batch-reporting/plan.md`：
  - 模块：`src/reporting/{collector,aggregator,writer}.py`；
  - CLI：在 `src/__main__.py` 增加 `report` 子命令与参数；
  - 数据：报告 JSON 结构与 TXT 摘要格式；
  - 日志：会话ID、失败截图路径；
  - 配置：`config.users.json.config` 可选扩展项（并发/重试/超时/推送）；
  - 风险：2FA、站点改版、选择器脆弱性与回退策略；
- `specs/001-batch-reporting/data-model.md`（如需）：存放报告 schema；
- `specs/001-batch-reporting/contracts/`（如需）：站点级任务契约与约束。
