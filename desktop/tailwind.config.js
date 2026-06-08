/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // 4-level elevation system (exact spec tokens)
        level0: "#050B12",
        level1: "#08121D",
        level2: "#0D1724",
        level3: "#112132",
        border: "#14304A",
        accent: "#4FE3E0",
        accent2: "#24A8FF",
        ok: "#21D07A",
        warn: "#F7B731",
        danger: "#FF5B5B",
        ftext: "#F4F8FC",
        fdim: "#90A6BC",
      },
      borderRadius: { card: "12px", btn: "10px", input: "8px" },
      fontFamily: {
        sans: ["'IBM Plex Sans Arabic'", "Cairo", "Segoe UI", "Tahoma", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 24px rgba(79,227,224,0.10)",
      },
    },
  },
  plugins: [],
};
