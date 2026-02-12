import { Type } from "@sinclair/typebox";
import https from "node:https";

import type { ClawdbotConfig } from "../../config/config.js";
import { assertPublicHostname } from "../../infra/net/ssrf.js";
import type { AnyAgentTool } from "./common.js";
import { jsonResult, readNumberParam, readStringParam } from "./common.js";
import { withTimeout } from "./web-shared.js";

const DEFAULT_TIMEOUT_SECONDS = 30;
const OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast";

// 主要城市坐标映射
const CITY_COORDINATES: Record<string, { lat: number; lon: number; name: string }> = {
  beijing: { lat: 39.9042, lon: 116.4074, name: "北京" },
  shanghai: { lat: 31.2304, lon: 121.4737, name: "上海" },
  guangzhou: { lat: 23.1291, lon: 113.2644, name: "广州" },
  shenzhen: { lat: 22.5431, lon: 114.0579, name: "深圳" },
  chengdu: { lat: 30.5728, lon: 104.0668, name: "成都" },
  hangzhou: { lat: 30.2741, lon: 120.1551, name: "杭州" },
  wuhan: { lat: 30.5928, lon: 114.3055, name: "武汉" },
  xian: { lat: 34.34, lon: 108.93, name: "西安" },
  chongqing: { lat: 29.4316, lon: 106.9123, name: "重庆" },
  tianjin: { lat: 39.3434, lon: 117.3616, name: "天津" },
  nanjing: { lat: 32.0603, lon: 118.7969, name: "南京" },
  suzhou: { lat: 31.2989, lon: 120.5853, name: "苏州" },
  // 中文别名
  "北京": { lat: 39.9042, lon: 116.4074, name: "北京" },
  "上海": { lat: 31.2304, lon: 121.4737, name: "上海" },
  "广州": { lat: 23.1291, lon: 113.2644, name: "广州" },
  "深圳": { lat: 22.5431, lon: 114.0579, name: "深圳" },
  "成都": { lat: 30.5728, lon: 104.0668, name: "成都" },
  "杭州": { lat: 30.2741, lon: 120.1551, name: "杭州" },
  "武汉": { lat: 30.5928, lon: 114.3055, name: "武汉" },
  "西安": { lat: 34.34, lon: 108.93, name: "西安" },
  "重庆": { lat: 29.4316, lon: 106.9123, name: "重庆" },
  "天津": { lat: 39.3434, lon: 117.3616, name: "天津" },
  "南京": { lat: 32.0603, lon: 118.7969, name: "南京" },
  "苏州": { lat: 31.2989, lon: 120.5853, name: "苏州" },
};

const WeatherSchema = Type.Object({
  location: Type.String({
    description:
      "Location to get weather for. Can be a city name (e.g., 'beijing', 'shanghai') or coordinates in format 'lat,lon' (e.g., '39.9,116.4')",
  }),
  units: Type.Optional(
    Type.String({
      description: "Temperature units: 'celsius' or 'fahrenheit'. Default: celsius",
      default: "celsius",
    }),
  ),
  forecast_days: Type.Optional(
    Type.Number({
      description: "Number of forecast days (1-16). Default: 1",
      minimum: 1,
      maximum: 16,
      default: 1,
    }),
  ),
});

type WeatherConfig =
  | {
      enabled?: boolean;
      timeoutSeconds?: number;
    }
  | undefined;

function resolveWeatherConfig(cfg?: ClawdbotConfig): WeatherConfig {
  const weather = cfg?.tools?.weather;
  if (!weather || typeof weather !== "object") return undefined;
  return weather as WeatherConfig;
}

function resolveWeatherEnabled(params: {
  weather?: WeatherConfig;
  sandboxed?: boolean;
}): boolean {
  if (typeof params.weather?.enabled === "boolean") return params.weather.enabled;
  return true;
}

function resolveTimeoutSeconds(value: unknown, fallback: number): number {
  const parsed = typeof value === "number" && Number.isFinite(value) ? value : fallback;
  return Math.max(1, Math.floor(parsed));
}

