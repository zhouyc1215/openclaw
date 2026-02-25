#!/bin/bash
# WebSocket 连接诊断脚本

set -e

echo "=========================================="
echo "OpenClaw WebSocket 连接诊断工具"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Gateway 是否运行
echo "1. 检查 Gateway 进程..."
if ss -ltnp 2>/dev/null | grep -q ":18789"; then
    echo -e "${GREEN}✓${NC} Gateway 正在运行"
    PID=$(ss -ltnp 2>/dev/null | grep ":18789" | grep -oP 'pid=\K[0-9]+' | head -1)
    echo "  进程 ID: $PID"
    BIND=$(ss -ltnp 2>/dev/null | grep ":18789" | awk '{print $4}')
    echo "  绑定地址: $BIND"
else
    echo -e "${RED}✗${NC} Gateway 未运行"
    echo "  请运行: clawdbot gateway run --bind lan --port 18789"
    exit 1
fi
echo ""

# 检查端口监听
echo "2. 检查端口监听..."
if ss -ltn | grep -q ":18789"; then
    echo -e "${GREEN}✓${NC} 端口 18789 正在监听"
else
    echo -e "${RED}✗${NC} 端口 18789 未监听"
    exit 1
fi
echo ""

# 检查 HTTP 访问
echo "3. 检查 HTTP 访问..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:18789/ | grep -q "200"; then
    echo -e "${GREEN}✓${NC} HTTP 访问正常"
else
    echo -e "${YELLOW}⚠${NC} HTTP 访问异常"
fi
echo ""

# 检查 Control UI 文件
echo "4. 检查 Control UI 文件..."
if [ -f "dist/control-ui/index.html" ]; then
    echo -e "${GREEN}✓${NC} Control UI 已构建"
    JS_FILE=$(ls dist/control-ui/assets/index-*.js 2>/dev/null | head -1)
    if [ -n "$JS_FILE" ]; then
        echo "  JavaScript: $(basename $JS_FILE)"
        SIZE=$(du -h "$JS_FILE" | cut -f1)
        echo "  大小: $SIZE"
    fi
else
    echo -e "${RED}✗${NC} Control UI 未构建"
    echo "  请运行: pnpm ui:build"
fi
echo ""

# 检查最近的 WebSocket 错误
echo "5. 检查最近的 WebSocket 错误..."
LOG_FILE="/tmp/clawdbot/clawdbot-$(date +%Y-%m-%d).log"
if [ -f "$LOG_FILE" ]; then
    ERROR_COUNT=$(grep -c "invalid connect params" "$LOG_FILE" 2>/dev/null || echo "0")
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo -e "${YELLOW}⚠${NC} 发现 $ERROR_COUNT 个连接错误"
        echo "  最近的错误："
        grep "invalid connect params" "$LOG_FILE" | tail -1 | jq -r '.time + " " + ."2"' 2>/dev/null || \
        grep "invalid connect params" "$LOG_FILE" | tail -1
    else
        echo -e "${GREEN}✓${NC} 没有发现连接错误"
    fi
else
    echo -e "${YELLOW}⚠${NC} 日志文件不存在: $LOG_FILE"
fi
echo ""

# 检查配置
echo "6. 检查 Gateway 配置..."
CONFIG_FILE="$HOME/.openclaw/openclaw.json"
if [ -f "$CONFIG_FILE" ]; then
    echo -e "${GREEN}✓${NC} 配置文件存在"
    BIND_MODE=$(jq -r '.gateway.bind // "loopback"' "$CONFIG_FILE")
    PORT=$(jq -r '.gateway.port // 18789' "$CONFIG_FILE")
    echo "  绑定模式: $BIND_MODE"
    echo "  端口: $PORT"
    
    if [ "$BIND_MODE" = "lan" ]; then
        echo -e "${GREEN}✓${NC} 已配置局域网访问"
    else
        echo -e "${YELLOW}⚠${NC} 未配置局域网访问"
        echo "  建议运行: clawdbot config set gateway.bind lan"
    fi
else
    echo -e "${YELLOW}⚠${NC} 配置文件不存在"
fi
echo ""

# 网络信息
echo "7. 网络信息..."
IP_ADDR=$(hostname -I | awk '{print $1}')
echo "  本机 IP: $IP_ADDR"
echo "  访问地址: http://$IP_ADDR:18789/"
echo ""

# 总结
echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "如果浏览器仍然无法连接，请尝试："
echo "1. 在浏览器中按 Ctrl + F5 强制刷新"
echo "2. 清除浏览器缓存（Ctrl + Shift + Delete）"
echo "3. 使用无痕模式测试（Ctrl + Shift + N）"
echo "4. 查看浏览器控制台（F12）的错误信息"
echo ""
echo "详细文档："
echo "- WebSocket 连接修复: ./WEBSOCKET-CONNECTION-FIX.md"
echo "- WebSocket 协议指南: ./WEBSOCKET-PROTOCOL-GUIDE.md"
echo ""
