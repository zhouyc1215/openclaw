# Weather Tool 最终修复

## 问题根源

经过深入分析,发现了两个关键问题:

### 1. 城市名称识别问题 ✅ 已修复

**问题**: Agent 传入中文城市名 `"西安"`,但工具只识别拼音 `xian`

**原因**: 
- 工具的 `CITY_COORDINATES` 映射表只包含拼音键
- `parseLocation` 函数虽然移除了引号,但移除后是中文 `西安`,仍然无法匹配

**解决方案**: 在映射表中添加中文城市名作为键
```typescript
const CITY_COORDINATES: Record<string, { lat: number; lon: number; name: string }> = {
  // 拼音
  beijing: { lat: 39.9042, lon: 116.4074, name: "北京" },
  xian: { lat: 34.34, lon: 108.93, name: "西安" },
  // ... 其他城市
  
  // 中文别名
  "北京": { lat: 39.9042, lon: 116.4074, name: "北京" },
  "西安": { lat: 34.34, lon: 108.93, name: "西安" },
  // ... 其他城市
};
```

### 2. 网络请求失败 (IPv6 超时) ✅ 已修复

**问题**: `fetch failed` - Node.js fetch 和 https 模块都失败

**诊断过程**:
1. ✅ curl 可以访问 API - 排除 API 问题
2. ✅ DNS 解析正常 - 排除 DNS 问题
3. ✅ telnet 可以连接 443 端口 - 排除防火墙问题
4. ❌ Node.js fetch 失败 - Node.js 特定问题
5. ❌ Node.js https 模块超时 - 网络层问题
6. ✅ curl -4 (强制 IPv4) 成功 - **找到根源!**

**根本原因**: 
- Open-Meteo API 同时返回 IPv4 和 IPv6 地址
- Node.js 默认优先尝试 IPv6
- 当前网络环境的 IPv6 连接超时
- curl 默认行为不同,或者网络配置不同

**解决方案**: 
1. 使用 `https` 模块替代 `fetch` (更好的控制)
2. 强制使用 IPv4: `family: 4`

```typescript
const req = https.get(
  url.toString(),
  {
    headers: {
      Accept: "application/json",
      "User-Agent": "Clawdbot Weather Tool",
    },
    family: 4, // 强制 IPv4
  },
  (res) => {
    // ... 处理响应
  },
);
```

## 验证测试

### 测试 1: 强制 IPv4 的 https 请求
```bash
node -e "
const https = require('https');
https.get('https://api.open-meteo.com/v1/forecast?latitude=34.34&longitude=108.93&current_weather=true', 
  { family: 4 }, 
  (res) => {
    let data = '';
    res.on('data', chunk => data += chunk);
    res.on('end', () => console.log('Success! Status:', res.statusCode));
  }
).on('error', err => console.error('Error:', err.message));
"
```
**结果**: ✅ Success! Status: 200

### 测试 2: 中文城市名解析
```javascript
const normalized = '"西安"'.trim().toLowerCase().replace(/['"]/g, '');
// normalized = "西安"
CITY_COORDINATES["西安"] // 现在可以找到了
```

## 完整修复清单

1. ✅ 添加中文城市名映射
2. ✅ 改进 `parseLocation` 函数,移除引号
3. ✅ 使用 `https` 模块替代 `fetch`
4. ✅ 强制使用 IPv4 (`family: 4`)
5. ✅ 改进错误处理,提供详细错误信息
6. ✅ 添加超时控制
7. ✅ 重新编译并重启 gateway

## 现在可以工作的查询

1. **中文城市名**: "查询西安天气", "北京天气怎么样"
2. **拼音城市名**: "xian weather", "beijing forecast"
3. **坐标查询**: "34.34,108.93 的天气"
4. **多天预报**: "获取西安3天天气预报"

## 技术要点

### 为什么 curl 可以工作但 Node.js 不行?

1. **默认行为不同**:
   - curl 可能有不同的 IPv6 fallback 策略
   - Node.js fetch/https 严格按照 DNS 返回的顺序尝试

2. **超时设置不同**:
   - curl 的默认超时可能更短,更快 fallback 到 IPv4
   - Node.js 的 IPv6 超时时间较长

3. **网络栈不同**:
   - curl 使用 libcurl
   - Node.js 使用自己的网络实现

### 为什么使用 https 模块而不是 fetch?

1. **更好的控制**: 可以设置 `family: 4` 强制 IPv4
2. **更详细的错误**: 可以捕获更多网络层错误
3. **兼容性**: Node.js 内置,不依赖新特性
4. **稳定性**: https 模块更成熟,经过更多测试

## 后续优化建议

### 1. 添加 IPv6 支持检测
```typescript
// 先尝试 IPv6,失败后 fallback 到 IPv4
async function fetchWithFallback(url: string) {
  try {
    return await httpsGet(url, { family: 6 });
  } catch (error) {
    return await httpsGet(url, { family: 4 });
  }
}
```

### 2. 添加更多城市别名
```typescript
const CITY_ALIASES: Record<string, string> = {
  "西安": "xian",
  "xi'an": "xian",
  "xi an": "xian",
  "xī ān": "xian",
};
```

### 3. 添加缓存
```typescript
const weatherCache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL = 5 * 60 * 1000; // 5 分钟
```

### 4. 添加重试机制
```typescript
async function fetchWithRetry(url: string, retries = 2) {
  for (let i = 0; i < retries; i++) {
    try {
      return await httpsGet(url);
    } catch (error) {
      if (i === retries - 1) throw error;
      await sleep(1000 * (i + 1)); // 指数退避
    }
  }
}
```

## 总结

问题的根本原因是:
1. **城市名映射不完整** - 缺少中文城市名
2. **IPv6 网络超时** - Node.js 默认优先 IPv6,但当前环境 IPv6 不可用

解决方案:
1. **添加中文城市名映射** - 支持中文查询
2. **强制使用 IPv4** - 避免 IPv6 超时

现在 weather 工具应该可以正常工作了!
