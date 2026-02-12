// Defaults for agent metadata when upstream does not supply them.
// Model id uses pi-ai's built-in Google Gemini catalog.
export const DEFAULT_PROVIDER = "google";
export const DEFAULT_MODEL = "gemini-2.5-flash";
// Context window: Gemini 2.5 Flash supports ~1M tokens.
export const DEFAULT_CONTEXT_TOKENS = 1_000_000;
