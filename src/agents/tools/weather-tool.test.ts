import { describe, expect, it } from "vitest";
import { createWeatherTool } from "./weather-tool.js";

describe("weather tool", () => {
  it("creates weather tool when enabled", () => {
    const tool = createWeatherTool({
      config: {
        tools: {
          weather: {
            enabled: true,
          },
        },
      } as any,
    });

    expect(tool).toBeDefined();
    expect(tool?.name).toBe("weather");
    expect(tool?.label).toBe("Weather");
  });

  it("returns null when disabled", () => {
    const tool = createWeatherTool({
      config: {
        tools: {
          weather: {
            enabled: false,
          },
        },
      } as any,
    });

    expect(tool).toBeNull();
  });

  it("is enabled by default", () => {
    const tool = createWeatherTool({
      config: {} as any,
    });

    expect(tool).toBeDefined();
  });
});
