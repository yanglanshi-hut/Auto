---
description: "Draft the feature specification for Daily Batch Run + Consolidated Report"
---

以产品经理视角，为“每日批量运行 + 汇总报告”能力撰写规范（只谈做什么/为什么，不讨论技术细节）：
- 范围：anyrouter、linuxdo、openi、github、shareyourcc；用户来自 `config/users.json`；
- 行为：Cookie 有效性判定→必要时交互式登录→执行站点任务→记录结果→产出 JSON+TXT 报告；
- 约束：并发、重试、全局超时、2FA/验证码、Cloudflare、脱敏策略；
- 验收：`data/reports/YYYY-MM-DD.json/.txt` 存在且结构正确；文档/脚本已更新；2FA 给出可操作指引；
- Clarifications：使用 `[NEEDS CLARIFICATION: ...]` 标注，并在后续步骤补齐。

产出：创建 `specs/001-batch-reporting/spec.md` 并写入完整内容（用户故事、成功标准、边界与异常处理）。
