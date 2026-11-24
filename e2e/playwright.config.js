import { defineConfig } from '@playwright/test'
import { STORAGE_STATE } from './tests/helpers.js'

export default defineConfig({
  testDir: './tests',
  globalSetup: './global-setup.js',
  timeout: 30_000,
  retries: 1,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost:8000',
    headless: true,
    storageState: STORAGE_STATE,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
})
