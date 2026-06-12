import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const homePath = path.resolve('src/pages/index/index.vue')
const source = fs.readFileSync(homePath, 'utf8')

assert.doesNotMatch(source, /hero-bg-dot|dot-one|dot-two/, 'home page should not render colored corner decoration dots')

console.log('home page colored corner decorations are removed')
