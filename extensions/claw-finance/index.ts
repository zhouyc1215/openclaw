import type { OpenClawPluginApi } from "../../src/plugins/types.js";
import { createFinanceAskTool } from "./src/finance-ask-tool.js";

export default function register(api: OpenClawPluginApi) {
  api.registerTool(
    (ctx) => {
      // 沙箱内禁止出站 HTTP，避免绕过隔离
      if (ctx.sandboxed) {
        return null;
      }
      return createFinanceAskTool(api);
    },
    { optional: true },
  );
}
