// Defaults for agent metadata when upstream does not supply them.
// Model id uses MiniMax M2.1 via Anthropic-compatible API.
export const DEFAULT_PROVIDER = "minimax";
export const DEFAULT_MODEL = "MiniMax-M2.1";
// Context window: MiniMax M2.1 supports 200k tokens.
export const DEFAULT_CONTEXT_TOKENS = 200_000;
