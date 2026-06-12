import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const tabPages = [
  { file: 'src/pages/news/index.vue', shellClass: 'news-shell', label: 'news tab' },
  { file: 'src/pages/settings/index.vue', shellClass: 'settings-shell', label: 'settings tab' }
]

for (const page of tabPages) {
  const source = fs.readFileSync(path.resolve(page.file), 'utf8')

  assert.match(
    source,
    /<view\s+:class="\['container',\s*themeClass\]"\s*>/,
    `${page.label} should use the shared themed container as the full-width mobile root`
  )
  assert.match(
    source,
    new RegExp(`<view\\s+class="page-shell ${page.shellClass}"\\s*>`),
    `${page.label} should put page-shell on an inner wrapper, not on the padded root`
  )
  assert.doesNotMatch(
    source,
    /<view\s+class="(?:news-page|settings-page) page-shell"/,
    `${page.label} root must not combine width:100% page-shell with padding because it overflows mobile screens`
  )
  assert.match(source, /const\s+\{[^}]*themeClass[^}]*\}\s*=\s*useTheme\(\)/s, `${page.label} should bind active theme class`)
  assert.match(source, /\.container\s*\{[\s\S]*box-sizing:\s*border-box;/, `${page.label} root padding should be included in viewport width`)
}

console.log('tab pages use mobile-safe container layout')
