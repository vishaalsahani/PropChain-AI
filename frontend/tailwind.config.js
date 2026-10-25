/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#000000",
        paper: {
          DEFAULT: "#ffffff",
          deep: "#f2f2f2",
          line: "#cfcfcf",
        },
        secondary: "#4d4d4d",
        quiet: "#cfcfcf",
        "quiet-inverted": "#3d3d3d",
      },
      fontFamily: {
        display: [
          "var(--font-eb-garamond)",
          "EB Garamond",
          "Garamond",
          "Georgia",
          "serif",
        ],
        text: [
          "var(--font-source-serif)",
          "Source Serif 4",
          "Iowan Old Style",
          "Georgia",
          "serif",
        ],
        sans: [
          "var(--font-source-serif)",
          "Source Serif 4",
          "Iowan Old Style",
          "Georgia",
          "serif",
        ],
        mono: [
          "var(--font-ibm-plex-mono)",
          "IBM Plex Mono",
          "Courier New",
          "monospace",
        ],
      },
      borderRadius: {
        none: "0",
        sm: "0",
        DEFAULT: "0",
        md: "0",
        lg: "0",
        xl: "0",
        "2xl": "0",
        "3xl": "0",
        "4xl": "0",
        full: "0",
      },
      boxShadow: {
        soft: "none",
        lift: "none",
        "inner-sm": "none",
      },
      backgroundImage: {
        "grid-dark": "none",
      },
      keyframes: {},
      animation: {},
    },
  },
  plugins: [],
};
