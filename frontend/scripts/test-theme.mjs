import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const themePath = path.resolve('src/utils/theme.ts')
const appPath = path.resolve('src/App.vue')
const globalStylePath = path.resolve('src/uni.scss')
const settingsPath = path.resolve('src/pages/settings/index.vue')

assert.ok(fs.existsSync(themePath), 'theme utility should exist')

const themeSource = fs.readFileSync(themePath, 'utf8')
const appSource = fs.readFileSync(appPath, 'utf8')
const globalStyleSource = fs.readFileSync(globalStylePath, 'utf8')
const settingsSource = fs.readFileSync(settingsPath, 'utf8')

for (const id of ['light', 'warm', 'fresh', 'minimal', 'night']) {
  assert.match(themeSource, new RegExp(`id:\\s*['"]${id}['"]`), `theme ${id} should be defined`)
  assert.match(themeSource, new RegExp(`theme-${id}`), `theme ${id} should expose a CSS class`)
}

assert.match(themeSource, /export\s+function\s+useTheme/, 'theme utility should expose useTheme')
assert.match(themeSource, /export\s+function\s+initTheme/, 'theme utility should expose initTheme')
assert.match(themeSource, /showActionSheet/, 'theme utility should open a native action sheet')
assert.match(themeSource, /setStorageSync\(['"]toolbox-theme['"]/, 'selected theme should be persisted')
assert.match(appSource, /initTheme\(\)/, 'app should initialize persisted theme on launch')
assert.match(
  settingsSource,
  /v-for="theme in themes"[\s\S]*@click="setTheme\(theme\.id\)"/,
  'settings tab should render theme choices and switch themes from the tab page'
)
assert.match(
  globalStyleSource,
  /\.container\.theme-light \.search-input,[\s\S]*\.container\.theme-night \.input[\s\S]*background:\s*transparent\s*!important;/,
  'themed search/input placeholders should not sit on a colored filled input background'
)
assert.match(
  globalStyleSource,
  /\.container\.theme-light \.search-input,[\s\S]*\.container\.theme-night \.input[\s\S]*color:\s*var\(--theme-text\)\s*!important;/,
  'themed search/input text should keep normal themed text color'
)

const nightReadableTextClasses = [
  'setting-title',
  'setting-label',
  'option-label',
  'strength-title',
  'size-label',
  'tags-title',
  'note-title',
  'oil-icon',
  'forecast-title',
  'forecast-weather',
  'quick-panel',
  'quick-tool-card',
  'quick-tool-name',
  'quick-tool-desc',
  'category-item',
  'tool-item',
  'empty-state'
]

for (const className of nightReadableTextClasses) {
  assert.match(
    globalStyleSource,
    new RegExp(`\\.container\\.theme-night \\.${className}(?:\\s*[,\\{])`),
    `night theme should override .${className} directly to keep card text readable`
  )
}

const pageFiles = [
  'src/pages/index/index.vue',
  'src/pages/news/index.vue',
  'src/pages/settings/index.vue',
  'src/pages/oil-price/index.vue',
  'src/pages/weather/index.vue',
  'src/pages/qrcode/index.vue',
  'src/pages/password/index.vue'
]

for (const file of pageFiles) {
  const source = fs.readFileSync(path.resolve(file), 'utf8')
  assert.match(source, /themeClass/, `${file} should bind the active theme class on the root container`)
  assert.match(source, /:class=\"\['container', themeClass\]\"/, `${file} root container should include themeClass`)
}

console.log('theme switcher integration is valid')
