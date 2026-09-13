export function isAuthEnforced(): boolean {
  return (process.env.AUTH_MODE || "").trim().toLowerCase() === "enforced";
}

export function clerkPublishableKey(): string {
  return (process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || "").trim();
}

export function hasClerkPublishableKey(): boolean {
  return clerkPublishableKey().length > 0;
}
