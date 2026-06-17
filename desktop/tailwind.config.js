/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // 4-level elevation system (exact spec tokens)
        void: "#000000",
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
        // DOSSIER//VOID blended-look accents (duotone per zone, never rainbow)
        hudViolet: "#A855F7",
        hudVioletDim: "#6D28D9",
        termGreen: "#21F38A",
        phosphor: "#18FFC8",
        posterBlue: "#1AA6FF",
        ink: "#0A1018",
        glitchRed: "#FF003C",
        glitchCyan: "#00E5FF",
      },
      borderRadius: { card: "12px", btn: "10px", input: "8px" },
      fontFamily: {
        // body / RTL default stays Arabic; display+mono are LATIN-ONLY.
        sans: ["'IBM Plex Sans Arabic'", "Cairo", "Segoe UI", "Tahoma", "sans-serif"],
        display: ["'Archivo Variable'", "Archivo", "sans-serif"],
        mono: ["'Share Tech Mono'", "'JetBrains Mono Variable'", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 0 24px rgba(79,227,224,0.10)",
        "glow-cyan": "0 0 24px rgba(79,227,224,0.18)",
        "glow-violet": "0 0 28px rgba(168,85,247,0.20)",
        "glow-green": "0 0 20px rgba(33,243,138,0.16)",
      },
      keyframes: {
        "crt-flicker": { "0%,100%": { opacity: "0.04" }, "50%": { opacity: "0.08" } },
        "glitch-skew": {
          "0%,100%": { transform: "translate(0)" },
          "20%": { transform: "translate(-2px,1px)" },
          "40%": { transform: "translate(2px,-1px)" },
          "60%": { transform: "translate(-1px,-1px)" },
          "80%": { transform: "translate(1px,1px)" },
        },
        sweep: { "0%": { transform: "translateY(-100%)" }, "100%": { transform: "translateY(200%)" } },
      },
      animation: {
        "crt-flicker": "crt-flicker .18s steps(2) infinite",
        sweep: "sweep 3.2s linear infinite",
      },
    },
  },
  plugins: [],
};
