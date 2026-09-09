import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        // System-first stack; no external font fetch at build/runtime.
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "Noto Sans",
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "Liberation Mono",
          "Courier New",
          "monospace",
        ],
      },
      colors: {
        // Single accent source — derived from recordchat_icon.png:
        // vivid azure #0b65fe with its light-blue tints (see AUD icon palette).
        accent: {
          DEFAULT: "#0b65fe", // icon accent azure
          hover: "#0a52e0", // darker azure
          weak: "#e6f1fd", // icon light-blue tint
          soft: "#d4e7fd", // icon mid tint
          ring: "#bad9fc", // icon pale azure
          fg: "#ffffff",
        },
        // Azure pairing for the brand gradient (light azure -> deep azure).
        brand: {
          light: "#1479ff",
          DEFAULT: "#0b65fe",
          deep: "#0b4efd",
        },
      },
      boxShadow: {
        // Three restrained elevation steps + an accent glow for focus moments.
        "rc-sm": "0 1px 2px rgba(15, 23, 42, 0.04), 0 1px 1px rgba(15, 23, 42, 0.03)",
        "rc-md": "0 4px 16px rgba(15, 23, 42, 0.06)",
        "rc-lg": "0 8px 32px rgba(15, 23, 42, 0.10)",
        "rc-glow": "0 6px 24px rgba(11, 101, 254, 0.24), 0 2px 8px rgba(11, 78, 253, 0.12)",
        "rc-icon":
          "0 10px 36px rgba(11, 101, 254, 0.28), 0 4px 12px rgba(20, 121, 255, 0.16), 0 0 0 1px rgba(255, 255, 255, 0.5)",
      },
      keyframes: {
        // Soft pulse for status labels (e.g. "Thinking…").
        "rc-pulse-soft": {
          "0%, 100%": { opacity: "0.55" },
          "50%": { opacity: "1" },
        },
        // Gradient shimmer for the brand/hero text.
        "rc-shimmer": {
          "0%": { backgroundPosition: "0% 50%" },
          "100%": { backgroundPosition: "200% 50%" },
        },
        // Gentle float for the empty-state brand mark.
        "rc-float": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-5px)" },
        },
      },
      animation: {
        "rc-pulse-soft": "rc-pulse-soft 1.6s ease-in-out infinite",
        "rc-shimmer": "rc-shimmer 3s linear infinite",
        "rc-float": "rc-float 5s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
