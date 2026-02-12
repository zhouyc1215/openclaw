---
name: weather
description: Get current weather and forecasts using the weather tool (powered by Open-Meteo API, no API key required).
homepage: https://open-meteo.com/en/docs
metadata: {"clawdbot":{"emoji":"🌤️"}}
---

# Weather

Use the `weather` tool to get current weather and forecasts. No API keys needed.

## Quick Start

Query weather by city name or coordinates:

```json
{
  "location": "beijing",
  "units": "celsius",
  "forecast_days": 1
}
```

## Supported Cities

Major Chinese cities can be queried by name (pinyin):

| 城市 | City Name | Latitude | Longitude |
|------|-----------|----------|-----------|
| 北京 | beijing | 39.9042 | 116.4074 |
| 上海 | shanghai | 31.2304 | 121.4737 |
| 广州 | guangzhou | 23.1291 | 113.2644 |
| 深圳 | shenzhen | 22.5431 | 114.0579 |
| 成都 | chengdu | 30.5728 | 104.0668 |
| 杭州 | hangzhou | 30.2741 | 120.1551 |
| 西安 | xian | 34.34 | 108.93 |
| 武汉 | wuhan | 30.5928 | 114.3055 |
| 南京 | nanjing | 32.0603 | 118.7969 |
| 重庆 | chongqing | 29.4316 | 106.9123 |
| 天津 | tianjin | 39.3434 | 117.3616 |
| 苏州 | suzhou | 31.2989 | 120.5853 |

## Using Coordinates

For locations not in the list, use coordinates:

```json
{
  "location": "33.07,107.02",
  "units": "celsius"
}
```

## Parameters

- `location` (required): City name (e.g., "beijing") or coordinates (e.g., "39.9,116.4")
- `units` (optional): "celsius" (default) or "fahrenheit"
- `forecast_days` (optional): Number of forecast days (1-16, default: 1)

## Response Format

The tool returns:
- `current`: Current weather conditions
  - `temperature`: Temperature with unit
  - `windspeed`: Wind speed with unit
  - `winddirection`: Wind direction in degrees
  - `weather`: Human-readable weather description (Chinese + English)
  - `time`: Current time
- `forecast`: Array of hourly forecasts (up to 24 hours)
  - `time`: Forecast time
  - `temperature`: Temperature with unit
  - `humidity`: Relative humidity percentage
  - `windspeed`: Wind speed with unit
  - `weather`: Weather description

## Weather Descriptions

The tool automatically translates weather codes to Chinese and English:

- 晴天 (Clear sky)
- 基本晴朗 (Mainly clear)
- 部分多云 (Partly cloudy)
- 阴天 (Overcast)
- 雾 (Fog)
- 小雨/中雨/大雨 (Light/Moderate/Heavy rain)
- 小雪/中雪/大雪 (Light/Moderate/Heavy snow)
- 雷暴 (Thunderstorm)
- And more...

## Example Usage

When user asks "查询西安天气" or "What's the weather in Xi'an":

1. Call the weather tool:
   ```json
   {
     "location": "xian",
     "units": "celsius",
     "forecast_days": 1
   }
   ```

2. The tool returns structured data with current weather and hourly forecast

3. Format the response in a user-friendly way

## Tips

- City names are case-insensitive
- Coordinates must be in "lat,lon" format
- Temperature is in Celsius by default
- Wind speed is in km/h (or mph for Fahrenheit)
- Forecast includes up to 24 hours of hourly data
