/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef8f3",
          100: "#d7efe3",
          200: "#aedfc8",
          300: "#7cc9a8",
          400: "#48ac87",
          500: "#2b8f6d",
          600: "#1e7359",
          700: "#195c49",
          800: "#164a3c",
          900: "#133d33",
          950: "#08251f",
        },
        brass: {
          50: "#fbf7ee",
          100: "#f5ecd6",
          200: "#ead7a8",
          300: "#dcbb72",
          400: "#cfa04b",
          500: "#bd8636",
          600: "#a36a2c",
          700: "#855126",
          800: "#6e4324",
          900: "#5d3821",
          950: "#35200f",
        },
        ink: "#12231e",
        paper: {
          DEFAULT: "#f7f5ef",
          deep: "#efeadd",
          line: "#e5dfd1",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "Segoe UI", "sans-serif"],
        display: ["var(--font-display)", "Georgia", "Cambria", "serif"],
      },
      boxShadow: {
        soft: "0 1px 2px rgba(18, 35, 30, 0.04), 0 12px 32px -18px rgba(18, 35, 30, 0.18)",
        lift: "0 2px 6px rgba(18, 35, 30, 0.05), 0 28px 60px -28px rgba(18, 35, 30, 0.35)",
        "inner-sm": "inset 0 1px 2px rgba(18, 35, 30, 0.06)",
      },
      borderRadius: {
        "4xl": "2rem",
      },
      backgroundImage: {
        "grid-dark":
          "linear-gradient(to right, rgba(255,255,255,0.055) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.055) 1px, transparent 1px)",
      },
      backgroundSize: {
        "grid-dark": "32px 32px",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.55s cubic-bezier(0.22, 1, 0.36, 1) both",
        "fade-in": "fade-in 0.4s ease both",
      },
    },
  },
  plugins: [],
};
