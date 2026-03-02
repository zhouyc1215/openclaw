#!/bin/bash
# 监控 FortiClient 窗口状态
# 如果窗口被最小化或隐藏，自动恢复

export DISPLAY=:1

echo "========================================"
echo "监控 FortiClient 窗口"
echo "========================================"
echo ""
echo "按 Ctrl+C 停止监控"
echo ""

while true; do
    # 查找 FortiClient 窗口
    WINDOW_ID=$(xdotool search --name "FortiClient" 2>/dev/null | head -1)
    
    if [ -z "$WINDOW_ID" ]; then
        echo "[$(date '+%H:%M:%S')] ⚠️  未找到 FortiClient 窗口"
        sleep 5
        continue
    fi
    
    # 检查窗口状态
    WINDOW_STATE=$(xprop -id "$WINDOW_ID" _NET_WM_STATE 2>/dev/null)
    
    # 检查是否最小化
    if echo "$WINDOW_STATE" | grep -q "HIDDEN"; then
        echo "[$(date '+%H:%M:%S')] ⚠️  窗口被最小化，正在恢复..."
        
        # 恢复窗口
        xdotool windowactivate "$WINDOW_ID"
        wmctrl -i -r "$WINDOW_ID" -b remove,hidden
        
        echo "[$(date '+%H:%M:%S')] ✅ 窗口已恢复"
    else
        echo "[$(date '+%H:%M:%S')] ✅ 窗口正常显示"
    fi
    
    # 每 2 秒检查一次
    sleep 2
done
