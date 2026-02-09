#!/bin/bash
# 安装和配置 qwen2.5:1.5b 模型

set -e

echo "=========================================="
echo "  安装 qwen2.5:1.5b 模型"
echo "=========================================="
echo ""

# 1. 安装模型
echo "📦 正在下载 qwen2.5:1.5b 模型..."
ollama pull qwen2.5:1.5b

echo ""
echo "✅ 模型下载完成！"
echo ""

# 2. 测试模型
echo "🧪 测试模型性能..."
echo ""
time ollama run qwen2.5:1.5b "什么是 MSTP 协议？请用一句话回答。"
echo ""

# 3. 更新 Clawdbot 配置
echo "⚙️  更新 Clawdbot 配置..."

cat > ~/.clawdbot/clawdbot.json << 'EOF'
{
  "models": {
    "providers": {
      "ollama": {
        "baseUrl": "http://127.0.0.1:11434/v1",
        "apiKey": "ollama-local",
        "api": "openai-completions",
        "models": {
          "qwen2.5:1.5b": {
            "contextWindow": 32768,
            "maxTokens": 327680
          },
          "qwen2.5:3b": {
            "contextWindow": 32768,
            "maxTokens": 327680
          }
        }
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
EOF

echo "✅ 配置已更新！"
echo ""

# 4. 重启 Gateway
echo "🔄 重启 Clawdbot Gateway..."
clawdbot gateway stop
sleep 2
clawdbot gateway start
sleep 3

echo ""
echo "✅ Gateway 已重启！"
echo ""

# 5. 验证配置
echo "🔍 验证配置..."
clawdbot models list

echo ""
echo "=========================================="
echo "  ✅ 安装完成！"
echo "=========================================="
echo ""
echo "📝 使用方式："
echo ""
echo "1. 直接使用 Ollama (最快):"
echo "   ollama run qwen2.5:1.5b \"你的问题\""
echo ""
echo "2. 使用 Clawdbot:"
echo "   clawdbot agent --agent main --message \"你的问题\" --thinking low"
echo ""
echo "3. 使用 TUI:"
echo "   clawdbot tui"
echo ""
echo "📊 已安装的模型："
ollama list
echo ""
echo "💡 提示："
echo "   - qwen2.5:1.5b 适合日常对话和简单查询"
echo "   - qwen2.5:3b 适合更复杂的任务（建议直接用 Ollama）"
echo "   - 如果不需要 qwen2.5:7b，可以卸载: ollama rm qwen2.5:7b"
echo ""