function parseLocation(location: string): { lat: number; lon: number; name?: string } {
  const trimmed = location.trim().toLowerCase();
  
  // Remove quotes and apostrophes for better matching
  const normalized = trimmed.replace(/['"]/g, '');

  // Check if it's a known city
  if (CITY_COORDINATES[normalized]) {
    return CITY_COORDINATES[normalized];
  }

  // Try to parse as coordinates (lat,lon)
  const coordMatch = normalized.match(/^(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)$/);
  if (coordMatch) {
    const lat = parseFloat(coordMatch[1]);
    const lon = parseFloat(coordMatch[2]);
    if (lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {
      return { lat, lon };
    }
  }

  throw new Error(
    `Invalid location: "${location}". Use a city name (beijing, shanghai, etc.) or coordinates (lat,lon)`,
  );
}

function formatWeatherCode(code: number): string {
  const codes: Record<number, string> = {
    0: "晴天 (Clear sky)",
    1: "基本晴朗 (Mainly clear)",
    2: "部分多云 (Partly cloudy)",
    3: "阴天 (Overcast)",
    45: "雾 (Fog)",
    48: "雾凇 (Depositing rime fog)",
    51: "小毛毛雨 (Light drizzle)",
    53: "中等毛毛雨 (Moderate drizzle)",
    55: "大毛毛雨 (Dense drizzle)",
    61: "小雨 (Slight rain)",
    63: "中雨 (Moderate rain)",
    65: "大雨 (Heavy rain)",
    71: "小雪 (Slight snow)",
    73: "中雪 (Moderate snow)",
    75: "大雪 (Heavy snow)",
    77: "雪粒 (Snow grains)",
    80: "小阵雨 (Slight rain showers)",
    81: "中等阵雨 (Moderate rain showers)",
    82: "强阵雨 (Violent rain showers)",
    85: "小阵雪 (Slight snow showers)",
    86: "大阵雪 (Heavy snow showers)",
    95: "雷暴 (Thunderstorm)",
    96: "雷暴伴小冰雹 (Thunderstorm with slight hail)",
    99: "雷暴伴大冰雹 (Thunderstorm with heavy hail)",
  };
  return codes[code] || `天气代码 ${code}`;
}

async function fetchWeather(params: {
  lat: number;
  lon: number;
  units: string;
  forecastDays: number;
  timeoutSeconds: number;
}): Promise<Record<string, unknown>> {
  const url = new URL(OPEN_METEO_BASE_URL);
  url.searchParams.set("latitude", params.lat.toString());
  url.searchParams.set("longitude", params.lon.toString());
  url.searchParams.set("current_weather", "true");
  url.searchParams.set(
    "hourly",
    "temperature_2m,relativehumidity_2m,windspeed_10m,weathercode",
  );
  url.searchParams.set("forecast_days", params.forecastDays.toString());
  url.searchParams.set("timezone", "auto");

  if (params.units === "fahrenheit") {
    url.searchParams.set("temperature_unit", "fahrenheit");
    url.searchParams.set("windspeed_unit", "mph");
  }

  await assertPublicHostname(url.hostname);

  // Use https module instead of fetch due to Node.js fetch issues
  // Force IPv4 to avoid IPv6 timeout issues
  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      reject(new Error(`Request timeout after ${params.timeoutSeconds}s. URL: ${url.toString()}`));
    }, params.timeoutSeconds * 1000);

    const req = https.get(
      url.toString(),
      {
        headers: {
          Accept: "application/json",
          "User-Agent": "Clawdbot Weather Tool",
        },
        family: 4, // Force IPv4
      },
      (res) => {
        clearTimeout(timeoutId);

        if (res.statusCode !== 200) {
          let errorData = "";
          res.on("data", (chunk) => (errorData += chunk));
          res.on("end", () => {
            reject(
              new Error(
                `Weather API returned ${res.statusCode}: ${errorData || res.statusMessage}. URL: ${url.toString()}`,
              ),
            );
          });
          return;
        }

        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          try {
            const parsed = JSON.parse(data) as {
              current_weather?: {
                temperature?: number;
                windspeed?: number;
                winddirection?: number;
                weathercode?: number;
                time?: string;
              };
              hourly?: {
                time?: string[];
                temperature_2m?: number[];
                relativehumidity_2m?: number[];
                windspeed_10m?: number[];
                weathercode?: number[];
              };
              latitude?: number;
              longitude?: number;
              timezone?: string;
            };
            resolve(parsed);
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            reject(new Error(`Failed to parse JSON response: ${errorMessage}`));
          }
        });
      },
    );

    req.on("error", (error) => {
      clearTimeout(timeoutId);
      reject(new Error(`Weather API request failed: ${error.message}. URL: ${url.toString()}`));
    });

    req.end();
  });
}

