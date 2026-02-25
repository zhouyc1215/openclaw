#!/bin/bash
# 自动解决 Git 合并冲突，保留 HEAD 版本

files=(
  "src/cli/gateway-cli/dev.ts"
  "src/infra/openclaw-root.ts"
  "src/agents/pi-embedded-runner/run/attempt.ts"
  "src/agents/tools/cron-tool.ts"
  "src/agents/system-prompt.ts"
  "src/agents/model-scan.ts"
  "src/agents/workspace-templates.ts"
  "src/agents/workspace-templates.test.ts"
  "src/agents/openclaw-tools.ts"
  "src/agents/pi-embedded-subscribe.handlers.messages.ts"
  "src/plugins/manifest.ts"
  "src/plugins/install.ts"
  "src/plugins/loader.ts"
)

for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    echo "Resolving conflicts in $file..."
    # 使用 sed 删除冲突标记，保留 HEAD 版本
    sed -i '/^<<<<<<< HEAD/,/^=======$/d; /^>>>>>>> /d' "$file"
  fi
done

echo "All conflicts resolved!"
