import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        blueprint: {
          950: "#0B1F33", // deep schematic navy - base background
          900: "#0F2740",
          800: "#15324F",
          700: "#1D4066",
          line: "#2E5A85", // grid line blue
        },
        amber: {
          signal: "#E8A33D", // safety-signage amber - primary accent
          bright: "#F5C065",
        },
        paper: "#EDEAE1", // aged drawing-paper for light surfaces / cards
        ok: "#5FAE7C",
        warn: "#E8A33D",
        critical: "#D9634A",
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
        body: ["Inter", "sans-serif"],
      },
      backgroundImage: {
        "blueprint-grid":
          "linear-gradient(rgba(46,90,133,0.35) 1px, transparent 1px), linear-gradient(90deg, rgba(46,90,133,0.35) 1px, transparent 1px)",
      },
      backgroundSize: {
        grid: "32px 32px",
      },
    },
  },
  plugins: [],
};
export default config;
