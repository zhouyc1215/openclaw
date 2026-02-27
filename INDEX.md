# awesome-openclaw-usecases 部署包索引

## 🎯 从这里开始

**第一次使用？** 按顺序阅读：

1. 📖 [快速参考.md](快速参考.md) - 一页纸快速参考（推荐）
2. 📚 [README-USECASES.md](README-USECASES.md) - 完整总览
3. 🚀 运行 `./deploy-usecases.sh` 开始部署

## 📁 文件导航

### 🌟 必读文档

| 文件                                           | 说明               | 适合人群          |
| ---------------------------------------------- | ------------------ | ----------------- |
| [快速参考.md](快速参考.md)                     | 一页纸快速参考     | 所有人 ⭐⭐⭐⭐⭐ |
| [README-USECASES.md](README-USECASES.md)       | 完整总览和快速开始 | 所有人 ⭐⭐⭐⭐⭐ |
| [DEPLOYMENT-SUMMARY.md](DEPLOYMENT-SUMMARY.md) | 部署总结和下一步   | 所有人 ⭐⭐⭐⭐   |

### 📖 详细文档

| 文件                                                             | 说明         | 适合人群        |
| ---------------------------------------------------------------- | ------------ | --------------- |
| [USECASES-QUICK-START.md](USECASES-QUICK-START.md)               | 快速开始指南 | 新手 ⭐⭐⭐⭐   |
| [AWESOME-USECASES-DEPLOYMENT.md](AWESOME-USECASES-DEPLOYMENT.md) | 详细部署方案 | 进阶用户 ⭐⭐⭐ |

### 🛠️ 工具脚本

| 文件                                     | 说明         | 用途                |
| ---------------------------------------- | ------------ | ------------------- |
| [deploy-usecases.sh](deploy-usecases.sh) | 自动部署脚本 | 部署用例 ⭐⭐⭐⭐⭐ |
| [test-usecases.sh](test-usecases.sh)     | 测试脚本     | 测试任务 ⭐⭐⭐⭐   |
| [manual-add-task.sh](manual-add-task.sh) | 手动添加工具 | 备用方案 ⭐⭐⭐     |

### 📋 配置文件

| 文件                                                 | 说明         | 用途            |
| ---------------------------------------------------- | ------------ | --------------- |
| [example-task-config.json](example-task-config.json) | 任务配置示例 | 参考模板 ⭐⭐⭐ |

## 🎓 使用场景

### 场景 1：我是新手，想快速开始

```bash
# 1. 看快速参考
cat 快速参考.md

# 2. 部署最小配置
./deploy-usecases.sh
# 选择 3（晨报）和 1（新闻）

# 3. 重启测试
openclaw gateway restart
./test-usecases.sh
```

**推荐阅读**：

- 快速参考.md
- README-USECASES.md

### 场景 2：我想了解所有用例

```bash
# 查看详细说明
cat AWESOME-USECASES-DEPLOYMENT.md
```

**推荐阅读**：

- AWESOME-USECASES-DEPLOYMENT.md
- USECASES-QUICK-START.md

### 场景 3：我想部署所有用例

```bash
# 一键部署
./deploy-usecases.sh
# 选择 6（全部）

# 重启测试
openclaw gateway restart
./test-usecases.sh
```

**推荐阅读**：

- README-USECASES.md
- DEPLOYMENT-SUMMARY.md

### 场景 4：我想自定义配置

```bash
# 查看示例配置
cat example-task-config.json

# 手动添加
./manual-add-task.sh
```

**推荐阅读**：

- AWESOME-USECASES-DEPLOYMENT.md
- example-task-config.json

### 场景 5：遇到问题需要排查

```bash
# 查看日志
tail -f /tmp/openclaw-gateway.log

# 查看任务状态
openclaw cron list

# 测试任务
./test-usecases.sh
```

**推荐阅读**：

- 快速参考.md（故障排查部分）
- USECASES-QUICK-START.md（常见问题部分）

## 📊 5 个推荐用例

| #   | 用例            | 时间       | 推荐度     | 文档位置                       |
| --- | --------------- | ---------- | ---------- | ------------------------------ |
| 1   | 科技新闻摘要    | 8:00       | ⭐⭐⭐⭐⭐ | AWESOME-USECASES-DEPLOYMENT.md |
| 2   | Reddit 每日摘要 | 18:00      | ⭐⭐⭐⭐   | AWESOME-USECASES-DEPLOYMENT.md |
| 3   | 自定义晨报      | 6:30       | ⭐⭐⭐⭐⭐ | AWESOME-USECASES-DEPLOYMENT.md |
| 4   | 个人知识库      | 手动       | ⭐⭐⭐⭐   | AWESOME-USECASES-DEPLOYMENT.md |
| 5   | AI 财报追踪     | 周日 20:00 | ⭐⭐⭐     | AWESOME-USECASES-DEPLOYMENT.md |

## 🔗 快速链接

### 部署相关

- [快速开始](README-USECASES.md#-快速开始3-步)
- [部署脚本使用](快速参考.md#-3-步快速部署)
- [测试方法](USECASES-QUICK-START.md#-部署后步骤)

### 配置相关

- [任务时间表](DEPLOYMENT-SUMMARY.md#-部署后的任务时间表)
- [自定义配置](USECASES-QUICK-START.md#-自定义)
- [API 密钥配置](AWESOME-USECASES-DEPLOYMENT.md#部署步骤)

### 故障排查

- [常见问题](USECASES-QUICK-START.md#-注意事项)
- [调试命令](快速参考.md#-常用命令)
- [日志查看](快速参考.md#-故障排查)

## 🎯 推荐阅读路径

### 路径 A：快速上手（10 分钟）

1. 快速参考.md（2 分钟）
2. 运行 deploy-usecases.sh（5 分钟）
3. 运行 test-usecases.sh（3 分钟）

### 路径 B：深入了解（30 分钟）

1. README-USECASES.md（10 分钟）
2. AWESOME-USECASES-DEPLOYMENT.md（15 分钟）
3. 运行部署和测试（5 分钟）

### 路径 C：完全掌握（1 小时）

1. 所有文档通读（40 分钟）
2. 部署和测试（10 分钟）
3. 自定义配置（10 分钟）

## 💡 使用建议

1. **先看快速参考** - 快速参考.md 包含最核心的信息
2. **逐步部署** - 不要一次部署所有，先试 1-2 个
3. **观察效果** - 运行几天后根据反馈调整
4. **查阅文档** - 遇到问题先查本索引找对应文档

## 📚 外部资源

- **原项目**: https://github.com/hesamsheikh/awesome-openclaw-usecases
- **OpenClaw 文档**: https://docs.openclaw.ai
- **ClawHub**: https://clawhub.ai

## 🆘 需要帮助？

1. 查看 [快速参考.md](快速参考.md) 的故障排查部分
2. 查看 [USECASES-QUICK-START.md](USECASES-QUICK-START.md) 的常见问题
3. 查看 Gateway 日志：`tail -f /tmp/openclaw-gateway.log`
4. 在飞书向 clawdbot 反馈问题

## 🎉 开始使用

```bash
# 最快的开始方式
cat 快速参考.md
./deploy-usecases.sh
```

祝使用愉快！🦞

---

**最后更新**: 2026-02-27  
**版本**: 1.0  
**作者**: Kiro AI Assistant
