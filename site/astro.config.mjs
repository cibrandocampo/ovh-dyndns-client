import { defineConfig } from 'astro/config'
import tailwind from '@astrojs/tailwind'

export default defineConfig({
  site: 'https://ovh-dyndns.cibran.es',
  output: 'static',
  trailingSlash: 'ignore',
  integrations: [tailwind()],
})
