# Auto 项目文档

## 项目历史

本项目经历了两次重要的重构，从最初的混乱结构演进为当前的清晰架构。

### 重构历史文档

- [V1 重构总结](history/PROJECT_REFACTORING_SUMMARY.md) - 2025-10-03
  - 消除 openi/openi/ 双层嵌套
  - 实现代码、配置、数据完全分离
  - 提供统一 CLI 入口

- [V2 重构总结](history/REFACTORING_V2_SUMMARY.md) - 2025-10-05
  - 修复截图路径 BUG
  - 统一路径管理（ProjectPaths）
  - OpeniLogin 职责分离（443行 → 141行）
  - 统一日志配置

## 当前架构

项目采用 **V2 架构**，核心特性：

- **清晰的目录结构**: src/（代码） + config/（配置） + data/（数据）
- **统一的路径管理**: ProjectPaths dataclass
- **单一职责原则**: 每个模块 <160 行，缩进 ≤3 层
- **100% 向后兼容**: API 和 CLI 完全兼容

详见项目根目录的 [README.md](../README.md)
