"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

const STORAGE_KEY = "rc-privacy-ack";

export function PrivacyBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      setVisible(window.localStorage.getItem(STORAGE_KEY) !== "1");
    } catch {
      setVisible(true);
    }
  }, []);

  if (!visible) {
    return null;
  }

  return (
    <div className="mb-2 rounded-xl border border-sky-100 bg-sky-50 px-3 py-2 text-xs text-slate-700">
      Chat stays in this browser. We do not store conversation bodies; logs omit
      question text.{" "}
      <Link href="/privacy" className="underline">
        Privacy
      </Link>
      <button
        type="button"
        className="ml-3 font-medium text-sky-800 underline"
        onClick={() => {
          try {
            window.localStorage.setItem(STORAGE_KEY, "1");
          } catch {
            /* ignore */
          }
          setVisible(false);
        }}
      >
        Got it
      </button>
    </div>
  );
}
