import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Single accent source — Tailwind blue scale, exposed semantically.
        accent: {
          DEFAULT: "#2563eb", // blue-600
          hover: "#1d4ed8", // blue-700
          weak: "#eff6ff", // blue-50
          soft: "#dbeafe", // blue-100
          ring: "#bfdbfe", // blue-200
          fg: "#ffffff",
        },
      },
      boxShadow: {
        // Two restrained elevation steps only.
        "rc-sm": "0 1px 2px rgba(15, 23, 42, 0.04), 0 1px 1px rgba(15, 23, 42, 0.03)",
        "rc-md": "0 4px 16px rgba(15, 23, 42, 0.06)",
      },
    },
  },
  plugins: [],
};

export default config;
