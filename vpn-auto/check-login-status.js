#!/usr/bin/env node
const { chromium } = require("playwright");
const fs = require("fs");

(async () => {
  const browser = await chromium.launch({ headless: true, args: ["--no-sandbox"] });
  const page = await browser.newPage();

  console.log("访问 VPN SAML 页面...");
  await page
    .goto("https://vpn-krgc.dasanns.com/remote/saml/start", {
      waitUntil: "domcontentloaded",
      timeout: 30000,
    })
    .catch((e) => console.log("goto 超时"));

  console.log("等待登录页面...");
  await page.waitForSelector("#i0116", { timeout: 15000 });

  console.log("输入用户名...");
  await page.fill("#i0116", "yuchao.zhou@dasanns.com");
  await page.click("#idSIButton9");

  console.log("等待密码框...");
  await page.waitForSelector("#i0118", { timeout: 15000 });

  console.log("输入密码...");
  await page.fill("#i0118", "Dasanzyc1215");
  await page.click("#idSIButton9");

  console.log("等待 10 秒...");
  await page.waitForTimeout(10000);

  console.log("当前 URL:", page.url());
  console.log("页面标题:", await page.title());

  const html = await page.content();
  fs.writeFileSync("vpn-auto/after-login.html", html);
  console.log("HTML 已保存");

  await page.screenshot({ path: "vpn-auto/after-login.png", fullPage: true });
  console.log("截图已保存");

  // 查找错误消息
  const errorMsg = await page.$eval("#passwordError", (el) => el.textContent).catch(() => null);
  if (errorMsg) {
    console.log("错误消息:", errorMsg);
  }

  await browser.close();
})();
