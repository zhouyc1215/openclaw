#!/bin/bash
# 诊断点击问题
# 分析为什么点击没有效果

export DISPLAY=:1

echo "========================================"
echo "诊断点击问题"
echo "========================================"
echo ""

# 1. 检查 FortiClient 窗口
echo "1. 检查 FortiClient 窗口..."
WINDOWS=$(xdotool search --name "FortiClient")
WINDOW_COUNT=$(echo "$WINDOWS" | wc -l)

echo "   找到 $WINDOW_COUNT 个 FortiClient 窗口:"
for WID in $WINDOWS; do
    WIN_NAME=$(xdotool getwindowname "$WID" 2>/dev/null || echo "未知")
    WIN_PID=$(xdotool getwindowpid "$WID" 2>/dev/null || echo "未知")
    echo "   - 窗口 ID: $WID"
    echo "     名称: $WIN_NAME"
    echo "     PID: $WIN_PID"
done
echo ""

# 2. 检查当前鼠标位置
echo "2. 当前鼠标位置..."
MOUSE_INFO=$(xdotool getmouselocation --shell)
eval "$MOUSE_INFO"
echo "   X = $X"
echo "   Y = $Y"
echo "   窗口 ID = $WINDOW"
echo ""

# 3. 截取当前屏幕
echo "3. 截取当前屏幕..."
scrot diagnose_screen.png
echo "   ✅ 截图已保存: diagnose_screen.png"
echo ""

# 4. 检查按钮图像
echo "4. 检查按钮图像..."
if [ -f "images/saml_login_button.png" ]; then
    SIZE=$(identify images/saml_login_button.png 2>/dev/null | awk '{print $3}')
    echo "   ✅ 按钮图像存在: $SIZE"
else
    echo "   ❌ 按钮图像不存在"
fi
echo ""

# 5. 测试不同的点击方式
echo "5. 测试不同的点击方式..."
echo ""

BUTTON_X=942
BUTTON_Y=787

# 方法 1: 直接点击
echo "   方法 1: xdotool 直接点击 ($BUTTON_X, $BUTTON_Y)"
xdotool mousemove --sync "$BUTTON_X" "$BUTTON_Y"
sleep 0.2
xdotool click 1
sleep 1
echo "   ✅ 已执行"
echo ""

# 方法 2: 激活窗口后点击
echo "   方法 2: 激活窗口后点击"
MAIN_WINDOW=$(xdotool search --name "FortiClient" | head -1)
if [ -n "$MAIN_WINDOW" ]; then
    xdotool windowactivate --sync "$MAIN_WINDOW"
    sleep 0.3
    xdotool mousemove --sync "$BUTTON_X" "$BUTTON_Y"
    sleep 0.2
    xdotool click 1
    sleep 1
    echo "   ✅ 已执行"
else
    echo "   ❌ 未找到窗口"
fi
echo ""

# 方法 3: 使用窗口相对坐标
echo "   方法 3: 使用窗口相对坐标点击"
if [ -n "$MAIN_WINDOW" ]; then
    # 获取窗口位置
    WIN_INFO=$(xdotool getwindowgeometry "$MAIN_WINDOW")
    echo "   窗口信息:"
    echo "$WIN_INFO" | sed 's/^/     /'
    
    xdotool windowactivate --sync "$MAIN_WINDOW"
    sleep 0.3
    
    # 尝试点击窗口内的相对位置
    # 假设按钮在窗口中央下方
    xdotool mousemove --window "$MAIN_WINDOW" --sync 400 400
    sleep 0.2
    xdotool click 1
    sleep 1
    echo "   ✅ 已执行"
else
    echo "   ❌ 未找到窗口"
fi
echo ""

echo "========================================"
echo "诊断完成"
echo "========================================"
echo ""
echo "请检查 FortiClient 窗口是否有任何反应"
echo ""
echo "如果所有方法都无效，可能的原因："
echo "1. 按钮坐标不正确"
echo "2. 窗口需要特殊的激活方式"
echo "3. 按钮可能是 Web 内容（需要使用浏览器自动化）"
echo "4. 应用可能有点击保护机制"
echo ""
echo "建议："
echo "1. 运行 ./find-button-coords.sh 手动定位按钮"
echo "2. 检查 FortiClient 是否使用 Electron/Web 技术"
echo "3. 考虑使用键盘快捷键代替鼠标点击"
