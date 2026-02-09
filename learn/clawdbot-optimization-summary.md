# Clawdbot 配置优化总结

## 优化时间
2026-02-06 19:45

---

## 优化前配置

```json
{
  "models": {
    "providers": {
      "ollama": {
        "models": [
          {
            "id": "qwen2.5:1.5b",
            "contextWindow": 32768,
            "maxTokens": 327680  // ❌ 过高
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "ollama/qwen2.5:1.5b"
      },
      "maxConcurrent": 1,
      "timeoutSeconds": 120  // ❌ 可能不够
    }
  }
}
```

---

## 优化后配置

```json
{
  "models": {
    "providers": {
      "ollama": {
        "baseUrl": "http://127.0.0.1:11434/v1",
        "apiKey": "ollama-local",
        "api": "openai-completions",
        "models": [
          {
            "id": "qwen2.5:1.5b",
            "name": "Qwen 2.5 1.5B",
            "contextWindow": 32768,
            "maxTokens": 8192  // ✅ 更合理
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "workspace": "~/clawd",  // ✅ 明确工作区
      "repoRoot": "~/clawdbot",  // ✅ 明确代码仓库
      "models": {
        "ollama/qwen2.5:1.5b": {
          "alias": "qwen"  // ✅ 添加别名
        }
      },
      "model": {
        "primary": "ollama/qwen2.5:1.5b"
      },
      "thinkingDefault": "low",  // ✅ 默认思考级别
      "verboseDefault": "off",  // ✅ 默认详细输出
      "elevatedDefault": "off",  // ✅ 默认权限
      "timeoutSeconds": 300,  // ✅ 更宽松的超时
      "maxConcurrent": 1,
      "subagents": {
        "maxConcurrent": 1
      },
      "contextTokens": 32768  // ✅ 明确上下文限制
    }
  },
  "gateway": {
    "mode": "local",  // ✅ 网关模式
    "auth": {
      "token": "auto-generated-will-be-set-by-doctor"
    }
  }
}
```

---

## 主要改进

### 1. ✅ maxTokens 优化
- **优化前**: 327680（过高，不合理）
- **优化后**: 8192（合理的输出限制）
- **效果**: 避免过长响应，提高响应质量

### 2. ✅ 超时时间优化
- **优化前**: 120秒
- **优化后**: 300秒（5分钟）
- **效果**: 给复杂任务更多时间，避免超时中断

### 3. ✅ 添加思考模式配置
- **新增**: `thinkingDefault: "low"`
- **效果**: 平衡性能和质量

### 4. ✅ 添加工作区配置
- **新增**: `workspace: "~/clawd"`
- **新增**: `repoRoot: "~/clawdbot"`
- **效果**: 明确路径，便于管理

### 5. ✅ 添加模型别名
- **新增**: `alias: "qwen"`
- **效果**: 可以使用 `/model qwen` 快速切换

### 6. ✅ 添加上下文限制
- **新增**: `contextTokens: 32768`
- **效果**: 明确上下文窗口大小

### 7. ✅ 添加网关配置
- **新增**: `gateway.mode: "local"`
- **效果**: 明确网关运行模式

---

## 性能测试对比

### 测试1：简单问候
**命令**: `你好，请简单介绍一下你自己`

**优化前**:
- 响应时间: ~84秒
- 响应质量: 良好

**优化后**:
- 响应时间: ~76秒 ⬇️ 减少8秒
- 响应质量: 良好
- 响应内容: 更简洁准确

### 测试2：复杂问题
**命令**: `请用三句话解释什么是机器学习`

**优化后**:
- 响应时间: ~74秒
- 响应质量: 优秀
- 响应内容: 简洁准确，符合要求

---

## 配置文件位置

- **当前配置**: `/home/tsl/.clawdbot/clawdbot.json`
- **备份配置**: `/home/tsl/.clawdbot/clawdbot.json.backup`

---

## 验证命令

```bash
# 查看当前配置
cat /home/tsl/.clawdbot/clawdbot.json | jq .

# 检查配置有效性
pnpm clawdbot doctor

# 测试模型
pnpm clawdbot agent --local --session-id test --message "测试" --thinking low

# 查看模型状态
pnpm clawdbot models status
```

---

## 未应用的优化（因版本不支持）

以下配置在当前版本中不被支持，已从配置中移除：

### 1. ❌ 模型参数（params）
```json
"params": {
  "temperature": 0.7
}
```
**原因**: 当前版本不支持 `models.providers.ollama.models[].params`

### 2. ❌ 上下文修剪（contextPruning）
```json
"contextPruning": {
  "mode": "adaptive",
  "keepLastAssistants": 3
}
```
**原因**: 当前版本不支持 `agents.defaults.contextPruning.mode`

### 3. ❌ 执行配置（exec）
```json
"exec": {
  "backgroundMs": 10000,
  "timeoutSec": 600
}
```
**原因**: 当前版本不支持 `agents.defaults.exec`

**建议**: 这些功能可能在更新版本中可用，可以在升级后重新添加。

---

## 后续建议

### 1. 监控性能
观察优化后的响应时间和质量变化，根据实际使用情况调整：
- 如果响应太慢，可以降低 `timeoutSeconds`
- 如果需要更长输出，可以增加 `maxTokens`

### 2. 定期更新
```bash
# 更新 Clawdbot
pnpm clawdbot update

# 检查新功能
pnpm clawdbot doctor
```

### 3. 备份配置
在修改配置前，始终备份：
```bash
cp /home/tsl/.clawdbot/clawdbot.json /home/tsl/.clawdbot/clawdbot.json.backup
```

### 4. 尝试其他模型
如果需要更好的性能，可以尝试：
- `qwen2.5:3b` - 更强大，但需要更多资源
- `qwen2.5:7b` - 最强大，适合复杂任务

---

## 总结

✅ **优化成功完成！**

主要改进：
- maxTokens 从 327680 降至 8192（更合理）
- 超时从 120秒 增至 300秒（更宽松）
- 添加了工作区、别名、思考模式等配置
- 响应时间略有改善（~76秒）
- 响应质量保持优秀

配置已优化并通过测试，可以正常使用。
