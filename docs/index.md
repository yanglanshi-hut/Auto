# Auto 项目文档中心

欢迎来到 Auto 项目文档中心！这里包含了项目的所有文档资源，帮助你快速了解、使用和开发本项目。

## 📚 文档导航

### 🚀 快速开始
- **[README](../README.md)** - 项目概述和快速入门
- **[安装指南](INSTALLATION.md)** - 详细的安装和环境配置说明
- **[配置参考](CONFIGURATION.md)** - 完整的配置选项说明

### 👤 用户文档
- **[站点集成指南](SITES.md)** - 所有支持站点的详细使用说明
- **[OAuth 多账号管理](OAUTH_MULTI_ACCOUNT.md)** - OAuth 和多账号管理指南
- **[任务调度说明](SCHEDULING.md)** - 定时任务和自动化调度

### 👨‍💻 开发者文档
- **[API 参考](API_REFERENCE.md)** - 完整的 API 接口文档
- **[架构设计](ARCHITECTURE.md)** - 系统架构和设计原理
- **[开发指南](DEVELOPMENT.md)** - 如何参与开发和添加新功能

### 📋 其他文档
- **[Spec Kit 优化案例](spec-kit-optimization-auto.md)** - 项目优化案例研究
- **[项目历史](history/)** - 项目重构和演进历史
  - [项目重构总结](history/PROJECT_REFACTORING_SUMMARY.md)
  - [V2 重构总结](history/REFACTORING_V2_SUMMARY.md)

## 🎯 文档使用指南

### 如果你是新用户
1. 从 [README](../README.md) 开始了解项目
2. 按照 [安装指南](INSTALLATION.md) 设置环境
3. 参考 [配置参考](CONFIGURATION.md) 配置账号
4. 查看 [站点集成指南](SITES.md) 了解具体站点使用

### 如果你是开发者
1. 阅读 [架构设计](ARCHITECTURE.md) 了解系统设计
2. 查看 [API 参考](API_REFERENCE.md) 了解接口细节
3. 参考 [开发指南](DEVELOPMENT.md) 开始开发
4. 了解如何添加新站点支持

### 如果你要部署生产环境
1. 查看 [安装指南](INSTALLATION.md#docker-安装) 的 Docker 部分
2. 参考 [任务调度说明](SCHEDULING.md) 设置定时任务
3. 阅读 [配置参考](CONFIGURATION.md#生产环境配置) 的生产环境配置
4. 了解 [OAuth 多账号管理](OAUTH_MULTI_ACCOUNT.md) 批量管理

## 📖 文档结构说明

```
docs/
├── index.md                           # 文档索引（本文件）
├── API_REFERENCE.md                   # API 参考文档
├── ARCHITECTURE.md                    # 架构设计文档
├── DEVELOPMENT.md                     # 开发指南
├── INSTALLATION.md                    # 安装指南
├── CONFIGURATION.md                   # 配置参考
├── SITES.md                          # 站点集成指南
├── OAUTH_MULTI_ACCOUNT.md            # OAuth 多账号管理
├── SCHEDULING.md                      # 任务调度说明
├── spec-kit-optimization-auto.md     # 优化案例
└── history/                          # 历史文档
    ├── PROJECT_REFACTORING_SUMMARY.md
    └── REFACTORING_V2_SUMMARY.md
```

## 🔍 快速查找

### 按功能查找

**登录相关**
- [LinuxDO 登录](SITES.md#linuxdo)
- [AnyRouter 登录](SITES.md#anyrouter)
- [OpenI 登录](SITES.md#openi)
- [GitHub 登录](SITES.md#github)
- [ShareYourCC 登录](SITES.md#shareyourcc)

**配置相关**
- [配置文件格式](CONFIGURATION.md#配置文件结构)
- [环境变量](CONFIGURATION.md#环境变量)
- [命令行参数](CONFIGURATION.md#命令行参数)
- [多用户配置](CONFIGURATION.md#多用户配置)

**开发相关**
- [添加新站点](DEVELOPMENT.md#添加新站点)
- [代码规范](DEVELOPMENT.md#代码规范)
- [测试策略](DEVELOPMENT.md#测试策略)
- [调试技巧](DEVELOPMENT.md#调试技巧)

**部署相关**
- [Docker 部署](INSTALLATION.md#docker-安装)
- [定时任务](SCHEDULING.md)
- [Cookie 管理](OAUTH_MULTI_ACCOUNT.md)

### 常见问题

**安装问题**
- [pip install 失败](INSTALLATION.md#常见问题)
- [Playwright 安装失败](INSTALLATION.md#常见问题)
- [权限错误](INSTALLATION.md#常见问题)

**使用问题**
- [OAuth 登录失败](SITES.md#常见问题)
- [Cookie 过期处理](SITES.md#常见问题)
- [验证码处理](SITES.md#常见问题)

**开发问题**
- [如何添加新站点](DEVELOPMENT.md#添加新站点)
- [如何处理弹窗](DEVELOPMENT.md#常见问题)
- [如何调试](DEVELOPMENT.md#调试技巧)

## 📝 文档约定

### 符号说明
- ✅ 支持/完成
- ❌ 不支持/未完成
- ⚠️ 警告/注意事项
- 💡 提示/建议
- 🔧 配置项
- 📌 重要信息

### 代码示例约定
- `bash` - Shell 命令
- `json` - JSON 配置
- `python` - Python 代码
- `yaml` - YAML 配置

### 版本说明
- 文档基于项目最新版本编写
- 部分功能可能需要特定版本支持
- 查看 [更新日志](../README.md) 了解版本变化

## 🤝 贡献文档

欢迎帮助改进文档！

### 如何贡献
1. Fork 项目仓库
2. 创建文档分支：`git checkout -b docs/improve-xxx`
3. 编辑文档文件
4. 提交更改：`git commit -m "docs: 改进 xxx 文档"`
5. 推送分支：`git push origin docs/improve-xxx`
6. 创建 Pull Request

### 文档规范
- 使用 Markdown 格式
- 保持格式一致性
- 提供清晰的示例
- 及时更新过时内容
- 添加必要的交叉引用

## 📞 获取帮助

### 文档问题
如果你在文档中发现错误或有改进建议：
- 提交 [Issue](https://github.com/yourusername/Auto/issues)
- 直接提交 Pull Request

### 使用问题
如果你在使用中遇到问题：
1. 先查看相关文档
2. 搜索已有的 Issue
3. 提交新的 Issue（附上详细信息）

### 联系方式
- GitHub Issues: [项目 Issues](https://github.com/yourusername/Auto/issues)
- 邮箱: your-email@example.com

## 🔄 文档更新

文档会随项目更新而更新，请关注：
- 最新发布版本的文档
- [更新日志](../README.md)
- [GitHub Releases](https://github.com/yourusername/Auto/releases)

---

*最后更新: 2024年*

*文档版本: 1.0.0*

*适用项目版本: 1.x*