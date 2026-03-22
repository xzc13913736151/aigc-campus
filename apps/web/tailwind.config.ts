import type { Config } from "tailwindcss";


const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#f7f1e8",
        ink: "#102133",
        coral: "#f16b4f",
        moss: "#557c55",
        gold: "#d8a44b",
        shell: "#fff9f2",
        line: "#d8c9b6",
      },
      borderRadius: {
        xl2: "1.5rem",
      },
      boxShadow: {
        card: "0 18px 48px rgba(16, 33, 51, 0.10)",
      },
      fontFamily: {
        sans: ["Space Grotesk", "Avenir Next", "Helvetica Neue", "sans-serif"],
        serif: ["Source Serif 4", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
};


export default config;
