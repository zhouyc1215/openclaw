#!/usr/bin/env python3
import json
import os

config_path = os.path.expanduser('~/.openclaw/openclaw.json')

# 读取当前配置
with open(config_path, 'r') as f:
    config = json.load(f)

# 更新 Gateway 配置
config['gateway'] = {
    "mode": "local",
    "bind": "0.0.0.0",
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

print("Gateway 配置已更新:")
print(json.dumps(config['gateway'], indent=2, ensure_ascii=False))
