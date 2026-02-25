/**
 * OpenClaw WebSocket Client ID 拦截器
 *
 * 用途：修改 WebSocket 连接中的 client.id 为服务器允许的值
 * 使用方法：
 *   1. 在浏览器控制台中执行此脚本
 *   2. 或创建书签，将下面的 bookmarklet 代码保存为书签
 *   3. 刷新页面，拦截器会自动工作
 */

(function () {
  "use strict";

  // 配置
  const CONFIG = {
    // 目标 client.id（服务器允许的值）
    targetClientId: "openclaw-control-ui",

    // 是否显示调试信息
    debug: true,

    // 允许的 client.id 列表（用于验证）
    allowedClientIds: [
      "openclaw-control-ui",
      "webchat-ui",
      "webchat",
      "cli",
      "gateway-client",
      "openclaw-macos",
      "openclaw-ios",
      "openclaw-android",
      "node-host",
      "test",
      "fingerprint",
      "openclaw-probe",
    ],
  };

  // 检查是否已经安装
  if (window.__OPENCLAW_WS_INTERCEPTOR_INSTALLED__) {
    console.log("[OpenClaw] WebSocket 拦截器已安装");
    return;
  }

  // 日志函数
  function log(...args) {
    if (CONFIG.debug) {
      console.log("[OpenClaw WS Interceptor]", ...args);
    }
  }

  // 保存原始 WebSocket 构造函数
  const OriginalWebSocket = window.WebSocket;

  // 创建代理 WebSocket
  window.WebSocket = function (url, protocols) {
    log("创建 WebSocket 连接:", url);

    // 创建原始连接
    const ws = new OriginalWebSocket(url, protocols);

    // 拦截 send 方法
    const originalSend = ws.send.bind(ws);
    ws.send = function (data) {
      try {
        // 尝试解析为 JSON
        const frame = JSON.parse(data);

        // 检查是否是 connect 请求
        if (frame.type === "req" && frame.method === "connect") {
          const originalClientId = frame.params?.client?.id;
          log("检测到 connect 请求");
          log("原始 client.id:", originalClientId);

          // 修改 client.id
          if (frame.params?.client) {
            frame.params.client.id = CONFIG.targetClientId;
            log("修改后 client.id:", frame.params.client.id);

            // 验证是否在允许列表中
            if (!CONFIG.allowedClientIds.includes(CONFIG.targetClientId)) {
              console.warn("[OpenClaw] 警告: client.id 不在允许列表中:", CONFIG.targetClientId);
            }

            // 发送修改后的数据
            const modifiedData = JSON.stringify(frame);
            log("发送修改后的 connect 请求");
            return originalSend(modifiedData);
          }
        }
      } catch (e) {
        // 如果不是 JSON 或解析失败，直接发送原始数据
      }

      // 其他消息直接发送
      return originalSend(data);
    };

    // 监听连接事件
    ws.addEventListener("open", () => {
      log("WebSocket 连接已建立");
    });

    ws.addEventListener("close", (event) => {
      log("WebSocket 连接已关闭", {
        code: event.code,
        reason: event.reason,
      });

      if (event.code === 1008) {
        console.error("[OpenClaw] 连接被拒绝 (1008)，可能是 client.id 验证失败");
        console.error("[OpenClaw] 原因:", event.reason);
      }
    });

    ws.addEventListener("error", (error) => {
      console.error("[OpenClaw] WebSocket 错误:", error);
    });

    return ws;
  };

  // 复制原始 WebSocket 的静态属性
  Object.setPrototypeOf(window.WebSocket, OriginalWebSocket);
  window.WebSocket.prototype = OriginalWebSocket.prototype;

  // 标记已安装
  window.__OPENCLAW_WS_INTERCEPTOR_INSTALLED__ = true;

  // 显示安装成功消息
  console.log("%c[OpenClaw] WebSocket 拦截器已安装", "color: green; font-weight: bold");
  console.log("[OpenClaw] 目标 client.id:", CONFIG.targetClientId);
  console.log("[OpenClaw] 请刷新页面以应用拦截器");

  // 提供卸载函数
  window.__OPENCLAW_WS_INTERCEPTOR_UNINSTALL__ = function () {
    window.WebSocket = OriginalWebSocket;
    delete window.__OPENCLAW_WS_INTERCEPTOR_INSTALLED__;
    delete window.__OPENCLAW_WS_INTERCEPTOR_UNINSTALL__;
    console.log("[OpenClaw] WebSocket 拦截器已卸载");
  };
})();

/**
 * Bookmarklet 版本（压缩后的代码，可以保存为浏览器书签）
 *
 * 使用方法：
 * 1. 创建一个新书签
 * 2. 将下面的代码复制到书签的 URL 字段
 * 3. 访问 OpenClaw Control UI 页面
 * 4. 点击书签注入拦截器
 * 5. 刷新页面
 *
 * Bookmarklet 代码：
 */

// javascript:(function(){if(window.__OPENCLAW_WS_INTERCEPTOR_INSTALLED__){console.log('[OpenClaw] 拦截器已安装');return;}const t='openclaw-control-ui',o=window.WebSocket;window.WebSocket=function(e,n){console.log('[OpenClaw] 创建连接:',e);const s=new o(e,n),c=s.send.bind(s);return s.send=function(e){try{const n=JSON.parse(e);if('req'===n.type&&'connect'===n.method){const e=n.params?.client?.id;if(console.log('[OpenClaw] 原始 client.id:',e),n.params?.client){n.params.client.id=t,console.log('[OpenClaw] 修改后 client.id:',t);const e=JSON.stringify(n);return c(e)}}}catch(e){}return c(e)},s.addEventListener('open',()=>console.log('[OpenClaw] 连接已建立')),s.addEventListener('close',e=>{console.log('[OpenClaw] 连接关闭:',e.code,e.reason),1008===e.code&&console.error('[OpenClaw] 连接被拒绝 (1008):',e.reason)}),s},Object.setPrototypeOf(window.WebSocket,o),window.WebSocket.prototype=o.prototype,window.__OPENCLAW_WS_INTERCEPTOR_INSTALLED__=!0,console.log('%c[OpenClaw] 拦截器已安装','color: green; font-weight: bold'),console.log('[OpenClaw] 请刷新页面')})();
