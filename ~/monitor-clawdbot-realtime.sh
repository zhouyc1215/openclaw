#!/bin/bash
# Clawdbot 实时监控脚本

echo "=== Clawdbot 实时监控 ==="
echo "按 Ctrl+C 退出"
echo ""

# 显示当前状态
echo "📊 当前状态:"
systemctl --user status clawdbot-gateway.service | head -n 8
echo ""

# 显示进程信息
echo "🔄 运行进程:"
ps aux | grep -E "clawdbot|node.*openclaw" | grep -v grep | awk '{printf "  PID: %-8s CPU: %-5s MEM: %-5s CMD: %s\n", $2, $3"%", $4"%", substr($0, index($0,$11))}'
echo ""

# 显示最近的 agent 运行
echo "🤖 最近的 Agent 运行:"
tail -n 200 /tmp/clawdbot/clawdbot-2026-02-09.log 2>/dev/null | \
  jq -r 'select(.["0"] | contains("embedded run")) | .["0"] + " | " + (._meta.date // "")' 2>/dev/null | \
  tail -n 5 | \
  sed 's/^/  /'
echo ""

# 显示可用工具
echo "🛠️  当前可用工具:"
tail -n 100 /tmp/clawdbot/clawdbot-2026-02-09.log 2>/dev/null | \
  jq -r 'select(.["0"] | contains("system-prompt")) | .["0"]' 2>/dev/null | \
  tail -n 1 | \
  sed 's/^/  /'
echo ""

# 显示飞书频道状态
echo "📱 飞书频道状态:"
tail -n 50 /tmp/clawdbot/clawdbot-2026-02-09.log 2>/dev/null | \
  jq -r 'select(.["0"] | contains("feishu")) | .["0"] + " | " + (._meta.date // "")' 2>/dev/null | \
  tail -n 3 | \
  sed 's/^/  /'
echo ""

# 实时日志监控
echo "📝 实时日志 (最近 20 行):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
tail -n 20 /tmp/clawdbot/clawdbot-2026-02-09.log 2>/dev/null | \
  jq -r '(._meta.date // "") + " | " + (.name // "clawdbot") + " | " + .["0"]' 2>/dev/null | \
  sed 's/^/  /'
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 提示: 使用 'tail -f /tmp/clawdbot/clawdbot-2026-02-09.log' 查看实时日志"
