---
description: "Execute tasks in order and implement the feature incrementally"
---

按 `specs/001-batch-reporting/tasks.md` 的顺序逐项实施：
- 小步提交，确保可回滚；
- 每完成一项：更新文档与进度；
- 每个站点引入最小必要适配，复用现有抽象；
- 遇到 2FA/验证码与 Cloudflare：记录人工介入路径与降级策略。

完成后，输出：
- `data/reports/YYYY-MM-DD.{json,txt}` 样例；
- README 片段与 `scripts/daily_run.*` 示例；
- 后续可维护与扩展建议。
