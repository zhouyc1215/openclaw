#!/usr/bin/env node
/**
 * Playwright 自动化 SAML 登录脚本
 * 用途：自动完成 FortiClient VPN 的 Microsoft SAML 认证
 *
 * 安装依赖：
 *   npm install playwright
 *   npx playwright install chromium
 */

const { chromium } = require("playwright");

// 配置
const CONFIG = {
  vpnServer: "vpn-krgc.dasanns.com",
  username: "yuchao.zhou@dasanns.com",
  password: "Dasanzyc1215",
  timeout: 60000, // 60 秒超时
  headless: true, // 无头模式（后台运行）
};

async function autoSamlLogin() {
  console.log("[INFO] 启动 Playwright 自动登录...");

  const browser = await chromium.launch({
    headless: CONFIG.headless,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  try {
    const context = await browser.newContext({
      viewport: { width: 1280, height: 720 },
    });

    const page = await context.newPage();

    // 设置超时
    page.setDefaultTimeout(CONFIG.timeout);

    console.log("[INFO] 访问 VPN SAML 登录页面...");
    const samlUrl = `https://${CONFIG.vpnServer}/remote/saml/start`;
    await page
      .goto(samlUrl, {
        waitUntil: "domcontentloaded",
        timeout: 30000,
      })
      .catch((e) => {
        console.log("[WARN] 页面加载超时，继续...");
      });

    // 等待 Microsoft 登录页面加载
    console.log("[INFO] 等待 Microsoft 登录页面...");
    await page.waitForSelector("#i0116", { timeout: 15000 });

    // 输入用户名
    console.log("[INFO] 输入用户名...");
    await page.fill("#i0116", CONFIG.username);
    await page.click("#idSIButton9");

    // 等待密码输入框
    console.log("[INFO] 等待密码输入框...");
    await page.waitForSelector("#i0118", { timeout: 15000 });

    // 输入密码
    console.log("[INFO] 输入密码...");
    await page.fill("#i0118", CONFIG.password);
    await page.click("#idSIButton9");

    // 等待 MFA 或"保持登录"提示
    console.log("[INFO] 等待认证完成...");
    await page.waitForTimeout(5000);

    // 检查当前 URL
    console.log("[INFO] 当前 URL:", page.url());

    // 检查是否有"保持登录"选项
    const staySignedInButton = await page.$("#idSIButton9");
    if (staySignedInButton) {
      const buttonText = await staySignedInButton.textContent();
      console.log("[INFO] 找到按钮:", buttonText);
      if (buttonText && (buttonText.includes("Yes") || buttonText.includes("是"))) {
        console.log('[INFO] 点击"保持登录"...');
        await staySignedInButton.click();
        await page.waitForTimeout(3000);
      }
    }

    // 检查是否需要 MFA
    const mfaElement = await page.$(
      'div[data-value="PhoneAppNotification"], div[data-value="PhoneAppOTP"]',
    );
    if (mfaElement) {
      console.log("[WARN] 检测到 MFA 要求，需要手动完成");
      console.log("[INFO] 等待 60 秒以完成 MFA...");
      await page.waitForTimeout(60000);
    }

    // 等待重定向回 VPN（增加超时时间）
    console.log("[INFO] 等待重定向到 VPN...");
    try {
      await page.waitForURL(`*://${CONFIG.vpnServer}/*`, { timeout: 60000 });
      console.log("[SUCCESS] ✅ 已重定向到 VPN");
    } catch (error) {
      console.log("[WARN] 等待重定向超时，检查当前状态...");
      console.log("[INFO] 最终 URL:", page.url());

      // 检查是否已经在 VPN 页面
      if (page.url().includes(CONFIG.vpnServer)) {
        console.log("[SUCCESS] ✅ 已在 VPN 页面");
      } else {
        throw new Error("未能重定向到 VPN 页面", { cause: error });
      }
    }

    console.log("[SUCCESS] ✅ SAML 认证成功！");

    // 等待一会儿确保 VPN 连接建立
    await page.waitForTimeout(5000);

    return true;
  } catch (error) {
    console.error("[ERROR] ❌ 自动登录失败:", error.message);
    return false;
  } finally {
    await browser.close();
  }
}

// 主函数
(async () => {
  try {
    const success = await autoSamlLogin();
    process.exit(success ? 0 : 1);
  } catch (error) {
    console.error("[FATAL] 脚本执行失败:", error);
    process.exit(1);
  }
})();
