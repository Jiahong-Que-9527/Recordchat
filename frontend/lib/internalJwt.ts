import { createHmac, randomUUID } from "crypto";

const ISS = "recordchat-bff";
const AUD = "recordchat-backend";

function b64url(input: string | Buffer): string {
  const buf = typeof input === "string" ? Buffer.from(input) : input;
  return buf.toString("base64url");
}

export function signInternalJwt(params: {
  sub: string;
  emailHash?: string;
  secret: string;
  ttlSeconds?: number;
}): string {
  const now = Math.floor(Date.now() / 1000);
  const ttl = params.ttlSeconds ?? 90;
  const header = b64url(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const payload = b64url(
    JSON.stringify({
      iss: ISS,
      aud: AUD,
      sub: params.sub,
      email_hash: params.emailHash ?? "",
      iat: now,
      exp: now + ttl,
      jti: randomUUID(),
    })
  );
  const sig = createHmac("sha256", params.secret)
    .update(`${header}.${payload}`)
    .digest("base64url");
  return `${header}.${payload}.${sig}`;
}
