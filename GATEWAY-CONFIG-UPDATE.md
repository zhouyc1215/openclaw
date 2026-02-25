# Gateway 配置更新完成

## 更新内容

更新了 Gateway 配置，添加了 `controlUi.allowInsecureAuth` 选项。

## 新配置

```json
{
  "gateway": {
    "mode": "local",
    "bind": "lan",
    "port": 18789,
    "auth": {
      "mode": "token",
      "token": "test-token-123"
    },
    "controlUi": {
      "allowInsecureAuth": true
    }
  }
}
```

## 配置说明

### mode: "local"

- Gateway 运行在本地模式
- 不需要远程连接配置

### bind: "lan"

- 绑定到所有网络接口（0.0.0.0）
- 允许局域网内的设备访问
- 可以从 10.71.1.19 (Windows) 访问 10.71.1.116:18789

### port: 18789

- Gateway 监听端口
- HTTP 和 WebSocket 都使用此端口

### auth.mode: "token"

- 使用 token 认证模式
- 客户端需要提供正确的 token 才能连接

### auth.token: "test-token-123"

- 认证 token
- Control UI 和其他客户端需要使用此 token

### controlUi.allowInsecureAuth: true

- **重要**: 允许 Control UI 在非 HTTPS 环境下使用设备认证
- 在开发环境或局域网环境中很有用
- 生产环境建议使用 HTTPS

## 配置效果

### 1. 允许不安全的认证

启用 `allowInsecureAuth` 后，Control UI 可以：

- 在 HTTP（非 HTTPS）环境下工作
- 跳过某些安全检查
- 在局域网内更容易连接

### 2. 设备认证

- Control UI 可以使用设备身份认证
- 即使在 HTTP 环境下也能正常工作
- 不需要强制 HTTPS 或 localhost

### 3. Token 认证

- 仍然需要提供正确的 token
- Token: `test-token-123`
- 提供基本的访问控制

## 验证结果

```bash
$ clawdbot config get gateway
{
  "port": 18789,
  "mode": "local",
  "bind": "lan",
  "controlUi": {
    "allowInsecureAuth": true
  },
  "auth": {
    "mode": "token",
    "token": "test-token-123"
  }
}
```

## Gateway 状态

```
✅ 运行中
- PID: 66682
- 地址: 0.0.0.0:18789
- 认证: token (test-token-123)
- Control UI: 允许不安全认证
```

## 飞书状态

```
✅ 正常工作
- 状态: enabled, configured, running, works
```

## 访问方式

### 从 Windows (10.71.1.19) 访问

1. **浏览器访问**:

   ```
   http://10.71.1.116:18789/
   ```

2. **输入 Token**:

   ```
   test-token-123
   ```

3. **连接成功**:
   - WebSocket 连接应该正常建立
   - 不会因为 HTTP 环境而被拒绝
   - 设备认证可以正常工作

### 从本地访问

```bash
# 浏览器
http://localhost:18789/

# 或
http://127.0.0.1:18789/
```

## 安全注意事项

### allowInsecureAuth 的影响

**启用后**:

- ✅ 允许 HTTP 环境下的设备认证
- ✅ 简化开发和测试
- ✅ 局域网内更容易使用
- ⚠️ 降低了安全性
- ⚠️ 不适合公网暴露

**建议**:

- 开发环境: 可以启用
- 局域网环境: 可以启用
- 公网环境: 应该禁用，使用 HTTPS

### Token 安全

当前 token (`test-token-123`) 是测试用的：

- ⚠️ 过于简单
- ⚠️ 容易被猜测
- ⚠️ 不适合生产环境

**生产环境建议**:

```bash
# 生成强 token
clawdbot config set gateway.auth.token "$(openssl rand -base64 32)"
```

## 配置文件位置

- 主配置: `~/.openclaw/openclaw.json`
- 备份: `~/.openclaw/openclaw.json.bak.before-gateway-update`

## 相关脚本

- `update-gateway-config.py` - 初始更新脚本（有错误）
- `fix-gateway-config.py` - 修正后的脚本

## 故障排查

### Control UI 无法连接

1. **检查 token**:

   ```bash
   clawdbot config get gateway.auth.token
   ```

2. **检查 allowInsecureAuth**:

   ```bash
   clawdbot config get gateway.controlUi.allowInsecureAuth
   ```

3. **检查 Gateway 状态**:
   ```bash
   ss -ltnp | grep 18789
   ```

### 设备认证失败

如果仍然遇到设备认证问题：

1. **清除浏览器缓存**:
   - Ctrl + Shift + Delete
   - 清除所有缓存和 Cookie

2. **检查浏览器控制台**:
   - F12 打开开发者工具
   - 查看 Console 和 Network 标签
   - 检查 WebSocket 连接状态

3. **尝试 localhost**:
   - 在服务器本地浏览器访问 `http://localhost:18789/`
   - 如果本地可以，说明是网络问题

### 禁用 allowInsecureAuth

如果需要更高的安全性：

```bash
# 禁用不安全认证
clawdbot config set gateway.controlUi.allowInsecureAuth false

# 重启 Gateway
clawdbot gateway stop
clawdbot gateway run --bind lan --port 18789
```

然后需要：

- 使用 HTTPS
- 或只在 localhost 访问
- 或配置反向代理（如 nginx）提供 HTTPS

## 总结

Gateway 配置已成功更新：

- ✅ 绑定到 0.0.0.0:18789（局域网可访问）
- ✅ 使用 token 认证（test-token-123）
- ✅ 允许 Control UI 不安全认证
- ✅ Gateway 运行正常
- ✅ 飞书工作正常

现在可以从 Windows 设备 (10.71.1.19) 通过 HTTP 访问 Control UI 了。
