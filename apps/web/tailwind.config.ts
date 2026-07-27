import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#fdf2fb",
          100: "#fce8f8",
          200: "#f5cdf0",
          300: "#eba6e3",
          400: "#dd76d1",
          500: "#c34fbb",
          600: "#a334a0",
          700: "#832782",
          800: "#661f66",
          900: "#4a1749",
        },
      },
    },
  },
  plugins: [],
};

export default config;
