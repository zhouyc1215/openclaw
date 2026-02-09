# 飞书插件配置测试

## 测试命令
```bash
pnpm clawdbot configure
```

## 预期结果
在频道选择列表中应该看到飞书（Feishu）选项

## 修改内容
修改了 `src/cli/program/command-registry.ts`，为 configure 命令添加了 `loadPlugins: true` 路由配置。

这样在运行 configure 命令时，插件注册表会被加载，飞书插件就能被识别并显示在频道列表中。
