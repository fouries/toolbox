import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const homePath = path.resolve('src/pages/index/index.vue')
const source = fs.readFileSync(homePath, 'utf8')
const quickToolListBlock = source.match(/\.quick-tool-list\s*\{[^}]*\}/)?.[0] || ''

assert.doesNotMatch(source, /hero-bg-dot|dot-one|dot-two/, 'home page should not render colored corner decoration dots')

assert.doesNotMatch(source, /\.tool-item\s*\{[\s\S]*min-height:\s*220rpx;/, 'mobile tool cards should not use oversized 220rpx cards')
assert.match(source, /\.tool-item\s*\{[\s\S]*min-height:\s*156rpx;/, 'mobile tool cards should use a compact card height')
assert.match(source, /\.tool-item\s*\{[\s\S]*align-items:\s*flex-start;/, 'tool cards should use a clean left-aligned content layout')
assert.match(source, /\.tool-icon\s*\{[\s\S]*width:\s*72rpx;[\s\S]*height:\s*72rpx;/, 'tool icons should be scaled down for compact cards')
assert.match(source, /@media\s*\(min-width:\s*768px\)[\s\S]*\.tool-item\s*\{[\s\S]*min-height:\s*136px;/, 'desktop tool cards should also be compact')

assert.match(source, /\.quick-tool-list\s*\{[\s\S]*display:\s*grid;[\s\S]*grid-template-columns:\s*repeat\(2,\s*minmax\(0,\s*1fr\)\);/, 'popular tools should use a full-width 2-column grid without centering')
assert.doesNotMatch(quickToolListBlock, /justify-content:\s*center;/, 'popular tools should not center the compact cards')
assert.doesNotMatch(source, /\.quick-tool-card\s*\{[\s\S]*flex:\s*0 0 auto;/, 'popular tool cards should fill the compact grid cells instead of auto-sized chips')
assert.doesNotMatch(source, /class="quick-tool-desc"|\.quick-tool-desc\s*\{/, 'popular tool cards should not show tool descriptions')
assert.doesNotMatch(source, /class="quick-arrow"|\.quick-arrow\s*\{/, 'popular tool cards should not reserve right-side arrow space')
assert.match(source, /\.quick-tool-card\s*\{[\s\S]*flex-direction:\s*column;[\s\S]*align-items:\s*flex-start;[\s\S]*justify-content:\s*flex-start;/, 'popular tool cards should stack icon above text without right-side empty space')
assert.match(source, /\.quick-tool-info\s*\{[\s\S]*width:\s*100%;/, 'popular tool name should use the full card width')
assert.match(source, /\.quick-tool-card\s*\{[\s\S]*min-height:\s*104rpx;/, 'popular tool cards should be compact vertical cards without descriptions')
assert.match(source, /\.quick-tool-card\s*\{[\s\S]*padding:\s*14rpx;/, 'popular tool cards should use compact vertical padding')
assert.match(source, /@media\s*\(min-width:\s*768px\)[\s\S]*\.quick-tool-list\s*\{[\s\S]*grid-template-columns:\s*repeat\(4,\s*minmax\(0,\s*1fr\)\);/, 'desktop popular tools should use full-width compact card columns')
assert.match(source, /@media\s*\(min-width:\s*768px\)[\s\S]*\.quick-tool-card\s*\{[\s\S]*min-height:\s*72px;/, 'desktop popular tool cards should be compact vertical cards without descriptions')

assert.match(source, /import\s+\{\s*getPopularTools\s*,\s*recordToolClick\s*,\s*type\s+ToolPopularityItem\s*\}\s+from\s+'@\/api'/, 'home page should import popularity APIs')
assert.match(source, /const\s+toolClickCounts\s*=\s*ref<Record<string,\s*number>>\(\{\}\)/, 'home page should keep click counts from backend')
assert.match(source, /const\s+loadPopularTools\s*=\s*async\s*\(\)\s*=>/, 'home page should load global popular tools from backend')
assert.match(source, /getPopularTools\(8\)/, 'home page should request enough popular tool rankings from backend')
assert.match(source, /const\s+rankedTools\s*=\s*tools\.value[\s\S]*toolClickCounts\.value\[b\.id\][\s\S]*toolClickCounts\.value\[a\.id\]/, 'popular tools should sort by backend click counts')
assert.match(source, /const\s+trackToolClick\s*=\s*async\s*\(toolId:\s*string\)\s*=>/, 'home page should record clicks in a non-blocking helper')
assert.match(source, /recordToolClick\(toolId\)/, 'tool clicks should be recorded to backend')
assert.doesNotMatch(source, /const\s+goToTool\s*=\s*async/, 'tool navigation handler should not be async')
assert.match(source, /const\s+goToTool\s*=\s*\(tool:\s*ToolItem\)\s*=>\s*\{[\s\S]*uni\.navigateTo\(\{\s*url:\s*tool\.path\s*\}\)[\s\S]*void\s+trackToolClick\(tool\.id\)/, 'tool card should navigate immediately and record the click in background')
assert.match(source, /onMounted\(\(\)\s*=>\s*\{\s*loadPopularTools\(\)/s, 'home page should refresh popular tools when opened')
assert.doesNotMatch(source, /filter\(t\s*=>\s*t\.implemented\)\.slice\(0,\s*4\)/, 'popular tools should not be the static first four implemented tools')

assert.doesNotMatch(source, /id:\s*'password'|name:\s*'密码生成'|path:\s*'\/pages\/password\/index'/, 'home page should not show the password generator card')
assert.doesNotMatch(source, /id:\s*'url'|name:\s*'URL编码'|path:\s*'\/pages\/url\/index'/, 'home page should not show the URL encoder card')
assert.doesNotMatch(source, /id:\s*'json'|name:\s*'JSON格式化'|path:\s*'\/pages\/json\/index'/, 'home page should not show the JSON formatter card')
assert.doesNotMatch(source, /id:\s*'base64'|name:\s*'Base64'|path:\s*'\/pages\/base64\/index'/, 'home page should not show the Base64 card')

console.log('home page cards and popular tools use compact polished layouts')
