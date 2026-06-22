import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const homePath = path.resolve('src/pages/index/index.vue')
const apiPath = path.resolve('src/api/index.ts')
const home = fs.readFileSync(homePath, 'utf8')
const api = fs.readFileSync(apiPath, 'utf8')
const template = home.match(/<template>[\s\S]*<\/template>/)?.[0] || ''

assert.match(api, /export interface UserIdentity/, 'API should expose lightweight user identity type')
assert.match(api, /export const ensureAnonymousUser\s*=\s*\(userKey:\s*string\)/, 'API should create or refresh anonymous user identity')
assert.match(api, /export const getUserFavorites\s*=\s*\(userKey:\s*string\)/, 'API should fetch user favorite tool ids')
assert.match(api, /export const addUserFavorite\s*=\s*\(userKey:\s*string,\s*toolId:\s*string\)/, 'API should add favorite tool')
assert.match(api, /export const removeUserFavorite\s*=\s*\(userKey:\s*string,\s*toolId:\s*string\)/, 'API should remove favorite tool')

assert.match(home, /TOOLBOX_USER_KEY\s*=\s*'toolbox_user_key'/, 'home should persist a lightweight anonymous user key')
assert.match(home, /FAVORITE_TOOLS_KEY\s*=\s*'toolbox_favorite_tools'/, 'home should cache favorite tool ids locally')
assert.match(home, /const\s+favoriteToolIds\s*=\s*ref<string\[\]>\(\[\]\)/, 'home should keep favorite tool ids in state')
assert.match(home, /const\s+favoriteTools\s*=\s*computed/, 'home should map favorite ids to implemented tools')
assert.match(home, /const\s+ensureUserKey\s*=\s*\(\)/, 'home should generate/reuse anonymous user key')
assert.match(home, /ensureAnonymousUser\(userKey\.value\)/, 'home should sync anonymous identity to backend')
assert.match(home, /getUserFavorites\(userKey\.value\)/, 'home should load cloud favorites')
assert.match(home, /addUserFavorite\(userKey\.value,\s*tool\.id\)/, 'home should add favorites through backend')
assert.match(home, /removeUserFavorite\(userKey\.value,\s*tool\.id\)/, 'home should remove favorites through backend')
assert.match(home, /const\s+toggleFavorite\s*=\s*async\s*\(tool:\s*ToolItem\)/, 'home should expose a favorite toggle handler')

const favoriteIndex = template.indexOf('<text class="quick-panel-title-text">我的收藏</text>')
const recentIndex = template.indexOf('<text class="quick-panel-title-text">最近使用</text>')
const popularIndex = template.indexOf('<text class="quick-panel-title-text">热门工具</text>')
assert.ok(favoriteIndex !== -1, 'home should render a 我的收藏 quick panel')
assert.ok(favoriteIndex < recentIndex && recentIndex < popularIndex, 'favorites should appear before recent and popular panels')
assert.match(template, /v-for="tool in favoriteTools"/, 'favorites panel should render favoriteTools')
assert.match(template, /class="favorite-toggle"[\s\S]*@click\.stop="toggleFavorite\(tool\)"/, 'tool cards should include a non-navigating favorite toggle')
assert.match(home, /isFavorite\(tool\.id\)\s*\?\s*'★'\s*:\s*'☆'/, 'favorite button should visibly switch between starred and unstarred states')
assert.match(home, /\.favorite-toggle\s*\{[\s\S]*position:\s*absolute;/, 'favorite button should be positioned inside tool cards')
assert.match(home, /\.favorite-toggle\.active\s*\{[\s\S]*color:\s*#f59e0b;/, 'active favorite star should use a highlighted color')

console.log('home page supports anonymous user identity and favorite tools sync')
