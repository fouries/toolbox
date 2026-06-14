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
  /实时油价参考/,
  'realtime oil price card should be labelled as reference data'
)

assert.match(
  source,
  /每日更新，接口缓存约\s*1\s*小时/,
  'realtime oil price card should explain data timeliness'
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
