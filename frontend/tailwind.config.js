/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        fintech: {
          dark: "#04060B",
          surface: "#070A14",
          elevated: "#0C101F",
          card: "#10162A",
          border: "#18223B",
          borderHover: "#27365D",
          cyan: "#00E5FF",
          blue: "#2979FF",
          emerald: "#00E676",
          crimson: "#FF1744",
          amber: "#FFB300",
          muted: "#64748B",
          subtle: "#94A3B8",
          text: "#F8FAFC",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "SFMono-Regular", "Menlo", "monospace"],
      },
      boxShadow: {
        "fintech-glow": "0 0 30px -5px rgba(0, 229, 255, 0.15)",
        "fintech-glow-lg": "0 0 50px -8px rgba(0, 229, 255, 0.2)",
        "emerald-glow": "0 0 30px -5px rgba(0, 230, 118, 0.15)",
        "crimson-glow": "0 0 30px -5px rgba(255, 23, 68, 0.15)",
        "amber-glow": "0 0 30px -5px rgba(255, 179, 0, 0.15)",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        fadeInUp: {
          from: { opacity: "0", transform: "translateY(20px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        fadeInScale: {
          from: { opacity: "0", transform: "scale(0.96)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        glowPulse: {
          "0%, 100%": { boxShadow: "0 0 20px -5px rgba(0, 229, 255, 0.15)" },
          "50%": { boxShadow: "0 0 40px -5px rgba(0, 229, 255, 0.3)" },
        },
      },
      animation: {
        fadeIn: "fadeIn 0.4s ease-out both",
        fadeInUp: "fadeInUp 0.5s ease-out both",
        fadeInScale: "fadeInScale 0.35s ease-out both",
        glowPulse: "glowPulse 3s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
