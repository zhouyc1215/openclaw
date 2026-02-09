# 飞书插件安装和验证报告

## 安装时间
2026-02-08 20:50

## 插件信息
- **名称**: @m1heng-clawd/feishu
- **版本**: 0.1.7
- **来源**: https://github.com/m1heng/clawdbot-feishu
- **描述**: OpenClaw Feishu/Lark (飞书) channel plugin

---

## 安装过程

### 1. 遇到的问题

#### 问题1：插件格式不兼容
**错误信息**:
```
Error: package.json missing clawdbot.extensions
```

**原因**: 插件使用新的 `openclaw.extensions` 格式，但代码库还在检查旧的 `clawdbot.extensions`

**解决方案**: 修改 `src/plugins/install.ts`，支持两种格式：
```typescript
type PackageManifest = {
  clawdbot?: { extensions?: string[] };
  openclaw?: { extensions?: string[] };  // 新增
};

async function ensureClawdbotExtensions(manifest: PackageManifest) {
  // 优先使用 openclaw.extensions，回退到 clawdbot.extensions
  const extensions = manifest.openclaw?.extensions ?? manifest.clawdbot?.extensions;
  // ...
}
```

#### 问题2：找不到插件清单文件
**错误信息**:
```
plugin manifest not found: /home/tsl/.clawdbot/extensions/feishu/clawdbot.plugin.json
```

**原因**: 插件使用 `openclaw.plugin.json`，但代码在找 `clawdbot.plugin.json`

**解决方案**: 修改 `src/plugins/manifest.ts`，支持两种文件名：
```typescript
export const PLUGIN_MANIFEST_FILENAME = "clawdbot.plugin.json";
export const PLUGIN_MANIFEST_FILENAME_NEW = "openclaw.plugin.json";

export function resolvePluginManifestPath(rootDir: string): string {
  // 优先尝试新文件名，回退到旧文件名
  const newPath = path.join(rootDir, PLUGIN_MANIFEST_FILENAME_NEW);
  if (fs.existsSync(newPath)) {
    return newPath;
  }
  return path.join(rootDir, PLUGIN_MANIFEST_FILENAME);
}
```

#### 问题3：找不到 openclaw/plugin-sdk 模块
**错误信息**:
```
Error: Cannot find module 'openclaw/plugin-sdk'
```

**原因**: 插件导入 `openclaw/plugin-sdk`，但 jiti 别名只配置了 `clawdbot/plugin-sdk`

**解决方案**: 修改 `src/plugins/loader.ts`，添加新别名：
```typescript
const jiti = createJiti(import.meta.url, {
  interopDefault: true,
  extensions: [".ts", ".tsx", ".mts", ".cts", ".mtsx", ".ctsx", ".js", ".mjs", ".cjs", ".json"],
  ...(pluginSdkAlias
    ? {
        alias: {
          "clawdbot/plugin-sdk": pluginSdkAlias,
          "openclaw/plugin-sdk": pluginSdkAlias,  // 新增
        },
      }
    : {}),
});
```

---

### 2. 修改的文件

1. **src/plugins/install.ts**
   - 添加 `openclaw.extensions` 支持
   - 修改类型定义和验证逻辑

2. **src/plugins/manifest.ts**
   - 添加 `PLUGIN_MANIFEST_FILENAME_NEW` 常量
   - 修改 `resolvePluginManifestPath` 函数支持两种文件名
   - 添加 `openclaw` 类型定义

3. **src/plugins/loader.ts**
   - 添加 `openclaw/plugin-sdk` 别名

---

## 安装命令

```bash
# 安装插件
pnpm clawdbot plugins install @m1heng-clawd/feishu

# 验证安装
pnpm clawdbot plugins list | grep feishu
```

---

## 验证结果

### 插件状态
```
│ Feishu       │ feishu   │ loaded   │ ~/.clawdbot/extensions/feishu/index.ts  │ 0.1.7     │
│              │          │          │ Feishu/Lark channel plugin              │           │
```

✅ **状态**: loaded（已加载）
✅ **版本**: 0.1.7
✅ **位置**: ~/.clawdbot/extensions/feishu/

---

## 插件功能

根据文档，该插件提供以下功能：

### 1. 连接模式
- WebSocket（推荐）
- Webhook

