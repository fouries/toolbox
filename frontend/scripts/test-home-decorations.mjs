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

assert.match(source, /\.quick-tool-list\s*\{[\s\S]*display:\s*grid;[\s\S]*grid-template-columns:\s*repeat\(2,\s*minmax\(0,\s*46%\)\);/, 'popular tools should use a narrower 2-column grid instead of full-width halves')
assert.match(source, /\.quick-tool-list\s*\{[\s\S]*justify-content:\s*center;/, 'popular tools should center the narrower compact cards')
assert.doesNotMatch(source, /\.quick-tool-card\s*\{[\s\S]*flex:\s*0 0 auto;/, 'popular tool cards should fill the compact grid cells instead of auto-sized chips')
assert.match(source, /\.quick-tool-card\s*\{[\s\S]*justify-content:\s*space-between;/, 'popular tool cards should have balanced spacing across each card')
assert.match(source, /\.quick-tool-card\s*\{[\s\S]*min-height:\s*88rpx;/, 'popular tool cards should use a shorter compact card height')
assert.match(source, /\.quick-tool-card\s*\{[\s\S]*padding:\s*14rpx 12rpx;/, 'popular tool cards should use tighter horizontal padding')
assert.match(source, /@media\s*\(min-width:\s*768px\)[\s\S]*\.quick-tool-list\s*\{[\s\S]*grid-template-columns:\s*repeat\(4,\s*minmax\(0,\s*144px\)\);/, 'desktop popular tools should use fixed compact card widths')
assert.match(source, /@media\s*\(min-width:\s*768px\)[\s\S]*\.quick-tool-card\s*\{[\s\S]*min-height:\s*62px;/, 'desktop popular tool cards should be shorter')

console.log('home page cards and popular tools use compact polished layouts')
