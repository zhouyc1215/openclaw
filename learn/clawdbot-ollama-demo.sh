#!/bin/bash

# Clawdbot + Ollama 使用演示脚本

export OLLAMA_API_KEY="ollama-local"

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║          Clawdbot 调用本地 Ollama 模型 - 完整指南                    ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# 检查状态
echo "📊 系统状态检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Ollama 状态
if curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama 服务: 运行中"
    OLLAMA_MODELS=$(curl -s http://127.0.0.1:11434/api/tags | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['models']))" 2>/dev/null)
    echo "   可用模型: $OLLAMA_MODELS 个"
else
    echo "❌ Ollama 服务: 未运行"
    echo "   请运行: ollama serve"
    exit 1
fi

# Clawdbot 配置
DEFAULT_MODEL=$(clawdbot models status 2>/dev/null | grep 'Default' | awk '{print $3}')
echo "✅ Clawdbot 配置: 完成"
echo "   默认模型: $DEFAULT_MODEL"

# 网关状态
if pgrep -f "openclaw-gateway" > /dev/null 2>&1; then
    GATEWAY_PID=$(pgrep -f "openclaw-gateway")
    echo "✅ 网关服务: 运行中 (PID: $GATEWAY_PID)"
else
    echo "⚠️  网关服务: 未运行"
    echo "   启动命令: clawdbot gateway start"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 使用方法
echo "🎯 推荐使用方法"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "方法 1: TUI 交互式界面 (最推荐) ⭐⭐⭐"
echo "----------------------------------------"
echo "命令:"
echo "  clawdbot tui"
echo ""
echo "说明: 打开一个交互式终端界面，可以持续对话"
echo "操作: 输入问题后按 Enter，按 Ctrl+C 退出"
echo ""

echo "方法 2: Agent 命令 (单次查询)"
echo "----------------------------------------"
echo "命令:"
echo '  clawdbot agent --agent main --session-id test-001 --message "你的问题"'
echo ""
echo "说明: 通过网关发送单次查询"
echo "注意: 需要指定 session-id 来创建会话"
echo ""

echo "方法 3: 直接使用 Ollama CLI (最快速) ⭐⭐⭐"
echo "----------------------------------------"
echo "命令:"
echo '  ollama run qwen2.5:7b "你的问题"'
echo ""
echo "说明: 绕过 Clawdbot，直接调用 Ollama"
echo "优点: 最快速，无需网关"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 示例演示
echo "💡 示例演示"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "示例 1: 使用 Ollama CLI 查询 MSTP 协议"
echo "----------------------------------------"
echo '$ ollama run qwen2.5:7b "什么是 MSTP 协议？请简要介绍。"'
echo ""
echo "示例 2: 使用 Clawdbot TUI"
echo "----------------------------------------"
echo '$ clawdbot tui'
echo '> 什么是 MSTP 协议？'
echo ""

echo "示例 3: 使用 Agent 命令"
echo "----------------------------------------"
echo '$ clawdbot agent --agent main --session-id mstp-query --message "什么是 MSTP 协议？"'
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 快速测试选项
echo "🚀 快速测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "选择一个方法进行测试:"
echo ""
echo "  1) 启动 TUI 交互界面"
echo "  2) 使用 Ollama CLI 测试查询"
echo "  3) 查看完整文档"
echo "  4) 退出"
echo ""
read -p "请选择 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "正在启动 TUI..."
        echo "提示: 按 Ctrl+C 退出"
        sleep 2
        clawdbot tui
        ;;
    2)
        echo ""
        echo "测试查询: 什么是 MSTP 协议？"
        echo ""
        ollama run qwen2.5:7b "什么是 MSTP 协议？请用中文简要介绍，50字以内。"
        ;;
    3)
        echo ""
        cat ~/ollama-usage-guide.md
        ;;
    4)
        echo ""
        echo "退出。"
        ;;
    *)
        echo ""
        echo "无效选择。"
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 相关文档:"
echo "   - 使用指南: ~/ollama-usage-guide.md"
echo "   - 配置总结: ~/ollama-setup-complete.txt"
echo "   - 快速参考: ~/ollama-quick-reference.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
