import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const homePath = path.resolve('src/pages/index/index.vue')
const source = fs.readFileSync(homePath, 'utf8')
const quickToolListBlock = source.match(/\.quick-tool-list\s*\{[^}]*\}/)?.[0] || ''
const templateBlock = source.match(/<template>[\s\S]*<\/template>/)?.[0] || ''
const searchIndex = templateBlock.indexOf('class="tool-search-wrap"')
const quickIndex = templateBlock.indexOf('class="quick-panel"')
const categoryIndex = templateBlock.indexOf('class="category-scroll"')

assert.doesNotMatch(source, /hero-bg-dot|dot-one|dot-two/, 'home page should not render colored corner decoration dots')

assert.doesNotMatch(source, /\.tool-item\s*\{[\s\S]*min-height:\s*220rpx;/, 'mobile tool cards should not use oversized 220rpx cards')
assert.match(source, /\.tool-item\s*\{[\s\S]*min-height:\s*156rpx;/, 'mobile tool cards should use a compact card height')
assert.match(source, /\.tool-item\s*\{[\s\S]*align-items:\s*flex-start;/, 'tool cards should use a clean left-aligned content layout')
assert.match(source, /\.tool-icon\s*\{[\s\S]*width:\s*72rpx;[\s\S]*height:\s*72rpx;/, 'tool icons should be scaled down for compact cards')
assert.match(source, /@media\s*\(min-width:\s*768px\)[\s\S]*\.tool-item\s*\{[\s\S]*min-height:\s*136px;/, 'desktop tool cards should also be compact')

assert.ok(searchIndex !== -1 && quickIndex !== -1 && categoryIndex !== -1, 'home page should render search, popular tools, and categories')
assert.ok(searchIndex < quickIndex && quickIndex < categoryIndex, 'search bar should sit above popular tools, and popular tools should sit above categories')
assert.match(source, /<button\s+class="search-submit"\s+@click="submitSearch">搜索<\/button>/, 'search bar should include a search button on the right')
assert.match(source, /const\s+submitSearch\s*=\s*\(\)\s*=>\s*\{[\s\S]*searchText\.value\s*=\s*searchText\.value\.trim\(\)/, 'search button should normalize the current search text')
assert.match(source, /\.tool-search\s*\{[\s\S]*gap:\s*12rpx;/, 'search input and button should have compact spacing')
assert.match(source, /\.search-submit\s*\{[\s\S]*flex-shrink:\s*0;[\s\S]*height:\s*56rpx;/, 'search button should stay fixed on the right side of the search bar')

assert.match(source, /<scroll-view\s+class="quick-tool-scroll"\s+scroll-x="true"\s+show-scrollbar="false">[\s\S]*<view class="quick-tool-list">/, 'popular tools should render in a one-row horizontal scroll view')
assert.match(source, /getPopularTools\(10\)/, 'home page should request up to 10 popular tool rankings from backend')
assert.match(source, /return\s+rankedTools\.slice\(0,\s*10\)/, 'popular tools should display at most 10 tools')
assert.match(source, /\.quick-tool-scroll\s*\{[\s\S]*width:\s*100%;[\s\S]*white-space:\s*nowrap;/, 'popular tools scroll view should keep cards on one row')
assert.match(source, /\.quick-tool-list\s*\{[\s\S]*display:\s*flex;[\s\S]*flex-direction:\s*row;[\s\S]*flex-wrap:\s*nowrap;/, 'popular tools should use a non-wrapping row')
assert.doesNotMatch(quickToolListBlock, /grid-template-columns:/, 'popular tools should not use a wrapping grid')
assert.doesNotMatch(quickToolListBlock, /justify-content:\s*center;/, 'popular tools should not center the compact cards')
assert.match(source, /\.quick-tool-card\s*\{[\s\S]*flex:\s*0 0 112rpx;/, 'popular tool cards should have a fixed compact mobile width for horizontal scrolling')
assert.doesNotMatch(source, /class="quick-tool-desc"|\.quick-tool-desc\s*\{/, 'popular tool cards should not show tool descriptions')
assert.doesNotMatch(source, /class="quick-arrow"|\.quick-arrow\s*\{/, 'popular tool cards should not reserve right-side arrow space')
assert.match(source, /\.quick-tool-card\s*\{[\s\S]*flex-direction:\s*column;[\s\S]*align-items:\s*center;[\s\S]*justify-content:\s*center;/, 'popular tool cards should center compact icon and name without internal blank space')
assert.match(source, /\.quick-tool-card\s*\{[\s\S]*min-height:\s*88rpx;/, 'popular tool cards should stay short without descriptions')
assert.match(source, /\.quick-tool-card\s*\{[\s\S]*padding:\s*10rpx 6rpx;/, 'popular tool cards should use tighter compact padding')
assert.match(source, /\.quick-tool-icon\s*\{[\s\S]*width:\s*40rpx;[\s\S]*height:\s*40rpx;/, 'popular tool icons should shrink with the shorter cards')
assert.match(source, /@media\s*\(min-width:\s*768px\)[\s\S]*\.quick-tool-card\s*\{[\s\S]*flex-basis:\s*92px;[\s\S]*min-height:\s*60px;/, 'desktop popular tool cards should have compact fixed width in the scroll row')

assert.match(source, /import\s+\{\s*getPopularTools\s*,\s*recordToolClick\s*,\s*type\s+ToolPopularityItem\s*\}\s+from\s+'@\/api'/, 'home page should import popularity APIs')
assert.match(source, /const\s+toolClickCounts\s*=\s*ref<Record<string,\s*number>>\(\{\}\)/, 'home page should keep click counts from backend')
assert.match(source, /const\s+loadPopularTools\s*=\s*async\s*\(\)\s*=>/, 'home page should load global popular tools from backend')
assert.match(source, /getPopularTools\(10\)/, 'home page should request enough popular tool rankings from backend')
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
