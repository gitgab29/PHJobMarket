/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Hanken Grotesk', 'system-ui', 'sans-serif'],
        mono: ['IBM Plex Mono', 'ui-monospace', 'monospace'],
      },
      colors: {
        accent: {
          50: 'oklch(0.96 0.03 var(--accent-h))',
          100: 'oklch(0.93 0.05 var(--accent-h))',
          500: 'oklch(0.55 0.17 var(--accent-h))',
          600: 'oklch(0.47 0.18 var(--accent-h))',
        }
      },
      spacing: {
        'card': '20px',
      },
      borderRadius: {
        'sm': '6px',
        'md': '9px',
      }
    },
  },
  plugins: [],
}
