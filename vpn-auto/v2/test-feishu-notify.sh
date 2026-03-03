#!/bin/bash
# 测试飞书通知功能

set -e

cd "$(dirname "$0")"

echo "测试飞书通知功能..."
echo "================================"

# 测试 Python 模块导入
echo "1. 测试模块导入..."
python3 -c "
from core.config_loader import load_config
from core.feishu_notifier import FeishuNotifier

config = load_config()
notifier = FeishuNotifier(config)
print(f'飞书通知器已初始化')
print(f'启用状态: {notifier.enabled}')
print(f'用户 ID: {notifier.user_id}')
"

echo ""
echo "2. 测试发送文本消息..."
python3 -c "
from core.config_loader import load_config
from core.feishu_notifier import FeishuNotifier

config = load_config()
notifier = FeishuNotifier(config)
result = notifier.send_text('🧪 VPN 自动重连系统测试消息')
print(f'发送结果: {result}')
"

echo ""
echo "3. 测试截图并发送..."
python3 -c "
from core.config_loader import load_config
from core.feishu_notifier import FeishuNotifier

config = load_config()
notifier = FeishuNotifier(config)
result = notifier.take_screenshot_and_send(
    caption='🧪 VPN 自动重连系统 - 截图测试'
)
print(f'截图发送结果: {result}')
"

echo ""
echo "================================"
echo "测试完成！"
