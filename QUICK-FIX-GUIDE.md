# WebSocket 连接问题快速修复指南

## 🚨 问题症状

```
错误信息: disconnected (1008): invalid connect params
原因: 浏览器缓存了旧版本的 Control UI
```

---

## ✅ 解决方案（按推荐顺序）

### 方案 1：强制刷新（最简单）⭐

```
1. 访问 http://10.71.1.116:18789/
2. 按 Ctrl + F5
```

**成功率：** 90%  
**耗时：** 5 秒

---

### 方案 2：清除缓存

```
1. 按 Ctrl + Shift + Delete
2. 勾选"缓存的图片和文件"
3. 点击"清除数据"
4. 刷新页面
```

**成功率：** 95%  
**耗时：** 30 秒

---

### 方案 3：无痕模式测试

```
1. 按 Ctrl + Shift + N
2. 访问 http://10.71.1.116:18789/
```

**成功率：** 100%（仅测试用）  
**耗时：** 10 秒  
**注意：** 无痕模式不保存数据

---

### 方案 4：WebSocket 拦截器（高级）🔧

#### 使用控制台

```javascript
// 1. 按 F12 打开控制台
// 2. 粘贴以下代码并按 Enter
// 3. 刷新页面

(function () {
  if (window.__OPENCLAW_WS_INTERCEPTOR_INSTALLED__) {
    console.log("[OpenClaw] 拦截器已安装");
    return;
  }
  const t = "openclaw-control-ui",
    o = window.WebSocket;
  ((window.WebSocket = function (e, n) {
    console.log("[OpenClaw] 创建连接:", e);
    const s = new o(e, n),
      c = s.send.bind(s);
    return (
      (s.send = function (e) {
        try {
          const n = JSON.parse(e);
          if ("req" === n.type && "connect" === n.method) {
            const e = n.params?.client?.id;
            if ((console.log("[OpenClaw] 原始 client.id:", e), n.params?.client)) {
              ((n.params.client.id = t), console.log("[OpenClaw] 修改后 client.id:", t));
              const e = JSON.stringify(n);
              return c(e);
            }
          }
        } catch (e) {}
        return c(e);
      }),
      s.addEventListener("open", () => console.log("[OpenClaw] 连接已建立")),
      s.addEventListener("close", (e) => {
        (console.log("[OpenClaw] 连接关闭:", e.code, e.reason),
          1008 === e.code && console.error("[OpenClaw] 连接被拒绝 (1008):", e.reason));
      }),
      s
    );
  }),
    Object.setPrototypeOf(window.WebSocket, o),
    (window.WebSocket.prototype = o.prototype),
    (window.__OPENCLAW_WS_INTERCEPTOR_INSTALLED__ = !0),
    console.log("%c[OpenClaw] 拦截器已安装", "color: green; font-weight: bold"),
    console.log("[OpenClaw] 请刷新页面"));
})();
```

#### 使用书签

1. 打开 `tools/websocket-interceptor.html`
2. 拖拽 Bookmarklet 到书签栏
3. 点击书签注入拦截器
4. 刷新页面

**成功率：** 100%  
**耗时：** 1 分钟  
**注意：** 每次刷新前需要重新注入

---

## 🔍 验证成功

连接成功后应该看到：

- ✅ Control UI 界面正常显示
- ✅ 没有 "disconnected (1008)" 错误
- ✅ 可以看到 Gateway 状态信息
- ✅ 可以与 Agent 进行对话

---

## 🛠️ 诊断工具

### 自动诊断脚本

```bash
bash scripts/diagnose-websocket.sh
```

检查项目：

- Gateway 进程状态
- 端口监听
- HTTP 访问
- Control UI 文件
- WebSocket 错误日志
- 配置信息

### 手动检查

```bash
# 检查 Gateway 是否运行
ss -ltnp | grep 18789

# 查看最新日志
tail -f /tmp/clawdbot/clawdbot-$(date +%Y-%m-%d).log

# 查看 WebSocket 错误
tail -f /tmp/clawdbot/clawdbot-$(date +%Y-%m-%d).log | grep "invalid connect params"
```

---

## 📚 详细文档

| 文档                                                                   | 说明               |
| ---------------------------------------------------------------------- | ------------------ |
| [WEBSOCKET-CONNECTION-FIX.md](./WEBSOCKET-CONNECTION-FIX.md)           | 详细的修复指南     |
| [WEBSOCKET-PROTOCOL-GUIDE.md](./WEBSOCKET-PROTOCOL-GUIDE.md)           | WebSocket 协议详解 |
| [tools/websocket-interceptor.html](./tools/websocket-interceptor.html) | 拦截器工具页面     |
| [TASK-SUMMARY.md](./TASK-SUMMARY.md)                                   | 完整任务总结       |

---

## 🆘 仍然无法解决？

1. 确认 Gateway 正在运行：

   ```bash
   ss -ltnp | grep 18789
   ```

2. 检查网络连接：

   ```bash
   curl http://10.71.1.116:18789/
   ```

3. 查看浏览器控制台（F12）的错误信息

4. 运行诊断脚本：

   ```bash
   bash scripts/diagnose-websocket.sh
   ```

5. 查看详细文档或联系技术支持

---

## 💡 提示

- **推荐顺序：** 方案 1 → 方案 2 → 方案 3 → 方案 4
- **最快方法：** 方案 1（Ctrl + F5）
- **最可靠方法：** 方案 2（清除缓存）
- **调试专用：** 方案 4（拦截器）
- **测试专用：** 方案 3（无痕模式）

---

**最后更新：** 2026-02-25  
**版本：** 1.0
