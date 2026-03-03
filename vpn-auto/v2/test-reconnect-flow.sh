#!/bin/bash
# 测试完整的重连流程

set -e

cd "$(dirname "$0")"

echo "测试 VPN 重连流程..."
echo "================================"

# 测试重连流程
echo "执行重连流程..."
python3 -c "
import logging
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
print('=' * 60)
print('开始 VPN 重连流程')
print('=' * 60)

result = orchestrator.reconnect()

print('')
print('=' * 60)
if result:
    print('✅ VPN 重连成功')
else:
    print('❌ VPN 重连失败（可能需要手动 SAML 认证）')
print('=' * 60)
"

echo ""
echo "================================"
echo "测试完成！"
