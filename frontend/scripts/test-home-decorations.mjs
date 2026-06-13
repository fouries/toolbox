import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const homePath = path.resolve('src/pages/index/index.vue')
const source = fs.readFileSync(homePath, 'utf8')

assert.doesNotMatch(source, /hero-bg-dot|dot-one|dot-two/, 'home page should not render colored corner decoration dots')

assert.doesNotMatch(source, /\.tool-item\s*\{[\s\S]*min-height:\s*220rpx;/, 'mobile tool cards should not use oversized 220rpx cards')
assert.match(source, /\.tool-item\s*\{[\s\S]*min-height:\s*156rpx;/, 'mobile tool cards should use a compact card height')
assert.match(source, /\.tool-item\s*\{[\s\S]*align-items:\s*flex-start;/, 'tool cards should use a clean left-aligned content layout')
assert.match(source, /\.tool-icon\s*\{[\s\S]*width:\s*72rpx;[\s\S]*height:\s*72rpx;/, 'tool icons should be scaled down for compact cards')
assert.match(source, /@media\s*\(min-width:\s*768px\)[\s\S]*\.tool-item\s*\{[\s\S]*min-height:\s*136px;/, 'desktop tool cards should also be compact')

assert.match(source, /\.quick-tool-list\s*\{[\s\S]*display:\s*grid;[\s\S]*grid-template-columns:\s*repeat\(2,\s*minmax\(0,\s*1fr\)\);/, 'popular tools should use a tidy 2-column grid instead of loose wrapping pills')
assert.doesNotMatch(source, /\.quick-tool-card\s*\{[\s\S]*flex:\s*0 0 auto;/, 'popular tool cards should fill the grid instead of auto-sized chips')
assert.match(source, /\.quick-tool-card\s*\{[\s\S]*justify-content:\s*space-between;/, 'popular tool cards should have balanced spacing across each card')
assert.match(source, /\.quick-tool-card\s*\{[\s\S]*min-height:\s*104rpx;/, 'popular tool cards should use compact card height')
assert.match(source, /@media\s*\(min-width:\s*768px\)[\s\S]*\.quick-tool-list\s*\{[\s\S]*grid-template-columns:\s*repeat\(4,\s*minmax\(0,\s*1fr\)\);/, 'desktop popular tools should become an even 4-column strip')

console.log('home page cards and popular tools use compact polished layouts')
