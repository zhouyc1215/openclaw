#!/bin/bash
# VPN 自动重连系统统一入口

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 设置环境变量
export DISPLAY="${DISPLAY:-:1}"
export NO_AT_BRIDGE=0

# 日志文件
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/vpn-$(date +%Y%m%d).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "VPN 自动重连系统启动"
log "=========================================="
log "DISPLAY: $DISPLAY"
log "工作目录: $SCRIPT_DIR"
log "日志文件: $LOG_FILE"
log ""

# 检查 Python 版本
if ! command -v python3 &> /dev/null; then
    log "❌ 错误: 未找到 python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
log "Python 版本: $PYTHON_VERSION"

# 检查依赖
log "检查依赖..."
MISSING_DEPS=()

if ! python3 -c "import yaml" 2>/dev/null; then
    MISSING_DEPS+=("pyyaml")
fi

if ! python3 -c "import cv2" 2>/dev/null; then
    MISSING_DEPS+=("opencv-python")
fi

if ! python3 -c "import numpy" 2>/dev/null; then
    MISSING_DEPS+=("numpy")
fi

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    log "⚠️  缺少依赖: ${MISSING_DEPS[*]}"
    log "正在安装..."
    pip3 install "${MISSING_DEPS[@]}" >> "$LOG_FILE" 2>&1
    log "✅ 依赖已安装"
fi

# 检查配置文件
CONFIG_FILE="$SCRIPT_DIR/config/config.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
    log "❌ 错误: 配置文件不存在: $CONFIG_FILE"
    exit 1
fi
log "✅ 配置文件: $CONFIG_FILE"
log ""

# 启动 watchdog
log "启动 VPN Watchdog..."
log ""

python3 "$SCRIPT_DIR/core/watchdog.py" -c "$CONFIG_FILE" 2>&1 | tee -a "$LOG_FILE"
