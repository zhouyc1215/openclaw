# awesome-openclaw-usecases 部署包

## 📦 包含文件

1. **AWESOME-USECASES-DEPLOYMENT.md** - 详细的部署方案和用例说明
2. **USECASES-QUICK-START.md** - 快速开始指南
3. **deploy-usecases.sh** - 自动化部署脚本
4. **test-usecases.sh** - 测试脚本
5. **README-USECASES.md** - 本文件

## 🚀 快速开始（3 步）

### 第 1 步：选择用例

查看 `USECASES-QUICK-START.md` 了解 5 个可用用例：

- ⭐⭐⭐⭐⭐ 科技新闻摘要（推荐）
- ⭐⭐⭐⭐⭐ 自定义晨报（推荐）
- ⭐⭐⭐⭐ Reddit 每日摘要
- ⭐⭐⭐⭐ 个人知识库
- ⭐⭐⭐ AI 财报追踪

### 第 2 步：运行部署脚本

```bash
./deploy-usecases.sh
```

按提示选择要部署的用例（推荐选择 6 = 全部部署）。

### 第 3 步：测试

```bash
# 重启 Gateway
openclaw gateway restart

# 测试新任务
./test-usecases.sh
```

## 📋 推荐部署顺序

### 新手推荐（最小配置）

只部署 2 个核心任务：

1. **自定义晨报** - 每天早上 6:30 的综合简报
2. **科技新闻摘要** - 每天早上 8:00 的新闻聚合

```bash
./deploy-usecases.sh
# 选择 3（晨报）
# 再次运行选择 1（新闻）
```

### 进阶推荐（完整配置）

部署所有 5 个用例：

```bash
./deploy-usecases.sh
# 选择 6（全部部署）
```

## 🎯 用例对比

| 用例         | 频率 | 时间       | 复杂度 | 需要 Skill | 推荐度     |
| ------------ | ---- | ---------- | ------ | ---------- | ---------- |
| 科技新闻摘要 | 每天 | 8:00       | 低     | ❌         | ⭐⭐⭐⭐⭐ |
| 自定义晨报   | 每天 | 6:30       | 中     | ❌         | ⭐⭐⭐⭐⭐ |
| Reddit 摘要  | 每天 | 18:00      | 低     | ✅         | ⭐⭐⭐⭐   |
| 个人知识库   | 手动 | -          | 中     | ✅         | ⭐⭐⭐⭐   |
| 财报追踪     | 每周 | 周日 20:00 | 低     | ❌         | ⭐⭐⭐     |

## 🔧 部署后配置

### 安装所需 Skills

```bash
# Reddit 摘要需要
openclaw skills install reddit-readonly

# 其他 skills（如果 ClawHub 有）
openclaw skills install tech-news-digest
openclaw skills install knowledge-base
```

### 配置知识库（可选）

知识库需要通过对话配置，在飞书发送：

```
设置知识库功能：

当我发送 URL 链接时，自动抓取并保存内容。
当我提问"搜索知识库：<关键词>"时，进行语义搜索并返回结果。

知识库存储在 ~/.openclaw/knowledge-base/ 目录。
```

## 📊 与现有任务的整合

部署后，你的完整任务时间表：

```
每天：
06:30 ☀️ 自定义晨报（新）
07:00 🌤️ 西安天气预报（原有）
08:00 📰 科技新闻摘要（新）
09:00 🚀 每日 AI 项目（原有）
18:00 📱 Reddit 摘要（新）
00:00 💾 自动提交代码（原有）
00:00 📦 备份定时任务（原有）

每周：
周日 20:00 💰 AI 财报追踪（新）
```

**优势**：

- 时间错开，无冲突
- 信息互补，不重复
- 覆盖全天，从早到晚

## 🎨 自定义建议

### 调整任务时间

如果时间冲突或不合适，编辑 `~/.openclaw/cron/jobs.json`：

```json
"schedule": {
  "expr": "30 7 * * *"  // 改为 7:30
}
```

### 调整任务内容

修改 `payload.message` 字段，自定义 prompt。

### 禁用不需要的任务

```bash
openclaw cron disable <task-name>
```

## 🐛 常见问题

### Q: 任务未执行？

```bash
# 检查 Gateway 状态
ss -ltnp | grep 18789

# 查看日志
tail -f /tmp/openclaw-gateway.log

# 查看任务状态
openclaw cron list
```

### Q: 消息未送达飞书？

检查：

1. Gateway 是否运行
2. 飞书配置是否正确（`~/.openclaw/openclaw.json`）
3. 用户 ID 是否正确（`ou_b3afb7d2133e4d689be523fc48f3d2b3`）

### Q: 任务超时？

增加 `timeoutSeconds`：

```json
"payload": {
  "timeoutSeconds": 300
}
```

### Q: Skill 安装失败？

某些 skills 可能不在 ClawHub 上，可以：

1. 跳过该 skill，使用基础功能
2. 自己实现类似功能
3. 等待 skill 发布

## 📚 更多信息

- **详细说明**: `AWESOME-USECASES-DEPLOYMENT.md`
- **快速指南**: `USECASES-QUICK-START.md`
- **原项目**: https://github.com/hesamsheikh/awesome-openclaw-usecases
- **OpenClaw 文档**: https://docs.openclaw.ai

## 💡 使用技巧

1. **先测试再启用**: 使用 `test-usecases.sh` 测试任务
2. **逐步部署**: 先部署 1-2 个任务，稳定后再添加
3. **观察反馈**: 运行几天后根据实际效果调整
4. **自定义 prompt**: 根据个人需求修改任务内容
5. **定期清理**: 知识库和日志定期清理

## 🎉 开始使用

```bash
# 1. 查看快速指南
cat USECASES-QUICK-START.md

# 2. 部署用例
./deploy-usecases.sh

# 3. 重启 Gateway
openclaw gateway restart

# 4. 测试
./test-usecases.sh

# 5. 查看飞书消息
# 等待任务执行或手动触发测试
```

祝使用愉快！🦞
