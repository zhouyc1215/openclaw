# Clawdbot 配置优化建议

## 当前配置分析

### 现有配置
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
            "maxTokens": 327680
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
      "subagents": {
        "maxConcurrent": 1
      },
      "timeoutSeconds": 120
    }
  }
}
```

---

## 优化建议

### 1. 模型参数优化

#### 问题
- `maxTokens` 设置过高（327680），远超模型实际能力
- 缺少温度参数控制

#### 建议
```json
{
  "models": {
    "providers": {
      "ollama": {
        "models": [
          {
            "id": "qwen2.5:1.5b",
            "name": "Qwen 2.5 1.5B",
            "contextWindow": 32768,
            "maxTokens": 8192,  // 更合理的输出限制
            "params": {
              "temperature": 0.7  // 平衡创造性和准确性
            }
          }
        ]
      }
    }
  }
}
```

**理由：**
- `maxTokens: 8192` 更符合实际使用场景，避免过长响应
- `temperature: 0.7` 是一个平衡值（0.0=确定性，1.0=创造性）

---

### 2. Agent 超时优化

#### 当前设置
```json
"timeoutSeconds": 120
```

#### 建议
```json
"timeoutSeconds": 300  // 5分钟，给模型更多时间
```

**理由：**
- 测试显示响应时间约84秒
- 120秒可能在复杂任务时不够
- 300秒提供更好的容错空间

---

### 3. 添加思考模式配置

#### 建议添加
```json
{
  "agents": {
    "defaults": {
      "thinkingDefault": "low",      // 默认思考级别
      "verboseDefault": "off",       // 默认详细输出关闭
      "elevatedDefault": "off"       // 默认不使用提升权限
    }
  }
}
```

**理由：**
- `thinkingDefault: "low"` 适合日常使用，平衡性能和质量
- `verboseDefault: "off"` 减少不必要的输出
- `elevatedDefault: "off"` 提高安全性

---

### 4. 添加工作区配置

#### 建议添加
```json
{
  "agents": {
    "defaults": {
      "workspace": "~/clawd",        // 明确指定工作区
      "repoRoot": "~/clawdbot"       // 指定代码仓库根目录
    }
  }
}
```

**理由：**
- 明确工作区位置，避免混淆
- 便于管理和备份

---

### 5. 添加上下文管理

#### 建议添加
```json
{
  "agents": {
    "defaults": {
      "contextTokens": 32768,        // 匹配模型上下文窗口
      "contextPruning": {
        "mode": "adaptive",          // 自适应修剪
        "keepLastAssistants": 3,     // 保留最后3个助手消息
        "softTrimRatio": 0.3,        // 软修剪阈值
        "hardClearRatio": 0.5        // 硬清除阈值
      }
    }
  }
}
```

**理由：**
- 自动管理上下文，避免超出模型限制
- 保留重要的最近对话
- 减少 token 使用

---

### 6. 添加执行超时配置

#### 建议添加
```json
{
  "agents": {
    "defaults": {
      "exec": {
        "backgroundMs": 10000,       // 10秒后视为后台任务
        "timeoutSec": 600,           // 命令执行超时10分钟
        "cleanupMs": 1800000         // 30分钟后清理
      }
    }
  }
}
```

**理由：**
- 防止命令执行卡死
- 自动清理长时间运行的进程

---

### 7. 添加模型别名

#### 建议添加
```json
{
  "agents": {
    "defaults": {
      "models": {
        "ollama/qwen2.5:1.5b": {
          "alias": "qwen"            // 简短别名
        }
      }
    }
  }
}
```

**理由：**
- 方便在聊天中切换模型：`/model qwen`
- 提高易用性

---

### 8. 添加沙箱配置（可选，用于安全性）

#### 建议添加（如果需要隔离执行）
```json
{
  "agents": {
    "defaults": {
      "sandbox": {
        "mode": "off",               // 本地开发关闭沙箱
        "scope": "session",          // 每个会话一个容器
        "workspaceAccess": "none"    // 沙箱不访问主工作区
      }
    }
  }
}
```

**理由：**
- 本地开发通常不需要沙箱
- 如果在生产环境或多用户场景，建议启用

---

## 完整优化配置

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
            "maxTokens": 8192,
            "params": {
              "temperature": 0.7
            }
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "workspace": "~/clawd",
      "repoRoot": "~/clawdbot",
      "models": {
        "ollama/qwen2.5:1.5b": {
          "alias": "qwen"
        }
      },
      "model": {
        "primary": "ollama/qwen2.5:1.5b"
      },
      "thinkingDefault": "low",
      "verboseDefault": "off",
      "elevatedDefault": "off",
      "timeoutSeconds": 300,
      "maxConcurrent": 1,
      "subagents": {
        "maxConcurrent": 1
      },
      "contextTokens": 32768,
      "contextPruning": {
        "mode": "adaptive",
        "keepLastAssistants": 3,
        "softTrimRatio": 0.3,
        "hardClearRatio": 0.5
      },
      "exec": {
        "backgroundMs": 10000,
        "timeoutSec": 600,
        "cleanupMs": 1800000
      }
    }
  }
}
```

---

## 应用优化配置

### 方法1：手动编辑
```bash
nano /home/tsl/.clawdbot/clawdbot.json
# 粘贴上面的完整配置
```

### 方法2：使用 CLI 命令
```bash
# 设置单个配置项
clawdbot config set agents.defaults.timeoutSeconds 300
clawdbot config set agents.defaults.thinkingDefault low
clawdbot config set agents.defaults.contextTokens 32768
```

### 方法3：使用 jq 批量更新
```bash
cat /home/tsl/.clawdbot/clawdbot.json | jq '
  .models.providers.ollama.models[0].maxTokens = 8192 |
  .models.providers.ollama.models[0].params = {"temperature": 0.7} |
  .agents.defaults.timeoutSeconds = 300 |
  .agents.defaults.thinkingDefault = "low" |
  .agents.defaults.verboseDefault = "off" |
  .agents.defaults.contextTokens = 32768
' > /tmp/clawdbot-optimized.json && mv /tmp/clawdbot-optimized.json /home/tsl/.clawdbot/clawdbot.json
```

---

## 验证配置

应用配置后，使用以下命令验证：

```bash
# 检查配置是否有效
clawdbot doctor

# 查看当前配置
clawdbot config get

# 测试模型
pnpm clawdbot agent --local --session-id test --message "测试配置" --thinking low
```

---

## 性能对比

### 优化前
- 超时：120秒（可能不够）
- maxTokens：327680（过高）
- 无温度控制
- 无上下文管理

### 优化后
- 超时：300秒（更宽松）
- maxTokens：8192（合理）
- 温度：0.7（平衡）
- 自适应上下文修剪

**预期改进：**
- ✅ 更稳定的响应（不会因超时中断）
- ✅ 更合理的输出长度
- ✅ 更好的响应质量控制
- ✅ 自动管理上下文，避免超限

---

## 注意事项

1. **备份配置**：修改前先备份
   ```bash
   cp /home/tsl/.clawdbot/clawdbot.json /home/tsl/.clawdbot/clawdbot.json.backup
   ```

2. **逐步应用**：建议先应用关键优化（超时、maxTokens），测试后再添加其他配置

3. **监控性能**：应用配置后，观察响应时间和质量变化

4. **根据需求调整**：
   - 如果需要更长响应，增加 `maxTokens`
   - 如果需要更确定的答案，降低 `temperature`
   - 如果需要更快响应，降低 `timeoutSeconds`
