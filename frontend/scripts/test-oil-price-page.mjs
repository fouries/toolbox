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

assert.doesNotMatch(
  source,
  /class="location-card"/,
  'current-region oil price card should be removed for a cleaner layout'
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

console.log('oil price page location initialization and compact layout are valid')
