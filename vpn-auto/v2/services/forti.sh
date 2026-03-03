#!/bin/bash
# FortiClient 进程管理脚本

DISPLAY="${DISPLAY:-:1}"
SUDO_PASSWORD="${SUDO_PASSWORD:-tsl123}"

start_forticlient() {
    echo "启动 FortiClient..."
    
    # 方法 1: GUI 点击启动（推荐）
    if [ "$1" = "gui" ]; then
        SIDEBAR_X=40
        SIDEBAR_Y=200
        
        echo "通过 GUI 点击启动..."
        DISPLAY=$DISPLAY xdotool mousemove --sync $SIDEBAR_X $SIDEBAR_Y
        sleep 0.5
        DISPLAY=$DISPLAY xdotool click 1
        sleep 2
        echo "✅ 已触发 FortiClient 启动"
        return 0
    fi
    
    # 方法 2: 命令行启动（不推荐，可能不工作）
    if command -v forticlient &> /dev/null; then
        nohup forticlient > /dev/null 2>&1 &
        echo "✅ FortiClient 已启动"
        return 0
    else
        echo "❌ 未找到 forticlient 命令"
        return 1
    fi
}

stop_forticlient() {
    echo "停止 FortiClient..."
    
    # 使用 sudo 停止（需要密码）
    if [ -n "$SUDO_PASSWORD" ]; then
        # 后台执行 sudo
        sudo pkill -9 -f forticlient 2>/dev/null &
        SUDO_PID=$!
        
        # 等待密码输入窗口
        sleep 2
        
        # 自动输入密码
        echo "自动输入密码..."
        DISPLAY=$DISPLAY xdotool type "$SUDO_PASSWORD"
        sleep 0.5
        DISPLAY=$DISPLAY xdotool key Return
        sleep 1
        
        # 等待命令完成
        wait $SUDO_PID 2>/dev/null || true
        sleep 2
        
        echo "✅ FortiClient 已停止"
        return 0
    else
        # 直接停止（可能需要手动输入密码）
        sudo pkill -9 -f forticlient
        echo "✅ FortiClient 已停止"
        return 0
    fi
}

status_forticlient() {
    if pgrep -f forticlient > /dev/null; then
        echo "✅ FortiClient 正在运行"
        pgrep -af forticlient
        return 0
    else
        echo "❌ FortiClient 未运行"
        return 1
    fi
}

case "$1" in
    start)
        start_forticlient "${2:-gui}"
        ;;
    stop)
        stop_forticlient
        ;;
    restart)
        stop_forticlient
        sleep 2
        start_forticlient "${2:-gui}"
        ;;
    status)
        status_forticlient
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status} [gui|command]"
        echo "示例: $0 start gui"
        exit 1
        ;;
esac
