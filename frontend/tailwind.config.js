/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          900: "#0d1117",
          800: "#161b22",
          700: "#21262d",
          600: "#30363d",
          500: "#3d444d",
        },
        accent: {
          blue: "#2f81f7",
          green: "#3fb950",
          yellow: "#d29922",
          orange: "#db6d28",
          red: "#f85149",
          purple: "#bc8cff",
        },
      },
    },
  },
  plugins: [],
};
