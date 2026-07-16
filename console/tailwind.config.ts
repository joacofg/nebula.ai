import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-fira-sans)", "sans-serif"],
        mono: ["var(--font-fira-code)", "ui-monospace", "monospace"],
      },
      colors: {
        panel: "rgb(var(--color-panel) / <alpha-value>)",
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        text: "rgb(var(--color-text) / <alpha-value>)",
        accent: "rgb(var(--color-accent) / <alpha-value>)",
        accentStrong: "rgb(var(--color-accent-strong) / <alpha-value>)",
        border: "rgb(var(--color-border) / <alpha-value>)",
      },
      boxShadow: {
        panel: "0 4px 20px rgba(2, 6, 23, 0.07)",
      },
    },
  },
  plugins: [],
};

export default config;
