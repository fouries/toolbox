import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const sourcePath = path.resolve('src/pages/oil-price/index.vue')
const source = fs.readFileSync(sourcePath, 'utf8')

assert.match(
  source,
  /const\s+initOilPricePage\s*=\s*async\s*\(\)\s*=>/,
  'oil price page should have an initialization function'
)

assert.match(
  source,
  /onMounted\(\(\)\s*=>\s*\{\s*initOilPricePage\(\)/s,
  'oil price page should try current location on first open instead of immediately querying the default province'
)

assert.match(
  source,
  /await\s+useCurrentLocation\(\{\s*initial:\s*true\s*\}\)/s,
  'initialization should reuse current-location lookup with initial=true'
)

assert.match(
  source,
  /fetchOilPrice\(\)/,
  'manual province selection should still query oil price directly'
)

assert.match(
  source,
  /<picker[^>]+@change="onProvinceChange"/,
  'province picker should remain available for manually querying other provinces'
)

assert.match(
  source,
  /更多省份|手动选择省份/,
  'province picker should be labelled as a manual province selector'
)

assert.match(
  source,
  /class="realtime-oil-card"/,
  'oil price page should render a realtime oil price card'
)

assert.match(
  source,
  /<text\s+class="realtime-title">实时油价<\/text>/,
  'realtime oil price card title should be 实时油价'
)

assert.doesNotMatch(
  source,
  /实时油价参考/,
  'realtime oil price card should not use the old 参考 title'
)

assert.doesNotMatch(
  source,
  /<text\s+class="realtime-subtitle">/,
  'realtime oil price card should remove the subtitle description under the title'
)

assert.match(
  source,
  /<text\s+class="realtime-update-time">更新时间[:：]\s*\{\{\s*oilUpdateText\(\)\s*\}\}<\/text>/,
  'realtime oil price card should show update time under the title'
)

assert.match(
  source,
  /<text\s+class="oil-province-label oil-unit-label">单位[:：]元\/升<\/text>/,
  'realtime oil price card should keep the unit label on the right'
)

assert.match(
  source,
  /\.oil-unit-label\s*\{[^}]*white-space:\s*nowrap;[^}]*\}/s,
  'unit label should not wrap to the next line'
)

assert.match(
  source,
  /const\s+oilUpdateText\s*=\s*\(\)\s*=>/,
  'oil price page should provide an update-time fallback when API omits time'
)

assert.match(
  source,
  /接口未返回具体时间（每日更新）/,
  'oil price page should show a clear update-time fallback when API omits time'
)

assert.match(
  source,
  /const\s+formatCrudeName\s*=\s*\(item:\s*CrudeOilItem\)\s*=>/,
  'oil price page should format crude oil names explicitly'
)

assert.match(
  source,
  /return 'WTI 原油'/,
  'WTI crude oil item should display as WTI 原油'
)

assert.match(
  source,
  /return 'Brent 原油'/,
  'Brent crude oil item should display as Brent 原油'
)

assert.doesNotMatch(
  source,
  /item\.name \|\| item\.type \|\| '原油'/,
  'crude oil card should not display upstream Chinese crude names directly'
)

assert.match(
  source,
  /const\s+crudeOilUpdateText\s*=\s*\(\)\s*=>/,
  'crude oil card should provide a dedicated update-time display helper'
)

assert.match(
  source,
  /<text>更新时间[:：]\s*\{\{\s*crudeOilUpdateText\(\)\s*\}\}<\/text>/,
  'crude oil card should display update time with the concise 更新时间 label'
)

assert.doesNotMatch(
  source,
  /国际原油更新时间/,
  'crude oil update-time label should not repeat 国际原油'
)

assert.match(
  source,
  /接口未返回具体时间（行情参考）/,
  'crude oil card should show a clear update-time fallback when API omits time'
)

assert.match(
  source,
  /item\.updown\s*\|\|\s*'行情参考'/,
  'crude oil item meta should keep change info separate from update time'
)

assert.match(
  source,
  /class="location-row"/,
  'current location and refresh-location button should share a compact row'
)

assert.match(
  source,
  /📍\s*当前定位：/,
  'current location text should show a location icon before the address'
)

assert.match(
  source,
  /<button[^>]*class="location-btn"[^>]*>/s,
  'refresh-location button should be displayed next to the current address'
)
assert.match(
  source,
  /locating \? '定位中\.\.\.' : '重新定位'/,
  'refresh-location button should keep locating and refresh labels'
)

console.log('oil price page realtime card, location initialization, and compact layout are valid')
