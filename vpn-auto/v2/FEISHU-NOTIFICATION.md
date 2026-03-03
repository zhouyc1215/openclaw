# 飞书通知功能说明

## 功能概述

当 VPN 自动重连系统检测到需要手动完成 SAML 认证时，会自动截取当前屏幕并发送到飞书，提醒用户完成认证。

## 工作原理

### 触发条件

飞书通知会在以下情况下触发：

1. ✅ 系统成功点击了 SAML Login 按钮
2. ⏱️ 等待 30 秒后 VPN 仍未连接
3. 📸 自动截取当前屏幕
4. 📤 发送截图到飞书

### 不会触发的情况

- ❌ 点击按钮失败（可能是其他问题，不是 SAML 认证问题）
- ❌ VPN 已经连接（正常状态）
- ❌ 飞书通知未启用

## 配置方法

### 1. 编辑配置文件

```bash
nano vpn-auto/v2/config/config.yaml
```

### 2. 配置飞书通知

```yaml
feishu:
  enabled: true # 启用飞书通知
  user_id: "ou_b3afb7d2133e4d689be523fc48f3d2b3" # 你的飞书用户 ID
  openclaw_bin: "/usr/bin/pnpm openclaw" # openclaw 命令路径
```

### 3. 获取飞书用户 ID

方法 1：从飞书个人资料中查看

方法 2：使用 OpenClaw 命令查询

```bash
cd ~/openclaw
pnpm openclaw channels status --channel feishu
```

### 4. 确保 OpenClaw Gateway 运行

```bash
# 检查 Gateway 状态
pnpm openclaw gateway status

# 如果未运行，启动 Gateway
pnpm openclaw gateway run --bind loopback --port 18789
```

### 5. 测试飞书通知

```bash
cd vpn-auto/v2
bash test-feishu-notify.sh
```

## 消息示例

当需要手动认证时，你会收到：

1. **截图**：当前屏幕的截图（包含 SAML 认证页面）
2. **文本消息**：
   ```
   ⚠️ VPN 需要手动完成 SAML 认证
   请在浏览器中完成认证流程
   ```

## 故障排查

### 问题 1：未收到飞书通知

**检查清单**：

1. 确认 `feishu.enabled` 设置为 `true`
2. 确认 `feishu.user_id` 正确
3. 确认 OpenClaw Gateway 正在运行
4. 查看日志：`tail -f vpn-auto/v2/logs/vpn-*.log`

### 问题 2：收到通知但没有截图

**可能原因**：

- DISPLAY 环境变量设置错误
- scrot 命令未安装
- 截图权限问题

**解决方案**：

```bash
# 检查 DISPLAY
echo $DISPLAY

# 手动测试截图
DISPLAY=:1 scrot /tmp/test.png

# 安装 scrot
sudo apt-get install scrot
```

### 问题 3：OpenClaw 命令找不到

**解决方案**：

```bash
# 检查 openclaw 命令路径
which pnpm

# 更新配置文件中的 openclaw_bin
nano vpn-auto/v2/config/config.yaml
```

## 技术实现

### 核心模块

- `core/feishu_notifier.py`：飞书通知器
- `core/orchestrator.py`：重连编排器（集成飞书通知）

### 发送流程

```
1. 检测到需要 SAML 认证
   ↓
2. 调用 feishu_notifier.take_screenshot_and_send()
   ↓
3. 使用 scrot 截取屏幕
   ↓
4. 调用 openclaw message send 发送图片
   ↓
5. 发送文本说明消息
```

### 命令示例

```bash
# 发送文本消息
cd ~/openclaw && pnpm openclaw message send \
  --channel feishu \
  --target ou_xxx \
  --message "测试消息"

# 发送图片
cd ~/openclaw && pnpm openclaw message send \
  --channel feishu \
  --target ou_xxx \
  --media /tmp/screenshot.png
```

## 安全建议

1. **保护配置文件**：

   ```bash
   chmod 600 vpn-auto/v2/config/config.yaml
   ```

2. **限制日志访问**：

   ```bash
   chmod 700 vpn-auto/v2/logs/
   ```

3. **定期清理截图**：
   - 截图保存在 `/tmp/vpn-saml-*.png`
   - 发送后自动删除
   - 系统重启后自动清理

## 扩展功能

### 自定义消息内容

编辑 `core/orchestrator.py`：

```python
self.feishu.take_screenshot_and_send(
    caption="⚠️ 自定义消息内容\n"
            "第二行内容"
)
```

### 发送到多个用户

修改 `core/feishu_notifier.py`，支持多个 `user_id`：

```python
user_ids = ["ou_xxx1", "ou_xxx2", "ou_xxx3"]
for user_id in user_ids:
    self.send_image(image_path, caption)
```

### 集成其他通知渠道

参考 `core/feishu_notifier.py` 的实现，可以添加：

- Telegram 通知
- 企业微信通知
- 钉钉通知
- 邮件通知

## 参考资料

- [OpenClaw 文档](https://docs.openclaw.ai/)
- [飞书开放平台](https://open.feishu.cn/)
- [scrot 文档](https://github.com/resurrecting-open-source-projects/scrot)

---

**版本**: v1.0  
**最后更新**: 2024-01-15
