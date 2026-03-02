#!/bin/bash
# VPN 自动重连系统 - 完整部署脚本
# 用途：从零开始部署整个 VPN 监控和自动重连系统

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENCLAW_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "VPN 自动重连系统 - 完整部署"
echo "========================================"
echo ""
echo "部署目录: $SCRIPT_DIR"
echo "OpenClaw 目录: $OPENCLAW_DIR"
echo ""

# 步骤 1: 检查依赖
echo "步骤 1/6: 检查系统依赖..."
echo "----------------------------------------"

# 检查 FortiClient
if ! command -v forticlient &> /dev/null; then
    echo "❌ FortiClient 未安装"
    echo "请先安装 FortiClient VPN 客户端"
    exit 1
fi
echo "✅ FortiClient: $(forticlient --version 2>&1 | head -1 || echo 'installed')"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi
echo "✅ Python3: $(python3 --version)"

# 检查 X11
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:1
fi
echo "✅ DISPLAY: $DISPLAY"

# 步骤 2: 安装 Python 依赖
echo ""
echo "步骤 2/6: 安装 Python 依赖..."
echo "----------------------------------------"

REQUIRED_PACKAGES=("pyautogui" "opencv-python-headless" "Pillow")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! python3 -c "import ${package//-/_}" 2>/dev/null; then
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "安装缺失的包: ${MISSING_PACKAGES[*]}"
    pip3 install --user "${MISSING_PACKAGES[@]}"
else
    echo "✅ 所有 Python 依赖已安装"
fi

# 检查系统包
echo ""
echo "检查系统包..."
SYSTEM_PACKAGES=("scrot" "python3-tk")
MISSING_SYSTEM=()

for package in "${SYSTEM_PACKAGES[@]}"; do
    if ! dpkg -l | grep -q "^ii  $package"; then
        MISSING_SYSTEM+=("$package")
    fi
done

if [ ${#MISSING_SYSTEM[@]} -gt 0 ]; then
    echo "需要安装系统包: ${MISSING_SYSTEM[*]}"
    echo "运行: sudo apt-get install -y ${MISSING_SYSTEM[*]}"
    sudo apt-get install -y "${MISSING_SYSTEM[@]}"
else
    echo "✅ 所有系统包已安装"
fi

# 步骤 3: 配置 X11 权限
echo ""
echo "步骤 3/6: 配置 X11 权限..."
echo "----------------------------------------"

if xhost | grep -q "SI:localuser:$USER"; then
    echo "✅ X11 权限已配置"
else
    echo "配置 X11 权限..."
    xhost +SI:localuser:$USER
    echo "✅ X11 权限配置完成"
fi

# 步骤 4: 创建图像目录
echo ""
echo "步骤 4/6: 准备图像目录..."
echo "----------------------------------------"

mkdir -p "$SCRIPT_DIR/images"
echo "✅ 图像目录: $SCRIPT_DIR/images"

# 检查按钮图像
if [ -f "$SCRIPT_DIR/images/connect_button.png" ]; then
    echo "✅ 连接按钮图像已存在"
    ls -lh "$SCRIPT_DIR/images/connect_button.png"
else
    echo "⚠️  连接按钮图像不存在"
    echo ""
    echo "请运行以下命令捕获按钮图像："
    echo "  cd $SCRIPT_DIR"
    echo "  export DISPLAY=:1"
    echo "  python3 capture-button.py"
    echo ""
    read -p "是否现在捕获按钮图像？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        export DISPLAY=:1
        python3 "$SCRIPT_DIR/capture-button.py"
    else
        echo "⚠️  跳过按钮图像捕获，稍后可手动运行"
    fi
fi

# 步骤 5: 配置监控服务
echo ""
echo "步骤 5/6: 配置 systemd 服务..."
echo "----------------------------------------"

# 创建 systemd 服务文件
SERVICE_FILE="/etc/systemd/system/vpn-monitor.service"

echo "创建服务文件: $SERVICE_FILE"
sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=VPN Monitor Service (Semi-Auto Mode)
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
Environment="DISPLAY=:1"
Environment="XAUTHORITY=/home/$USER/.Xauthority"
Environment="PATH=/usr/local/bin:/usr/bin:/bin:/home/$USER/.local/bin"
ExecStart=$SCRIPT_DIR/vpn-monitor.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✅ 服务文件已创建"

# 重载 systemd
echo "重载 systemd..."
sudo systemctl daemon-reload

# 启用服务
echo "启用服务..."
sudo systemctl enable vpn-monitor

# 启动服务
echo "启动服务..."
sudo systemctl start vpn-monitor

# 等待服务启动
sleep 2

# 检查服务状态
echo ""
echo "检查服务状态..."
if sudo systemctl is-active --quiet vpn-monitor; then
    echo "✅ 服务运行正常"
    sudo systemctl status vpn-monitor --no-pager | head -15
else
    echo "❌ 服务启动失败"
    sudo systemctl status vpn-monitor --no-pager
    exit 1
fi

# 步骤 6: 测试系统
echo ""
echo "步骤 6/6: 测试系统..."
echo "----------------------------------------"

# 测试 VPN 状态检测
echo "测试 VPN 状态检测..."
VPN_STATUS=$(forticlient vpn status | grep "Status:" | awk '{print $2}')
echo "当前 VPN 状态: $VPN_STATUS"

# 测试 GUI 自动化（如果按钮图像存在）
if [ -f "$SCRIPT_DIR/images/connect_button.png" ]; then
    echo ""
    echo "测试 GUI 自动化..."
    read -p "是否测试 GUI 自动连接？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        export DISPLAY=:1
        python3 "$SCRIPT_DIR/gui-auto-connect.py"
    else
        echo "跳过 GUI 测试"
    fi
fi

# 完成
echo ""
echo "========================================"
echo "✅ 部署完成！"
echo "========================================"
echo ""
echo "系统状态："
echo "  - 监控服务: vpn-monitor.service (运行中)"
echo "  - 检查间隔: 60秒"
echo "  - 自动重连: 启用 (GUI 自动化)"
echo "  - 飞书通知: 启用"
echo ""
echo "常用命令："
echo "  查看日志: journalctl -u vpn-monitor -f"
echo "  重启服务: sudo systemctl restart vpn-monitor"
echo "  停止服务: sudo systemctl stop vpn-monitor"
echo "  服务状态: sudo systemctl status vpn-monitor"
echo ""
echo "手动测试："
echo "  GUI 自动连接: cd $SCRIPT_DIR && export DISPLAY=:1 && python3 gui-auto-connect.py"
echo "  捕获按钮: cd $SCRIPT_DIR && export DISPLAY=:1 && python3 capture-button.py"
echo ""
