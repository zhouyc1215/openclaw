#!/bin/bash

# 飞书消息处理流程实时监控脚本

echo "=========================================="
echo "飞书消息处理流程实时监控"
echo "=========================================="
echo "监控日志: /tmp/clawdbot/clawdbot-*.log"
echo "时间: $(date)"
echo "=========================================="
echo ""
echo "等待飞书消息..."
echo ""

tail -f /tmp/clawdbot/clawdbot-*.log | while read line; do
    timestamp=$(echo "$line" | grep -oP '\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z' | head -1)
    
    # 飞书消息接收
    if echo "$line" | grep -q "feishu: received message"; then
        echo "📨 [$timestamp] 飞书收到消息"
        echo "$line" | grep -oP 'from \S+' | sed 's/from /  用户: /'
    fi
    
    # 分发到 Agent
    if echo "$line" | grep -q "feishu: dispatching to agent"; then
        echo "🚀 [$timestamp] 分发到 Agent"
    fi
    
    # Agent 开始
    if echo "$line" | grep -q "embedded run start"; then
        echo "⚙️  [$timestamp] Agent 开始运行"
        echo "$line" | grep -oP 'provider=\S+' | sed 's/provider=/  Provider: /'
        echo "$line" | grep -oP 'model=\S+' | sed 's/model=/  Model: /'
    fi
    
    # Prompt 开始
    if echo "$line" | grep -q "embedded run prompt start"; then
        echo "💭 [$timestamp] Prompt 处理开始"
    fi
    
    # Agent 执行中
    if echo "$line" | grep -q "embedded run agent start"; then
        echo "🔄 [$timestamp] Agent 执行中..."
    fi
    
    # Agent 结束
    if echo "$line" | grep -q "embedded run agent end"; then
        echo "✅ [$timestamp] Agent 执行完成"
    fi
    
    # Prompt 结束
    if echo "$line" | grep -q "embedded run prompt end"; then
        duration=$(echo "$line" | grep -oP 'durationMs=\d+')
        echo "⏱️  [$timestamp] Prompt 处理完成 ($duration)"
    fi
    
    # 发送回复
    if echo "$line" | grep -q "feishu deliver called"; then
        echo "📤 [$timestamp] 准备发送回复"
        text=$(echo "$line" | grep -oP 'text=.*' | cut -c6- | head -c 100)
        echo "  内容预览: $text"
    fi
    
    # 发送完成
    if echo "$line" | grep -q "feishu: dispatch complete"; then
        echo "✉️  [$timestamp] 消息发送完成"
        echo "$line" | grep -oP 'replies=\d+' | sed 's/replies=/  回复数: /'
    fi
    
    # 错误
    if echo "$line" | grep -qi "error\|HTTP 400\|Access denied"; then
        echo "❌ [$timestamp] 错误发生"
        error=$(echo "$line" | grep -oP '(error|Error|HTTP \d+|Access denied)[^"]*' | head -1)
        echo "  错误: $error"
    fi
    
    # 工具调用
    if echo "$line" | grep -q '"name":'; then
        tool=$(echo "$line" | grep -oP '"name":\s*"[^"]*"' | head -1)
        if [ ! -z "$tool" ]; then
            echo "🔧 [$timestamp] 工具调用: $tool"
        fi
    fi
    
    echo ""
done
