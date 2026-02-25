#!/usr/bin/env python3
import json
import os

config_path = os.path.expanduser('~/.openclaw/openclaw.json')

# 读取当前配置
with open(config_path, 'r') as f:
    config = json.load(f)

# 更新 Gateway 配置（bind 应该是 "lan" 而不是 "0.0.0.0"）
config['gateway'] = {
    "mode": "local",
    "bind": "lan",  # 修正：使用 "lan" 而不是 "0.0.0.0"
    "port": 18789,
    "auth": {
        "mode": "token",
        "token": "test-token-123"
    },
    "controlUi": {
        "allowInsecureAuth": True
    }
}

# 写回配置文件
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("Gateway 配置已修正:")
print(json.dumps(config['gateway'], indent=2, ensure_ascii=False))
print("\n注意: bind 使用 'lan' (绑定到 0.0.0.0)，而不是直接使用 '0.0.0.0'")
