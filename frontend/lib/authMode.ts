export function isAuthEnforced(): boolean {
  return (process.env.AUTH_MODE || "").trim().toLowerCase() === "enforced";
}
