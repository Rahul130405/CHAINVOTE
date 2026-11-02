/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./voting/templates/**/*.html",
    "./voting/static/**/*.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Noto Sans Devanagari', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        devanagari: ['Noto Sans Devanagari', 'sans-serif'],
      },
      colors: {
        apple: {
          light: '#f5f5f7',
          cardLight: 'rgba(255, 255, 255, 0.7)',
        }
      }
    },
  },
  plugins: [],
}
