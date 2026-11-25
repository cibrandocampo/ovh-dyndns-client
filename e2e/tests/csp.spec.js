import { test, expect } from '@playwright/test'
import { openDashboard, goToSection } from './helpers.js'

test('dashboard runs without Content-Security-Policy violations', async ({ page }) => {
  await page.addInitScript(() => {
    window.__cspViolations = []
    document.addEventListener('securitypolicyviolation', (e) => {
      window.__cspViolations.push(`${e.violatedDirective} ${e.blockedURI}`)
    })
  })

  await openDashboard(page)
  await page.waitForLoadState('networkidle')
  for (const section of ['hosts', 'history', 'settings', 'status']) {
    await goToSection(page, section)
    await page.waitForLoadState('networkidle')
  }

  expect(await page.evaluate(() => window.__cspViolations)).toEqual([])
})
