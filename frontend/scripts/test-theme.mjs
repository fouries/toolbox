import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const themePath = path.resolve('src/utils/theme.ts')
const switcherPath = path.resolve('src/components/ThemeSwitcher.vue')
const appPath = path.resolve('src/App.vue')

assert.ok(fs.existsSync(themePath), 'theme utility should exist')
assert.ok(fs.existsSync(switcherPath), 'theme switcher component should exist')

const themeSource = fs.readFileSync(themePath, 'utf8')
const switcherSource = fs.readFileSync(switcherPath, 'utf8')
const appSource = fs.readFileSync(appPath, 'utf8')

for (const id of ['light', 'warm', 'fresh', 'minimal', 'night']) {
  assert.match(themeSource, new RegExp(`id:\\s*['"]${id}['"]`), `theme ${id} should be defined`)
  assert.match(themeSource, new RegExp(`theme-${id}`), `theme ${id} should expose a CSS class`)
}

assert.match(themeSource, /export\s+function\s+useTheme/, 'theme utility should expose useTheme')
assert.match(themeSource, /export\s+function\s+initTheme/, 'theme utility should expose initTheme')
assert.match(themeSource, /showActionSheet/, 'theme utility should open a native action sheet')
assert.match(themeSource, /setStorageSync\(['"]toolbox-theme['"]/, 'selected theme should be persisted')
assert.match(appSource, /initTheme\(\)/, 'app should initialize persisted theme on launch')
assert.match(switcherSource, /theme-switcher/, 'switcher should render a fixed theme button')

const pageFiles = [
  'src/pages/index/index.vue',
  'src/pages/oil-price/index.vue',
  'src/pages/weather/index.vue',
  'src/pages/qrcode/index.vue',
  'src/pages/password/index.vue'
]

for (const file of pageFiles) {
  const source = fs.readFileSync(path.resolve(file), 'utf8')
  assert.match(source, /ThemeSwitcher/, `${file} should render the theme switcher`)
  assert.match(source, /themeClass/, `${file} should bind the active theme class on the root container`)
  assert.match(source, /:class=\"\['container', themeClass\]\"/, `${file} root container should include themeClass`)
}

console.log('theme switcher integration is valid')