### 2. 消息功能
- 私聊和群聊
- 消息回复和引用
- 图片和文件上传/下载
- 富文本支持
- 输入指示器
- @mention 转发

### 3. 工具集成
- **文档工具** (feishu_doc): 读取、创建、编辑飞书文档
- **知识库工具** (feishu_wiki): 浏览、搜索、管理知识库
- **云空间工具** (feishu_drive): 文件夹管理、文件操作
- **多维表格工具** (feishu_bitable): 读写多维表格数据

### 4. 高级功能
- 动态 Agent 创建（多用户隔离）
- 卡片渲染模式（Markdown 语法高亮）
- 权限错误自动提示

---

## 配置示例

### 基础配置
```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "cli_xxxxx",
      "appSecret": "your_app_secret",
      "domain": "feishu",
      "connectionMode": "websocket",
      "dmPolicy": "pairing",
      "groupPolicy": "allowlist",
      "requireMention": true,
      "mediaMaxMb": 30,
      "renderMode": "auto"
    }
  }
}
```

### 配置命令
```bash
# 设置 App ID
pnpm clawdbot config set channels.feishu.appId "cli_xxxxx"

# 设置 App Secret
pnpm clawdbot config set channels.feishu.appSecret "your_secret"

# 启用插件
pnpm clawdbot config set channels.feishu.enabled true
```

---

## 使用前准备

### 1. 创建飞书应用
1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建自建应用
3. 获取 App ID 和 App Secret

### 2. 配置权限

#### 必需权限
- `im:message` - 发送和接收消息
- `im:message.p2p_msg:readonly` - 读取私聊消息
- `im:message.group_at_msg:readonly` - 接收群内 @消息
- `im:message:send_as_bot` - 以机器人身份发送
- `im:resource` - 上传下载媒体文件

#### 工具权限（可选）
- `docx:document:readonly` - 读取文档
- `drive:drive:readonly` - 访问云空间
- `wiki:wiki:readonly` - 访问知识库
- `bitable:app:readonly` - 读取多维表格

### 3. 配置事件订阅 ⚠️ 重要
1. 进入应用后台 → 事件与回调
2. 选择 **长连接** 模式
3. 添加事件：
   - `im.message.receive_v1` - 接收消息（必需）
   - `im.message.message_read_v1` - 消息已读
   - `im.chat.member.bot.added_v1` - 机器人进群
   - `im.chat.member.bot.deleted_v1` - 机器人被移出

### 4. 资源访问权限
- **云空间**: 需要将文件夹分享给机器人
- **知识库**: 需要将机器人添加为知识库成员
- **多维表格**: 需要将表格分享给机器人

---

## 测试建议

### 1. 基础测试
```bash
# 查看插件状态
pnpm clawdbot plugins list

# 查看配置
pnpm clawdbot config get channels.feishu

# 启动网关（如果配置了飞书）
pnpm clawdbot gateway run
```

### 2. 功能测试
1. 私聊测试：向机器人发送消息
2. 群聊测试：在群里 @机器人
3. 文件测试：发送图片/文件
4. 工具测试：使用文档/知识库/云空间工具

---

## 注意事项

1. **兼容性**: 此插件需要修改后的代码库才能正常工作（已完成修改）
2. **权限**: 确保飞书应用有足够的权限
3. **事件订阅**: 必须配置长连接模式的事件订阅
4. **资源访问**: 需要手动分享资源给机器人
5. **网关模式**: 需要配置 `gateway.mode=local` 并启动网关

---

## 后续步骤

1. ✅ 插件已成功安装并加载
2. ⏳ 需要配置飞书应用（App ID、App Secret）
3. ⏳ 需要配置权限和事件订阅
4. ⏳ 需要启动网关进行实际测试

---

## 相关资源

- **插件仓库**: https://github.com/m1heng/clawdbot-feishu
- **飞书开放平台**: https://open.feishu.cn/
- **文档**: 插件 README.md 包含详细的配置说明
- **Wiki**: 中文社区资料和常见问题

---

## 总结

✅ **安装成功**: 飞书插件已成功安装并加载
✅ **代码修改**: 完成了对 openclaw 命名的兼容性支持
✅ **功能完整**: 插件提供了完整的飞书集成功能

**下一步**: 配置飞书应用并进行实际测试。
