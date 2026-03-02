#!/usr/bin/env node
const { chromium } = require("playwright");
const fs = require("fs");

(async () => {
  const browser = await chromium.launch({ headless: true, args: ["--no-sandbox"] });
  const page = await browser.newPage();

  console.log("访问页面...");
  await page
    .goto("https://vpn-krgc.dasanns.com/remote/saml/start", {
      waitUntil: "domcontentloaded",
      timeout: 30000,
    })
    .catch((e) => console.log("goto 超时，继续..."));

  console.log("当前 URL:", page.url());

  await page.waitForTimeout(3000);

  const html = await page.content();
  fs.writeFileSync("vpn-auto/page.html", html);
  console.log("HTML 已保存到 page.html");

  await page.screenshot({ path: "vpn-auto/page.png", fullPage: true });
  console.log("截图已保存到 page.png");

  const inputs = await page.$$eval("input", (els) =>
    els.map((el) => ({
      type: el.type,
      name: el.name,
      id: el.id,
      placeholder: el.placeholder,
      visible: el.offsetParent !== null,
    })),
  );

  console.log("输入框:", JSON.stringify(inputs, null, 2));

  await browser.close();
})();
