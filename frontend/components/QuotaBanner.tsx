"use client";

import { useEffect, useState } from "react";

type Me = {
  plan?: string;
  quota?: number;
  used_today?: number;
};

export function QuotaBanner() {
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/me", { cache: "no-store" })
      .then(async (res) => {
        if (!res.ok) {
          return null;
        }
        return (await res.json()) as Me;
      })
      .then((data) => {
        if (!cancelled && data?.quota != null) {
          setMe(data);
        }
      })
      .catch(() => {
        /* local AUTH_MODE=off */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!me || me.quota == null || me.used_today == null) {
    return null;
  }

  return (
    <p className="mb-2 text-xs text-slate-500">
      {me.plan === "trial" ? "Trial" : "Plan"}: {me.used_today} / {me.quota}{" "}
      questions today
    </p>
  );
}
