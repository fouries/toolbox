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

console.log('oil price page location initialization is valid')
