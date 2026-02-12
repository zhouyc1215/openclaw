#!/bin/bash

# 设置工作目录
cd /home/tsl/openclaw

# 检查是否有未提交的变更
if [ -n "$(git status --porcelain)" ]; then
  # 添加所有变更和新文件
  git add .
  
  # 提交变更
  git commit -m "Auto-commit: $(date +'%Y-%m-%d %H:%M:%S')"
  
  # 推送到远端仓库
  git push origin main
fi