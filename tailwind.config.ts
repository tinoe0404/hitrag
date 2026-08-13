import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        hit: {
          blue: "#0B2E5C",
          "blue-dark": "#071D3D",
          amber: "#E8A33D",
          bg: "#F7F8FA",
          surface: "#FFFFFF",
          border: "#DDE3EA",
          "text-primary": "#16202B",
          "text-secondary": "#5B6B7A",
          success: "#2F7D5E",
          warning: "#B5482D",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "sans-serif"],
        body: ["var(--font-body)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
