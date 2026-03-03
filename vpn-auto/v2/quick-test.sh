#!/bin/bash
# 快速测试 VPN 自动重连系统

cd "$(dirname "$0")"

echo "=========================================="
echo "VPN 自动重连系统 v2 快速测试"
echo "=========================================="
echo ""

# 测试配置加载
echo "1. 测试配置加载..."
python3 -c "
from core.config_loader import load_config
try:
    config = load_config()
    print('✅ 配置加载成功')
    print(f'   - VPN 接口: {config[\"network\"][\"vpn_interface\"]}')
    print(f'   - 检测间隔: {config[\"network\"][\"check_interval\"]} 秒')
except Exception as e:
    print(f'❌ 配置加载失败: {e}')
"
echo ""

# 测试网络检测
echo "2. 测试网络检测..."
python3 -c "
from core.config_loader import load_config
from core.network_check import NetworkChecker
try:
    config = load_config()
    checker = NetworkChecker(config)
    is_connected = checker.is_vpn_connected()
    if is_connected:
        print('✅ VPN 已连接')
    else:
        print('⚠️  VPN 未连接')
except Exception as e:
    print(f'❌ 网络检测失败: {e}')
"
echo ""

# 测试驱动加载
echo "3. 测试驱动加载..."
DISPLAY=:1 python3 -c "
from core.config_loader import load_config
from core.orchestrator import ReconnectOrchestrator
try:
    config = load_config()
    orchestrator = ReconnectOrchestrator(config)
    print(f'✅ 已加载 {len(orchestrator.drivers)} 个驱动')
    for driver in orchestrator.drivers:
        print(f'   - {driver.__class__.__name__}')
except Exception as e:
    print(f'❌ 驱动加载失败: {e}')
"
echo ""

echo "=========================================="
echo "✅ 核心功能测试完成"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 等待 apt 安装完成（可选的桌面环境组件）"
echo "2. 编辑配置文件: nano config/config.yaml"
echo "3. 运行完整测试: bash run.sh"
echo ""
