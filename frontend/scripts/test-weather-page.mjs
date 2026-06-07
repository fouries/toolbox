import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const sourcePath = path.resolve('src/pages/weather/index.vue')
const source = fs.readFileSync(sourcePath, 'utf8')

assert.match(
  source,
  /const\s+initWeatherPage\s*=\s*async\s*\(\)\s*=>/,
  'weather page should have an initialization function'
)

assert.match(
  source,
  /onMounted\(\(\)\s*=>\s*\{\s*initWeatherPage\(\)/s,
  'weather page should try current location on first open instead of immediately querying the default city'
)

assert.match(
  source,
  /await\s+useCurrentLocation\(\{\s*initial:\s*true\s*\}\)/s,
  'weather page initialization should reuse current-location lookup with initial=true'
)

assert.match(
  source,
  /const\s+useCurrentLocation\s*=\s*async\s*\(options:\s*\{\s*initial\?:\s*boolean\s*\}\s*=\s*\{\}\)/s,
  'current-location lookup should accept an initial option for first-open fallback behavior'
)

assert.match(
  source,
  /await\s+fetchWeather\(\)/,
  'located city should automatically query weather after location succeeds'
)

assert.match(
  source,
  /if\s*\(options\.initial\)\s*\{[\s\S]*await\s+fetchWeather\(\)/,
  'initial location failure should fall back to querying the default city'
)

assert.match(
  source,
  /<button class="location-btn" @click="\(\) => useCurrentLocation\(\)"/,
  'manual location button should remain available without receiving click event payload'
)

console.log('weather page auto-location initialization is valid')
