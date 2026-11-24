import { test, expect } from '@playwright/test'
import { openDashboard, goToSection } from './helpers.js'

// The API now rejects such hostnames, but hosts stored before that validation
// may still contain them, so the UI is tested with a mocked API response.
const EVIL_HOSTNAME = "x');window.__xss=1;//"

const evilHost = {
  id: 999999,
  hostname: EVIL_HOSTNAME,
  username: 'user',
  last_update: null,
  last_status: null,
  last_error: null,
  created_at: null,
}

test.describe('Hostnames are never executed as code', () => {
  test('force update on the status table', async ({ page }) => {
    await page.route('**/api/status/', route =>
      route.fulfill({ json: { current_ip: null, last_check: null, next_check: null, hosts: [evilHost] } }),
    )
    let triggeredUrl = null
    await page.route('**/api/status/trigger/**', route => {
      triggeredUrl = route.request().url()
      return route.fulfill({ json: { success: true, message: 'ok' } })
    })

    await openDashboard(page)
    await page.locator('#host-status-table [aria-label="Force update"]').click()
    await expect(page.locator('#status-message')).toBeVisible()

    expect(await page.evaluate(() => window.__xss)).toBeUndefined()
    expect(decodeURIComponent(new URL(triggeredUrl).pathname)).toBe(`/api/status/trigger/${EVIL_HOSTNAME}`)
  })

  test('delete confirmation on the hosts table', async ({ page }) => {
    await page.route('**/api/hosts/', route => route.fulfill({ json: [evilHost] }))

    await openDashboard(page)
    await goToSection(page, 'hosts')
    await page.locator('#hosts-table [aria-label="Delete host"]').click()

    await expect(page.locator('#delete-hostname')).toHaveText(EVIL_HOSTNAME)
    expect(await page.evaluate(() => window.__xss)).toBeUndefined()
  })
})
