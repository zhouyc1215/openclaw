#!/bin/bash
# 使用命令行触发 VPN 连接，会自动打开 SAML 登录页面

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 使用命令行触发 VPN 连接..."

# 后台运行 openfortivpn，它会打开浏览器进行 SAML 认证
echo tsl123 | sudo -S openfortivpn -c /etc/openfortivpn/config &

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ VPN 连接已触发"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 等待 SAML 登录页面出现..."
