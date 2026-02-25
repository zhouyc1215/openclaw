# WebSocket 连接错误修复指南

## 问题描述

Control UI 页面可以打开，但 WebSocket 连接失败，错误信息：

```
disconnected (1008): invalid connect params: at /client/id: must be equal to constant; at /client/id: must match a schema in anyOf
```

## 问题原因

浏览器缓存了旧版本的 Control UI JavaScript 文件，导致发送的 WebSocket 连接参数与 Gateway 期望的格式不匹配。

## 解决方案

### 方法 1：强制刷新浏览器缓存（推荐）✅

在 Windows Chrome 浏览器中：

**快速方法（推荐）：**

1. 打开 `http://10.71.1.116:18789/`
2. 按 `Ctrl + F5` 强制刷新页面（跳过缓存）
3. 如果还不行，按 `Ctrl + Shift + R` 硬性重新加载

**完整清除缓存：**

1. 打开 `http://10.71.1.116:18789/`
2. 按 `Ctrl + Shift + Delete` 打开清除浏览数据对话框
3. 时间范围选择"全部时间"
4. 只勾选"缓存的图片和文件"
5. 点击"清除数据"
6. 刷新页面

### 方法 2：使用无痕模式测试

1. 按 `Ctrl + Shift + N` 打开无痕窗口
2. 访问 `http://10.71.1.116:18789/`
3. 查看是否能正常连接
4. 如果无痕模式可以连接，说明确实是缓存问题

### 方法 3：检查 Control UI 版本

在浏览器开发者工具中（按 F12）：

1. 切换到 Network 标签
2. 刷新页面（F5）
3. 查找 `index-*.js` 文件
4. 检查文件名是否为 `index-BeKTXH1m.js`（最新版本）
5. 如果不是，说明浏览器仍在使用缓存，需要强制刷新

### 方法 4：禁用缓存（开发调试用）

在浏览器开发者工具中（F12）：

1. 切换到 Network 标签
2. 勾选"Disable cache"（禁用缓存）
3. 保持开发者工具打开
4. 刷新页面
5. 这样每次刷新都会重新加载资源

### 方法 5：手动修改 client.id（高级）⚠️

如果你熟悉浏览器开发者工具和 JavaScript，可以手动修改 client.id：

#### 步骤 1：打开浏览器控制台

1. 访问 http://10.71.1.116:18789/
2. 按 F12 打开开发者工具
3. 切换到 Console 标签

#### 步骤 2：拦截并修改 WebSocket 连接

在控制台中执行以下代码：

```javascript
// 保存原始 WebSocket 构造函数
const OriginalWebSocket = window.WebSocket;

// 创建代理 WebSocket
window.WebSocket = function (url, protocols) {
  console.log("WebSocket 连接:", url);

  // 创建原始连接
  const ws = new OriginalWebSocket(url, protocols);

  // 拦截 send 方法
  const originalSend = ws.send.bind(ws);
  ws.send = function (data) {
    try {
      const frame = JSON.parse(data);

      // 如果是 connect 请求，修改 client.id
      if (frame.type === "req" && frame.method === "connect") {
        console.log("原始 client.id:", frame.params?.client?.id);

        // 修改为服务器允许的值
        if (frame.params?.client) {
          frame.params.client.id = "openclaw-control-ui";
          console.log("修改后 client.id:", frame.params.client.id);
        }

        // 发送修改后的数据
        return originalSend(JSON.stringify(frame));
      }
    } catch (e) {
      // 如果不是 JSON，直接发送
    }

    return originalSend(data);
  };

  return ws;
};

console.log("WebSocket 拦截器已安装，请刷新页面");
```

#### 步骤 3：刷新页面

执行代码后，按 F5 刷新页面，拦截器会自动修改 client.id。

#### 允许的 client.id 值

服务器当前接受以下值：

