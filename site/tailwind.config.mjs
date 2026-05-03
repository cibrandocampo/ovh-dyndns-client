/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,ts,tsx,md,mdx}'],
  darkMode: 'media',
  theme: {
    extend: {
      colors: {
        brand: '#FCD34D',
        ovh: {
          50:  '#f1f2f5',
          100: '#dde0e8',
          300: '#8d93a9',
          500: '#454961',
          600: '#3a3d52',
          700: '#2d3041',
          800: '#23252f',
          900: '#181a22',
          950: '#0e0f15',
        },
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
    },
  },
}
