#!/usr/bin/env node
/*
 * Regenerate docs/dashboard-*.png from the running dev API.
 *
 * Captures four canonical scenes at viewport 1280x800:
 *   - dashboard-status.png    (default landing after login)
 *   - dashboard-hosts.png     (hosts management table)
 *   - dashboard-history.png   (history with hostname filter dropdown)
 *   - dashboard-settings.png  (settings card with version footer)
 *
 * Pre-requisites:
 *   - The dev container is up and the FastAPI server is reachable on
 *     `localhost:8000` (caller is responsible for booting it — see the
 *     project-root Makefile `screenshots` target).
 *   - The seed has been run (`python /scripts/seed.py --reset` inside
 *     the dev container) so the dashboard renders realistic data.
 *   - The seeded admin (admin / admin, must_change_password=False)
 *     reaches the dashboard directly without a forced password change.
 *
 * Env (all optional):
 *   BASE_URL          API root            (default http://localhost:8000)
 *   E2E_USERNAME      Login user          (default admin)
 *   E2E_PASSWORD      Login password      (default admin)
 *   SCREENSHOTS_DIR   Output directory    (default /screenshots)
 *
 * Manual run:
 *   docker run --rm --network host \
 *     -v "$(pwd)/e2e/screenshots.mjs":/e2e/screenshots.mjs \
 *     -v "$(pwd)/docs":/screenshots \
 *     ovh-dyndns-e2e node /e2e/screenshots.mjs
 *
 * The script is read-only — it logs in and navigates, but never clicks
 * a destructive control (no Add Host / Force Update / Delete). The dev
 * data survives the run untouched.
 */

import { chromium } from '@playwright/test'
import { mkdir } from 'fs/promises'
import { join } from 'path'

const BASE_URL = (process.env.BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')
const USERNAME = process.env.E2E_USERNAME ?? 'admin'
const PASSWORD = process.env.E2E_PASSWORD ?? 'admin'
const OUT = process.env.SCREENSHOTS_DIR ?? '/screenshots'

async function login(page) {
  await page.goto(BASE_URL + '/')
  await page.locator('#login-page').waitFor({ state: 'visible' })
  await page.locator('#username').fill(USERNAME)
  await page.locator('#password').fill(PASSWORD)
  await page.locator('#login-form button[type="submit"]').click()

  // Seeded admin has must_change_password=False, so the dashboard appears
  // directly. If the change-password page does appear, fail fast with a
  // useful message rather than silently capture the wrong screen.
  const dashboard = page.locator('#dashboard')
  const changePasswordPage = page.locator('#change-password-page')
  await Promise.race([
    dashboard.waitFor({ state: 'visible' }),
    changePasswordPage.waitFor({ state: 'visible' }),
  ])
  if (await changePasswordPage.isVisible()) {
    throw new Error(
      'Login redirected to change-password — re-seed the database with `python /scripts/seed.py --reset` so the admin user has must_change_password=False.',
    )
  }
}

async function shoot(page, name) {
  // `networkidle` waits for fetches triggered by the section render to
  // complete (e.g., /api/history/hostnames when entering History).
  await page.waitForLoadState('networkidle')
  // Small debounce so fonts and any CSS transitions settle.
  await page.waitForTimeout(300)
  const path = join(OUT, `${name}.png`)
  await page.screenshot({ path, fullPage: false })
  console.log(`captured ${path}`)
}

async function showSection(page, section) {
  await page.locator(`.nav-link[data-section="${section}"]`).click()
  await page.locator(`#${section}-section`).waitFor({ state: 'visible' })
}

const browser = await chromium.launch()
const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } })
const page = await ctx.newPage()
await mkdir(OUT, { recursive: true })

await login(page)

// 01 — Status (default landing after login)
await page.locator('#status-section').waitFor({ state: 'visible' })
await shoot(page, 'dashboard-status')

// 02 — Hosts
await showSection(page, 'hosts')
await shoot(page, 'dashboard-hosts')

// 03 — History
await showSection(page, 'history')
await shoot(page, 'dashboard-history')

// 04 — Settings
await showSection(page, 'settings')
await shoot(page, 'dashboard-settings')

await browser.close()
console.log('done')
