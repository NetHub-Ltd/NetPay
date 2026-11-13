import { handlers } from "../../../../auth";

/** Node runtime so PKCE cookies encrypt/decrypt consistently (not Edge). */
export const runtime = "nodejs";

export const { GET, POST } = handlers;
