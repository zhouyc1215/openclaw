#!/bin/bash
# Clawdbot 实时监控脚本
# 监控 MiniMax 工具调用转换和处理过程

echo "=== Clawdbot 实时监控 ==="
echo "监控文件: /tmp/clawdbot/clawdbot-2026-02-12.log"
echo "按 Ctrl+C 停止监控"
echo ""

# 使用 SSH 连接到远程服务器并实时监控日志
sshpass -p 'tsl123' ssh tsl@10.71.1.116 'tail -f /tmp/clawdbot/clawdbot-2026-02-12.log' | while read line; do
    # 高亮显示关键信息
    if echo "$line" | grep -qi "minimax"; then
        echo -e "\033[1;35m[MINIMAX]\033[0m $line"
    elif echo "$line" | grep -qi "tool.*start"; then
        echo -e "\033[1;32m[TOOL START]\033[0m $line"
    elif echo "$line" | grep -qi "tool.*end"; then
        echo -e "\033[1;33m[TOOL END]\033[0m $line"
    elif echo "$line" | grep -qi "error"; then
        echo -e "\033[1;31m[ERROR]\033[0m $line"
    elif echo "$line" | grep -qi "assistant_message"; then
        echo -e "\033[1;36m[MESSAGE]\033[0m $line"
    elif echo "$line" | grep -qi "embedded run"; then
        echo -e "\033[1;34m[RUN]\033[0m $line"
    else
        # 只显示重要的日志行
        if echo "$line" | grep -qE "(INFO|WARN|ERROR|DEBUG)"; then
            echo "$line"
        fi
    fi
done
