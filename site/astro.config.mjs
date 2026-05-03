import { defineConfig } from 'astro/config'
import tailwind from '@astrojs/tailwind'

export default defineConfig({
  site: 'https://cibrandocampo.github.io',
  base: '/ovh-dyndns-client',
  output: 'static',
  trailingSlash: 'ignore',
  integrations: [tailwind()],
})
