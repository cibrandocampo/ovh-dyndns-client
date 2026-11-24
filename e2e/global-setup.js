import { chromium } from '@playwright/test'
import { login, STORAGE_STATE } from './tests/helpers.js'

/**
 * Logs in once and saves the session for every test to reuse.
 * Login is rate-limited (5/minute), so tests must not log in each time.
 */
export default async function globalSetup(config) {
  const { baseURL } = config.projects[0].use
  const browser = await chromium.launch()
  const page = await browser.newPage({ baseURL })
  await login(page)
  await page.context().storageState({ path: STORAGE_STATE })
  await browser.close()
}
