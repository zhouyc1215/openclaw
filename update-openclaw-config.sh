#!/bin/bash
# 更新 openclaw.json 配置文件

cat > ~/.openclaw/openclaw.json << 'EOF'
{
  "meta": {
    "lastTouchedVersion": "2026.2.6-3",
    "lastTouchedAt": "2026-02-25T09:13:49.514Z"
  },
  "env": {
    "GEMINI_API_KEY": "AIzaSyC2w06KAtlzb50vBvjL_wY3sjWzzWrNyIU",
    "MINIMAX_API_KEY": "sk-api-PT9gHJYDG9PdBL097V52ddUKSoKh4OCZOHvkKRjbeAlvNZXJoy0GUcq3IHQCffPy0n-36YnB3jjvRDij7rC-K-C2hoejP6-BW4d1RkF3p9sLrcoKpDtfFPs"
  },
  "models": {
    "providers": {
      "qwen-portal": {
        "baseUrl": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "apiKey": "sk-3effff40719b46259d25ae1b16dfdaea",
        "api": "openai-completions",
        "models": [
          {
            "id": "qwen-plus",
            "name": "Qwen Plus",
            "reasoning": false,
            "input": ["text"],
            "cost": {
              "input": 0.0004,
              "output": 0.002,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": 131072,
            "maxTokens": 8192
          },
          {
            "id": "qwen-turbo",
            "name": "Qwen Turbo",
            "reasoning": false,
            "input": ["text"],
            "cost": {
              "input": 0.0003,
              "output": 0.0006,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": 131072,
            "maxTokens": 8192
          },
          {
            "id": "qwen-max",
            "name": "Qwen Max",
            "reasoning": false,
            "input": ["text"],
            "cost": {
              "input": 0.02,
              "output": 0.06,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": 32768,
            "maxTokens": 8192
          }
        ]
      },
      "minimax": {
        "baseUrl": "https://api.minimaxi.com/v1",
        "apiKey": "sk-api-PT9gHJYDG9PdBL097V52ddUKSoKh4OCZOHvkKRjbeAlvNZXJoy0GUcq3IHQCffPy0n-36YnB3jjvRDij7rC-K-C2hoejP6-BW4d1RkF3p9sLrcoKpDtfFPs",
        "api": "openai-completions",
        "models": [
          {
            "id": "MiniMax-M2.1",
            "name": "MiniMax M2.1",
            "reasoning": false,
            "input": ["text"],
            "cost": {
              "input": 15,
              "output": 60,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": 200000,
            "maxTokens": 8192
          }
        ]
      },
      "ollama": {
        "baseUrl": "http://127.0.0.1:11434/v1",
        "apiKey": "ollama-local",
        "api": "openai-completions",
        "models": [
          {
            "id": "qwen2.5:7b",
            "name": "Qwen 2.5 7B",
            "reasoning": false,
            "input": ["text"],
            "cost": {
              "input": 0,
              "output": 0,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": 32768,
            "maxTokens": 32768
          },
          {
            "id": "qwen2.5:3b",
            "name": "Qwen 2.5 3B (Local)",
            "reasoning": false,
            "input": ["text"],
            "cost": {
              "input": 0,
              "output": 0,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": 32768,
            "maxTokens": 8192
          },
          {
            "id": "qwen2.5:1.5b",
            "name": "Qwen 2.5 1.5B (Local)",
            "reasoning": false,
            "input": ["text"],
            "cost": {
              "input": 0,
              "output": 0,
              "cacheRead": 0,
              "cacheWrite": 0
            },
            "contextWindow": 32768,
            "maxTokens": 8192
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "ollama/qwen2.5:7b"
      },
      "models": {
        "qwen-portal/qwen-turbo": {
          "alias": "qwen-turbo"
        },
        "qwen-portal/qwen-plus": {
          "alias": "qwen-plus"
        },
        "qwen-portal/qwen-max": {
          "alias": "qwen-max"
        }
      },
      "compaction": {
        "mode": "safeguard"
      },
      "maxConcurrent": 4,
      "subagents": {
        "maxConcurrent": 8
      }
    }
  },
  "tools": {
    "allow": ["exec", "read", "write"],
    "deny": []
  },
  "messages": {
    "ackReactionScope": "group-mentions"
  },
  "commands": {
    "native": "auto",
    "nativeSkills": "auto"
  },
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "cli_a90d40fc70b89bc2",
      "appSecret": "jEFgKlvjq5c0aYRuh7YaecohSuV7IPUF",
      "domain": "feishu",
      "groupPolicy": "open",
      "connectionMode": "websocket"
    }
  },
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "lan",
    "auth": {
      "token": "test-token-123"
    }
  },
  "skills": {
    "install": {
      "nodeManager": "npm"
    }
  },
  "plugins": {
    "entries": {
      "feishu": {
        "enabled": true
      },
      "qwen-portal-auth": {
        "enabled": true
      }
    }
  }
}
EOF

echo "配置文件已更新: ~/.openclaw/openclaw.json"
