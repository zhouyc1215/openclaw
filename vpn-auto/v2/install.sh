#!/bin/bash
# VPN 自动重连系统 v2 安装脚本

set -e

# 检查是否以 root 运行
if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 获取实际用户
USER_HOME=$(eval echo ~${SUDO_USER})
USERNAME=${SUDO_USER}

echo "=========================================="
echo "VPN 自动重连系统 v2 安装"
echo "=========================================="
echo "用户: $USERNAME"
echo "主目录: $USER_HOME"
echo ""

# 1. 安装系统依赖
echo "===> 安装系统依赖"
apt update
apt install -y \
    python3 \
    python3-pip \
    xvfb \
    xfce4 \
    scrot \
    xdotool \
    imagemagick \
    python3-opencv \
    python3-pyatspi \
    supervisor

echo "✅ 系统依赖已安装"
echo ""

# 2. 安装 Python 依赖
echo "===> 安装 Python 依赖"
pip3 install --upgrade pip
pip3 install pyautogui pillow numpy pyyaml

echo "✅ Python 依赖已安装"
echo ""

# 3. 创建项目结构
echo "===> 创建项目结构"
PROJECT_DIR="$USER_HOME/vpn-auto/v2"

# 创建目录
mkdir -p "$PROJECT_DIR"/{core,drivers,services,config,logs}

# 创建 __init__.py 文件
touch "$PROJECT_DIR/core/__init__.py"
touch "$PROJECT_DIR/drivers/__init__.py"

echo "✅ 项目结构已创建"
echo ""

# 4. 设置权限
echo "===> 设置权限"
chown -R $USERNAME:$USERNAME "$USER_HOME/vpn-auto"
chmod 700 "$PROJECT_DIR/run.sh"
chmod 700 "$PROJECT_DIR/services/"*.sh
chmod 600 "$PROJECT_DIR/config/config.yaml"

echo "✅ 权限已设置"
echo ""

# 5. 安装 systemd 服务（可选）
echo "===> 安装 systemd 服务"
read -p "是否安装 systemd 服务？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cp "$PROJECT_DIR/vpn-auto.service" /etc/systemd/system/
    systemctl daemon-reload
    echo "✅ systemd 服务已安装"
    echo ""
    echo "启用并启动服务："
    echo "  sudo systemctl enable --now vpn-auto.service"
    echo ""
    echo "查看状态："
    echo "  sudo systemctl status vpn-auto.service"
    echo ""
    echo "查看日志："
    echo "  sudo journalctl -u vpn-auto.service -f"
else
    echo "跳过 systemd 服务安装"
fi
echo ""

# 6. 配置 sudo 免密码
echo ""
echo "配置 sudo 免密码..."
if [ -f "$PROJECT_DIR/forticlient-sudoers" ]; then
    cp "$PROJECT_DIR/forticlient-sudoers" /etc/sudoers.d/forticlient
    chmod 440 /etc/sudoers.d/forticlient
    echo "✅ sudo 免密码配置完成"
else
    echo "⚠️  forticlient-sudoers 文件不存在，跳过"
fi

# 7. 配置 polkit 免密码
echo ""
echo "配置 polkit 免密码（FortiClient GUI 启动）..."
if [ -f "$PROJECT_DIR/forticlient-polkit.pkla" ]; then
    cp "$PROJECT_DIR/forticlient-polkit.pkla" /etc/polkit-1/localauthority/50-local.d/50-forticlient.pkla
    chmod 644 /etc/polkit-1/localauthority/50-local.d/50-forticlient.pkla
    systemctl restart polkit
    echo "✅ polkit 免密码配置完成"
else
    echo "⚠️  forticlient-polkit.pkla 文件不存在，跳过"
fi

# 8. 完成
echo "=========================================="
echo "✅ 安装完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 编辑配置文件："
echo "   nano $PROJECT_DIR/config/config.yaml"
echo ""
echo "2. 测试运行："
echo "   bash $PROJECT_DIR/run.sh"
echo ""
echo "3. 安装 systemd 服务（如果之前跳过）："
echo "   sudo cp $PROJECT_DIR/vpn-auto.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable --now vpn-auto.service"
echo ""
echo "4. 查看日志："
echo "   tail -f $PROJECT_DIR/logs/vpn-*.log"
echo ""
