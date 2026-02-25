import { Type } from "@sinclair/typebox";
import { SESSION_LABEL_MAX_LENGTH } from "../../../sessions/session-label.js";
import { GATEWAY_CLIENT_IDS, GATEWAY_CLIENT_MODES } from "../client-info.js";

export const NonEmptyString = Type.String({ minLength: 1 });
export const SessionLabelString = Type.String({
  minLength: 1,
  maxLength: SESSION_LABEL_MAX_LENGTH,
});

// Allow any non-empty string for client.id (relaxed validation)
// Previously: strict enum validation using GATEWAY_CLIENT_IDS
export const GatewayClientIdSchema = NonEmptyString;

export const GatewayClientModeSchema = Type.Union(
  Object.values(GATEWAY_CLIENT_MODES).map((value) => Type.Literal(value)),
);
