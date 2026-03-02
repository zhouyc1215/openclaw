#!/bin/bash
# 逐步调试 FortiClient 启动和按钮点击

set -e

echo "=========================================="
echo "逐步调试 FortiClient"
echo "=========================================="
echo ""

# 步骤 1: 检查当前状态
echo "步骤 1: 检查当前状态"
echo "----------------------------------------"
echo "检查 FortiClient 进程..."
ps aux | grep forticlient | grep -v grep || echo "  没有运行的 FortiClient 进程"
echo ""

echo "检查 FortiClient 窗口..."
DISPLAY=:1 xdotool search --name "FortiClient" 2>/dev/null && echo "  ✅ 找到 FortiClient 窗口" || echo "  ❌ 没有 FortiClient 窗口"
echo ""

# 步骤 2: 停止所有 FortiClient 进程
echo "步骤 2: 停止所有 FortiClient 进程"
echo "----------------------------------------"
echo "tsl123" | sudo -S pkill -9 -f forticlient 2>/dev/null && echo "  ✅ 已停止 FortiClient 进程" || echo "  ⚠️  没有需要停止的进程"
sleep 3
echo ""

# 步骤 3: 启动 FortiClient GUI
echo "步骤 3: 启动 FortiClient GUI"
echo "----------------------------------------"
echo "启动命令: DISPLAY=:1 /usr/bin/forticlient gui"
DISPLAY=:1 nohup /usr/bin/forticlient gui > /tmp/forticlient-gui-debug.log 2>&1 &
FORTICLIENT_PID=$!
echo "  进程 PID: $FORTICLIENT_PID"
echo ""

# 步骤 4: 等待并监控启动过程
echo "步骤 4: 等待并监控启动过程（最多30秒）"
echo "----------------------------------------"
for i in {1..30}; do
    echo "  等待 ${i} 秒..."
    
    # 检查进程是否还在运行
    if ! ps -p $FORTICLIENT_PID > /dev/null 2>&1; then
        echo "  ❌ FortiClient 进程已退出"
        echo ""
        echo "  查看日志:"
        tail -20 /tmp/forticlient-gui-debug.log
        exit 1
    fi
    
    # 检查窗口是否出现
    if DISPLAY=:1 xdotool search --name "FortiClient" > /dev/null 2>&1; then
        echo "  ✅ FortiClient 窗口已出现（等待 ${i} 秒）"
        WINDOW_ID=$(DISPLAY=:1 xdotool search --name "FortiClient" | head -1)
        echo "  窗口 ID: $WINDOW_ID"
        break
    fi
    
    # 显示最新的日志
    if [ -f /tmp/forticlient-gui-debug.log ]; then
        LAST_LINE=$(tail -1 /tmp/forticlient-gui-debug.log)
        if [ -n "$LAST_LINE" ]; then
            echo "  日志: $LAST_LINE"
        fi
    fi
    
    if [ $i -eq 30 ]; then
        echo "  ❌ 窗口出现超时"
        echo ""
        echo "  完整日志:"
        cat /tmp/forticlient-gui-debug.log
        exit 1
    fi
    
    sleep 1
done
echo ""

# 步骤 5: 检查窗口详细信息
echo "步骤 5: 检查窗口详细信息"
echo "----------------------------------------"
WINDOW_ID=$(DISPLAY=:1 xdotool search --name "FortiClient" | head -1)
echo "窗口 ID: $WINDOW_ID"
echo "窗口名称: $(DISPLAY=:1 xdotool getwindowname $WINDOW_ID 2>/dev/null)"
echo "窗口位置和大小:"
DISPLAY=:1 xdotool getwindowgeometry $WINDOW_ID 2>/dev/null || echo "  无法获取窗口几何信息"
echo ""

# 步骤 6: 等待 GUI 完全加载
echo "步骤 6: 等待 GUI 完全加载"
echo "----------------------------------------"
echo "等待 10 秒让 GUI 完全加载..."
for i in {1..10}; do
    echo "  ${i}/10 秒..."
    sleep 1
done
echo "  ✅ 等待完成"
echo ""

# 步骤 7: 截图并检查
echo "步骤 7: 截图并检查"
echo "----------------------------------------"
DISPLAY=:1 scrot debug_screenshot.png 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✅ 截图已保存: debug_screenshot.png"
    
    # 检查截图文件大小
    FILE_SIZE=$(stat -f%z debug_screenshot.png 2>/dev/null || stat -c%s debug_screenshot.png 2>/dev/null)
    echo "  截图文件大小: $FILE_SIZE 字节"
    
    if [ $FILE_SIZE -lt 10000 ]; then
        echo "  ⚠️  截图文件太小，可能有问题"
    fi
else
    echo "  ❌ 截图失败"
fi
echo ""

# 步骤 8: 检查 FortiClient 进程详情
echo "步骤 8: 检查 FortiClient 进程详情"
echo "----------------------------------------"
echo "所有 FortiClient 相关进程:"
ps aux | grep forticlient | grep -v grep
echo ""

# 步骤 9: 检查 X11 显示
echo "步骤 9: 检查 X11 显示"
echo "----------------------------------------"
echo "DISPLAY 环境变量: ${DISPLAY:-未设置}"
echo "检查 DISPLAY :1 是否可用..."
DISPLAY=:1 xdpyinfo > /dev/null 2>&1 && echo "  ✅ DISPLAY :1 可用" || echo "  ❌ DISPLAY :1 不可用"
echo ""

# 步骤 10: 尝试激活窗口
echo "步骤 10: 尝试激活窗口"
echo "----------------------------------------"
WINDOW_ID=$(DISPLAY=:1 xdotool search --name "FortiClient" | head -1)
if [ -n "$WINDOW_ID" ]; then
    echo "激活窗口 $WINDOW_ID..."
    DISPLAY=:1 xdotool windowactivate --sync $WINDOW_ID 2>&1
    sleep 1
    echo "  ✅ 窗口激活命令已执行"
else
    echo "  ❌ 没有找到窗口"
fi
echo ""

# 步骤 11: 再次截图对比
echo "步骤 11: 再次截图对比"
echo "----------------------------------------"
DISPLAY=:1 scrot debug_screenshot_after_activate.png 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✅ 截图已保存: debug_screenshot_after_activate.png"
else
    echo "  ❌ 截图失败"
fi
echo ""

echo "=========================================="
echo "调试完成"
echo "=========================================="
echo ""
echo "生成的文件:"
echo "  - /tmp/forticlient-gui-debug.log (启动日志)"
echo "  - debug_screenshot.png (等待后的截图)"
echo "  - debug_screenshot_after_activate.png (激活后的截图)"
echo ""
echo "请检查:"
echo "  1. FortiClient 窗口是否真的打开了"
echo "  2. 截图中是否显示了 FortiClient 界面"
echo "  3. 是否有 SAML Login 按钮"
echo ""
