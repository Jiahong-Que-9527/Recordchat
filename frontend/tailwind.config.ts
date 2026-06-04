import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(214 32% 91%)",
        muted: "hsl(210 40% 96%)",
        accent: "hsl(221 83% 53%)",
      },
    },
  },
  plugins: [],
};

export default config;
