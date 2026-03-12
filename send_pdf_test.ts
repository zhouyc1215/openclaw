import { sendMessage } from "./src/infra/outbound/message.js";

async function main() {
  const cfg = {
    channels: {
      feishu: {
        enabled: true,
        appId: "cli_a90d40fc70b89bc2",
        appSecret: "jEFgKlvjq5c0aYRuh7YaecohSuV7IPUF",
        domain: "feishu",
      },
    },
  } as any;

  await sendMessage({
    cfg,
    channel: "feishu",
    to: "ou_b3afb7d2133e4d689be523fc48f3d2b3",
    content: "PDF文件已生成",
    mediaUrl:
      "file:///home/tsl/.openclaw/media/outbound/SONIC_PROTOCOL_SECURITY_COMPREHENSIVE_ANALYSIS---dd05e1bf-523f-47b2-8a6b-3efbeccff203.pdf",
  });
  console.log("发送成功");
}

main().catch(console.error);
