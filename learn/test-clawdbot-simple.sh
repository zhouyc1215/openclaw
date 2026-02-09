#!/bin/bash

# 简单测试脚本 - Clawdbot 调用 Ollama

export OLLAMA_API_KEY="ollama-local"

echo "=== Clawdbot 调用 Ollama 测试 ==="
echo ""

# 测试 1: 使用 TUI (推荐)
echo "✅ 方法 1: 使用 TUI (交互式界面)"
echo "   命令: clawdbot tui"
echo "   说明: 这是最简单的方式，打开后直接输入问题即可"
echo ""

# 测试 2: 使用 agent 命令创建会话
echo "✅ 方法 2: 使用 agent 命令"
echo "   命令: clawdbot agent --agent main --session-id test-session --message \"你的问题\""
echo "   说明: 需要指定 session-id 来标识会话"
echo ""

# 测试 3: 直接使用 Ollama
echo "✅ 方法 3: 直接使用 Ollama CLI (最快)"
echo "   命令: ollama run qwen2.5:7b \"你的问题\""
echo "   说明: 绕过 clawdbot，直接调用模型"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "现在演示方法 3 (最快速):"
echo ""
echo "问题: 什么是 MSTP 协议？"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 执行查询
ollama run qwen2.5:7b "什么是 MSTP 协议？请用中文简要介绍，不超过100字。"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 要使用 Clawdbot TUI 进行交互式对话，请运行:"
echo "   clawdbot tui"
echo ""
echo "💡 要使用 agent 命令，请运行:"
echo '   clawdbot agent --agent main --session-id my-session --message "你的问题"'
echo ""
