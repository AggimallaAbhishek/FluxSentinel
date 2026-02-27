/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#f4f5ef",
        ink: "#172026",
        accent: "#0f766e",
        threat: "#b91c1c"
      }
    }
  },
  plugins: []
};
