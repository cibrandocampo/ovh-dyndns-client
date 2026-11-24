import { defineConfig } from 'astro/config'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  site: 'https://ovh-dyndns.cibran.es',
  output: 'static',
  trailingSlash: 'ignore',
  // Astro 7 defaults to JSX whitespace rules, which drop the spaces between
  // inline elements written on separate lines. Keep the lossless mode.
  compressHTML: true,
  vite: {
    plugins: [tailwindcss()],
  },
})
