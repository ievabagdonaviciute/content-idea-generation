import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f4f5ff",
          100: "#e8eaff",
          200: "#c9ceff",
          300: "#a3aaff",
          400: "#7c7ff5",
          500: "#5f5de0",
          600: "#4a45c2",
          700: "#3a369a",
          800: "#2b2872",
          900: "#1d1b4f",
        },
      },
    },
  },
  plugins: [],
};

export default config;
