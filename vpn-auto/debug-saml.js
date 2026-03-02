#!/usr/bin/env node
/**
 * Playwright SAML 登录调试脚本
 * 用途：探索页面结构，找到正确的选择器
 */

const { chromium } = require("playwright");

const CONFIG = {
  vpnServer: "vpn-krgc.dasanns.com",
  username: "yuchao.zhou@dasanns.com",
  password: "Dasanzyc1215",
  timeout: 120000, // 2 分钟超时
};

async function debugSamlLogin() {
  console.log("[DEBUG] 启动浏览器...");

  const browser = await chromium.launch({
    headless: true, // 使用 headless 模式
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  try {
    const context = await browser.newContext({
      viewport: { width: 1280, height: 720 },
    });

    const page = await context.newPage();
    page.setDefaultTimeout(CONFIG.timeout);

    // 监听控制台输出
    page.on("console", (msg) => console.log("[PAGE LOG]", msg.text()));

    // 监听页面错误
    page.on("pageerror", (error) => console.error("[PAGE ERROR]", error));

    console.log("[DEBUG] 访问 VPN SAML 登录页面...");
    const samlUrl = `https://${CONFIG.vpnServer}/remote/saml/start`;

    try {
      await page.goto(samlUrl, {
        waitUntil: "domcontentloaded",
        timeout: 30000,
      });
      console.log("[DEBUG] 页面加载完成");
    } catch (error) {
      console.log("[DEBUG] 页面加载超时或失败:", error.message);
      console.log("[DEBUG] 继续尝试获取页面信息...");
    }

    console.log("[DEBUG] 当前 URL:", page.url());
    console.log("[DEBUG] 页面标题:", await page.title());

    // 等待页面加载
    console.log("[DEBUG] 等待页面动态内容加载...");
    await page.waitForTimeout(3000);

    // 截图
    await page.screenshot({ path: "vpn-auto/debug-step1.png", fullPage: true });
    console.log("[DEBUG] 截图已保存: debug-step1.png");

    // 获取页面 HTML（前 2000 字符）
    const html = await page.content();
    console.log("[DEBUG] 页面 HTML 片段:");
    console.log(html.substring(0, 2000));

    // 等待输入框出现
    console.log("[DEBUG] 等待输入框出现...");
    try {
      await page.waitForSelector("input", { timeout: 10000 });
      console.log("[DEBUG] 输入框已出现");
    } catch (error) {
      console.log("[DEBUG] 等待输入框超时");
    }

    // 查找所有输入框
    const inputs = await page.$$("input");
    console.log(`[DEBUG] 找到 ${inputs.length} 个输入框`);

    for (let i = 0; i < inputs.length; i++) {
      const input = inputs[i];
      const type = await input.getAttribute("type");
      const name = await input.getAttribute("name");
      const id = await input.getAttribute("id");
      const placeholder = await input.getAttribute("placeholder");
      console.log(
        `[DEBUG] 输入框 ${i + 1}: type="${type}", name="${name}", id="${id}", placeholder="${placeholder}"`,
      );
    }

    // 查找所有按钮
    const buttons = await page.$$('button, input[type="submit"]');
    console.log(`[DEBUG] 找到 ${buttons.length} 个按钮`);

    for (let i = 0; i < buttons.length; i++) {
      const button = buttons[i];
      const text = await button.textContent();
      const type = await button.getAttribute("type");
      const value = await button.getAttribute("value");
      console.log(
        `[DEBUG] 按钮 ${i + 1}: text="${text?.trim()}", type="${type}", value="${value}"`,
      );
    }

    console.log("\n[DEBUG] 等待 5 秒，让页面完全加载...");
    await page.waitForTimeout(5000);

    console.log("[DEBUG] 调试完成");
  } catch (error) {
    console.error("[ERROR] 调试失败:", error);
  } finally {
    await browser.close();
  }
}

// 主函数
(async () => {
  try {
    await debugSamlLogin();
  } catch (error) {
    console.error("[FATAL] 脚本执行失败:", error);
    process.exit(1);
  }
})();
