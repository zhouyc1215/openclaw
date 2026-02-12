// Defaults for agent metadata when upstream does not supply them.
<<<<<<< HEAD
// Model id uses MiniMax M2.1 via Anthropic-compatible API.
export const DEFAULT_PROVIDER = "minimax";
export const DEFAULT_MODEL = "MiniMax-M2.1";
// Context window: MiniMax M2.1 supports 200k tokens.
=======
// Model id uses pi-ai's built-in Anthropic catalog.
export const DEFAULT_PROVIDER = "anthropic";
export const DEFAULT_MODEL = "claude-opus-4-6";
// Conservative fallback used when model metadata is unavailable.
>>>>>>> 69aa3df116d38141626fcdc29fc16b5f31f08d6c
export const DEFAULT_CONTEXT_TOKENS = 200_000;
