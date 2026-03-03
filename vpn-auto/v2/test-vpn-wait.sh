#!/bin/bash
# 测试 VPN 连接等待逻辑

echo "测试 VPN 连接等待逻辑..."
echo "================================"

python3 -c "
import logging
import time
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

from core.config_loader import load_config
from core.orchestrator import ReconnectOrchestrator

config = load_config()
orchestrator = ReconnectOrchestrator(config)

print('')
print('测试 wait_for_vpn_connection 方法')
print('=' * 60)

# 模拟等待 VPN 连接
result = orchestrator.wait_for_vpn_connection()

print('=' * 60)
print(f'结果: {result}')
"

echo ""
echo "================================"
echo "测试完成！"