function formatWeatherResponse(params: {
  data: Record<string, unknown>;
  location: string;
  locationName?: string;
  units: string;
}): Record<string, unknown> {
  const current = params.data.current_weather as
    | {
        temperature?: number;
        windspeed?: number;
        winddirection?: number;
        weathercode?: number;
        time?: string;
      }
    | undefined;

  const hourly = params.data.hourly as
    | {
        time?: string[];
        temperature_2m?: number[];
        relativehumidity_2m?: number[];
        windspeed_10m?: number[];
        weathercode?: number[];
      }
    | undefined;

  const tempUnit = params.units === "fahrenheit" ? "°F" : "°C";
  const windUnit = params.units === "fahrenheit" ? "mph" : "km/h";

  const result: Record<string, unknown> = {
    location: params.locationName || params.location,
    latitude: params.data.latitude,
    longitude: params.data.longitude,
    timezone: params.data.timezone,
    units: params.units,
  };

  if (current) {
    result.current = {
      time: current.time,
      temperature: `${current.temperature}${tempUnit}`,
      windspeed: `${current.windspeed} ${windUnit}`,
      winddirection: `${current.winddirection}°`,
      weather: formatWeatherCode(current.weathercode ?? 0),
      weathercode: current.weathercode,
    };
  }

  if (hourly?.time && hourly.time.length > 0) {
    const forecastHours = Math.min(24, hourly.time.length);
    const forecast = [];
    for (let i = 0; i < forecastHours; i++) {
      forecast.push({
        time: hourly.time[i],
        temperature: `${hourly.temperature_2m?.[i]}${tempUnit}`,
        humidity: `${hourly.relativehumidity_2m?.[i]}%`,
        windspeed: `${hourly.windspeed_10m?.[i]} ${windUnit}`,
        weather: formatWeatherCode(hourly.weathercode?.[i] ?? 0),
      });
    }
    result.forecast = forecast;
  }

  return result;
}

export function createWeatherTool(options?: {
  config?: ClawdbotConfig;
  sandboxed?: boolean;
}): AnyAgentTool | null {
  const weather = resolveWeatherConfig(options?.config);
  if (!resolveWeatherEnabled({ weather, sandboxed: options?.sandboxed })) return null;

  return {
    label: "Weather",
    name: "weather",
    description:
      "Get current weather and forecast for a location using Open-Meteo API. Supports major Chinese cities by name or any location by coordinates.",
    parameters: WeatherSchema,
    execute: async (_toolCallId, args) => {
      const params = args as Record<string, unknown>;
      const locationInput = readStringParam(params, "location", { required: true });
      const units = readStringParam(params, "units") === "fahrenheit" ? "fahrenheit" : "celsius";
      const forecastDays = readNumberParam(params, "forecast_days", { integer: true }) ?? 1;

      const location = parseLocation(locationInput);
      const timeoutSeconds = resolveTimeoutSeconds(
        weather?.timeoutSeconds,
        DEFAULT_TIMEOUT_SECONDS,
      );

      const data = await fetchWeather({
        lat: location.lat,
        lon: location.lon,
        units,
        forecastDays: Math.max(1, Math.min(16, forecastDays)),
        timeoutSeconds,
      });

      const formatted = formatWeatherResponse({
        data,
        location: locationInput,
        locationName: location.name,
        units,
      });

      return jsonResult(formatted);
    },
  };
}
