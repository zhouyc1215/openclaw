#!/bin/bash
# 虚拟桌面服务管理脚本

DISPLAY="${1:-:99}"
RESOLUTION="${2:-1920x1080x24}"

start_xvfb() {
    echo "启动 Xvfb (DISPLAY=$DISPLAY, 分辨率=$RESOLUTION)..."
    
    # 停止已存在的 Xvfb
    pkill -f "Xvfb $DISPLAY" || true
    sleep 1
    
    # 启动 Xvfb
    Xvfb "$DISPLAY" -screen 0 "$RESOLUTION" &
    XVFB_PID=$!
    
    # 等待启动
    sleep 2
    
    # 检查是否启动成功
    if ps -p $XVFB_PID > /dev/null; then
        echo "✅ Xvfb 已启动 (PID: $XVFB_PID)"
        echo $XVFB_PID > /tmp/xvfb.pid
        return 0
    else
        echo "❌ Xvfb 启动失败"
        return 1
    fi
}

stop_xvfb() {
    echo "停止 Xvfb..."
    
    if [ -f /tmp/xvfb.pid ]; then
        PID=$(cat /tmp/xvfb.pid)
        if ps -p $PID > /dev/null; then
            kill $PID
            echo "✅ Xvfb 已停止"
        fi
        rm -f /tmp/xvfb.pid
    else
        pkill -f "Xvfb $DISPLAY" || true
        echo "✅ Xvfb 已停止"
    fi
}

status_xvfb() {
    if pgrep -f "Xvfb $DISPLAY" > /dev/null; then
        echo "✅ Xvfb 正在运行"
        return 0
    else
        echo "❌ Xvfb 未运行"
        return 1
    fi
}

case "$3" in
    start)
        start_xvfb
        ;;
    stop)
        stop_xvfb
        ;;
    restart)
        stop_xvfb
        sleep 1
        start_xvfb
        ;;
    status)
        status_xvfb
        ;;
    *)
        echo "用法: $0 <DISPLAY> <RESOLUTION> {start|stop|restart|status}"
        echo "示例: $0 :99 1920x1080x24 start"
        exit 1
        ;;
esac