- `openclaw-control-ui` ✓ (推荐)
- `webchat-ui`
- `webchat`
- `cli`
- `gateway-client`
- `openclaw-macos`
- `openclaw-ios`
- `openclaw-android`
- `node-host`
- `test`
- `fingerprint`
- `openclaw-probe`

#### 注意事项

⚠️ 这是临时解决方案，每次刷新页面前都需要重新执行拦截代码。

⚠️ 建议仅用于调试和测试，生产环境应该使用正确版本的 Control UI。

## 验证修复

成功连接后，你应该能看到：

- Control UI 界面正常显示
- 没有 "disconnected (1008)" 错误
- 可以看到 Gateway 状态信息
- 可以与 Agent 进行对话

## 技术细节

### 期望的 client.id 值

Gateway 期望 Control UI 发送以下 client.id 值之一：

- `openclaw-control-ui` ✓（Control UI 应该使用这个）
- `webchat-ui`
- `webchat`
- `cli`
- `gateway-client`
- `openclaw-macos`
- `openclaw-ios`
- `openclaw-android`
- `node-host`
- `test`
- `fingerprint`
- `openclaw-probe`

### 最新构建信息

Control UI 已重新构建：

- 构建时间：2026-02-25 08:17
- 版本：2026.2.6-3
- 文件：
  - `dist/control-ui/index.html` (0.69 KB)
  - `dist/control-ui/assets/index-DWhx-9JL.css` (83.87 KB)
  - `dist/control-ui/assets/index-BeKTXH1m.js` (542.77 KB)

### Gateway 配置

当前 Gateway 配置：

```json
{
  "gateway": {
    "mode": "local",
    "bind": "lan",
    "port": 18789
  }
}
```

Gateway 正在运行：

- 进程 ID：24896
- 绑定地址：0.0.0.0:18789
- 可从局域网访问：http://10.71.1.116:18789/

## 如果问题仍然存在

### 步骤 1：确认 Gateway 正在运行

```bash
# 检查 Gateway 进程
ss -ltnp | grep 18789

# 应该看到类似输出：
# LISTEN 0 511 0.0.0.0:18789 0.0.0.0:* users:(("clawdbot-gatewa",pid=24896,fd=23))
```

### 步骤 2：查看 Gateway 日志

```bash
# 实时查看日志
tail -f /tmp/clawdbot/clawdbot-$(date +%Y-%m-%d).log

# 筛选 WebSocket 错误
tail -f /tmp/clawdbot/clawdbot-$(date +%Y-%m-%d).log | grep "invalid connect params"
```

### 步骤 3：检查浏览器控制台

按 F12 打开开发者工具，查看：

1. **Console 标签** - 查看 JavaScript 错误
2. **Network 标签** - 查看 WebSocket 连接状态
   - 筛选 WS 类型
   - 查看连接的状态码和错误信息
3. **Application 标签** - 清除 Storage
   - 点击 "Clear site data"

### 步骤 4：测试基本连接

```bash
# 从 Linux 服务器本地测试
curl http://localhost:18789/

# 从 Windows 测试（PowerShell）
Invoke-WebRequest -Uri http://10.71.1.116:18789/

# 使用 wscat 测试 WebSocket（需要先安装）
npm install -g wscat
wscat -c ws://10.71.1.116:18789/
```

### 步骤 5：重启 Gateway

如果以上都不行，尝试重启 Gateway：

```bash
# 停止 Gateway
pkill -9 -f clawdbot-gateway

# 启动 Gateway
nohup clawdbot gateway run --bind lan --port 18789 --force > /tmp/clawdbot-gateway.log 2>&1 &

# 等待几秒后检查
sleep 3
ss -ltnp | grep 18789
```

## 相关文档

- [Gateway LAN Access Setup](./GATEWAY-LAN-ACCESS-SETUP.md)
- [Control UI Setup Complete](./CONTROL-UI-SETUP-COMPLETE.md)
- [OpenClaw Architecture](./OPENCLAW-ARCHITECTURE.md)
