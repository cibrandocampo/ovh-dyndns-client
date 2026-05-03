#!/usr/bin/env node
/*
 * Prebuild hook: mirror ../docs/dashboard-*.png into ./public/screenshots/
 * so the Astro landing references them via /<base>/screenshots/<file>.
 * Sync mode: stale files in destination are removed.
 */
import { copyFileSync, mkdirSync, readdirSync, rmSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const SRC = join(__dirname, '..', '..', 'docs')
const DEST = join(__dirname, '..', 'public', 'screenshots')

function listDashboardPngs(dir) {
  const result = new Set()
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.isFile() && entry.name.startsWith('dashboard-') && entry.name.endsWith('.png')) {
      result.add(entry.name)
    }
  }
  return result
}

function listAllFiles(dir) {
  const result = new Set()
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.isFile()) result.add(entry.name)
  }
  return result
}

mkdirSync(DEST, { recursive: true })

const srcFiles = listDashboardPngs(SRC)
// DEST is fully owned by this hook (gitignored) — sweep ANY file the
// source no longer provides, not just stale `dashboard-*.png`. This
// matches the "sync mode" promise in the header comment.
let destFiles = new Set()
try {
  destFiles = listAllFiles(DEST)
} catch {
  // dest empty, fine
}

let copied = 0
for (const name of srcFiles) {
  copyFileSync(join(SRC, name), join(DEST, name))
  copied += 1
}

let removed = 0
for (const name of destFiles) {
  if (srcFiles.has(name)) continue
  rmSync(join(DEST, name), { force: true })
  removed += 1
}

const suffix = removed > 0 ? ` (removed ${removed} stale)` : ''
console.log(`copy-screenshots: mirrored ${copied} PNG(s) from docs → site/public/screenshots${suffix}`)
