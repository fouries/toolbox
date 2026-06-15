import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const pagesJsonPath = path.resolve('src/pages.json')
const homePath = path.resolve('src/pages/index/index.vue')
const apiPath = path.resolve('src/api/index.ts')
const calendarPath = path.resolve('src/pages/calendar/index.vue')
const lunarUtilPath = path.resolve('src/utils/lunar-calendar.ts')
const oilPath = path.resolve('src/pages/oil-price/index.vue')
const solarTermsPagePath = path.resolve('src/pages/solar-terms/index.vue')
const infoNewsPagePath = path.resolve('src/pages/info-news/index.vue')
const newsDetailPagePath = path.resolve('src/pages/news-detail/index.vue')
const goldPagePath = path.resolve('src/pages/gold-price/index.vue')
const backendMainPath = path.resolve('../backend/main.py')
const backendTianApiPath = path.resolve('../backend/api/tianapi.py')

for (const file of [solarTermsPagePath, infoNewsPagePath, newsDetailPagePath, goldPagePath]) {
  assert.ok(fs.existsSync(file), `${path.relative(process.cwd(), file)} should exist`)
}

const pagesJson = JSON.parse(fs.readFileSync(pagesJsonPath, 'utf8'))
const routes = pagesJson.pages.map(page => page.path)
assert.ok(routes.includes('pages/solar-terms/index'), 'pages.json should register 二十四节气 page route')
assert.ok(routes.includes('pages/info-news/index'), 'pages.json should register 资讯查询 page route')
assert.ok(routes.includes('pages/news-detail/index'), 'pages.json should register news detail page route')
assert.ok(routes.includes('pages/gold-price/index'), 'pages.json should register 黄金行情 page route')

const home = fs.readFileSync(homePath, 'utf8')
for (const [id, name] of [
  ['internet-news', '互联网资讯'],
  ['esports-news', '电竞资讯'],
  ['auto-news', '汽车新闻'],
  ['gold-price', '黄金行情'],
]) {
  assert.match(home, new RegExp(`id:\\s*'${id}'[\\s\\S]*name:\\s*'${name}'[\\s\\S]*implemented:\\s*true`), `home should enable ${name} card`)
}
assert.match(home, /category:\s*'market'/, 'home should include a market/news category for information tools')

const api = fs.readFileSync(apiPath, 'utf8')
assert.match(api, /export\s+interface\s+NewsItem/, 'api should expose NewsItem type')
assert.match(api, /export\s+interface\s+GoldPriceItem/, 'api should expose GoldPriceItem type')
assert.match(api, /export\s+interface\s+CrudeOilItem/, 'api should expose CrudeOilItem type')
assert.match(api, /getInfoNews\s*=\s*\(category:/, 'api should expose getInfoNews(category)')
assert.match(api, /\/api\/news\?category=\$\{encodeURIComponent\(category\)\}/, 'getInfoNews should call backend news endpoint with category')
assert.match(api, /export\s+interface\s+NewsDetail/, 'api should expose NewsDetail type')
assert.match(api, /getNewsDetail\s*=\s*\(url:/, 'api should expose getNewsDetail(url)')
assert.match(api, /\/api\/news\/detail\?url=\$\{encodeURIComponent\(url\)\}/, 'getNewsDetail should call backend news detail endpoint with encoded url')
assert.match(api, /getGoldPrice\s*=\s*\(\)/, 'api should expose getGoldPrice()')
assert.match(api, /\/api\/gold-price/, 'getGoldPrice should call backend gold endpoint')
assert.match(api, /getCrudeOilPrice\s*=\s*\(\)/, 'api should expose getCrudeOilPrice()')
assert.match(api, /\/api\/crude-oil/, 'getCrudeOilPrice should call backend crude-oil endpoint')

const lunarUtil = fs.readFileSync(lunarUtilPath, 'utf8')
assert.match(lunarUtil, /export\s+interface\s+SolarTermItem/, 'lunar utility should expose SolarTermItem type')
assert.match(lunarUtil, /export\s+function\s+getSolarTermsForYear/, 'lunar utility should expose a yearly solar-term lookup')
assert.match(lunarUtil, /立春[\s\S]*雨水[\s\S]*惊蛰[\s\S]*春分/, 'solar-term lookup should include the 24 terms in order')

const calendar = fs.readFileSync(calendarPath, 'utf8')
assert.match(calendar, /class="solar-term-entry-card"/, 'calendar page should show a 二十四节气 entry card')
assert.match(calendar, /二十四节气/, 'calendar entry card should be labelled 二十四节气')
assert.match(calendar, /goSolarTerms/, 'calendar page should provide a jump handler for solar terms')
assert.match(calendar, /\/pages\/solar-terms\/index\?date=\$\{selectedDay\.value\.dateText\}/, 'calendar should pass selected date to solar terms page')

const solarTermsPage = fs.readFileSync(solarTermsPagePath, 'utf8')
assert.match(solarTermsPage, /二十四节气/, 'solar terms page should render title text')
assert.match(solarTermsPage, /getSolarTermsForYear/, 'solar terms page should load terms from lunar utility')
assert.match(solarTermsPage, /v-for="term in solarTerms"/, 'solar terms page should render all solar terms')
assert.match(solarTermsPage, /当前日期/, 'solar terms summary should label the selected day as 当前日期')
assert.match(solarTermsPage, /summary-date[\s\S]*selectedDateText/, 'solar terms summary should display the current selected date instead of only the year')
assert.match(solarTermsPage, /当前节气/, 'solar terms page should show the current solar term')
assert.match(solarTermsPage, /currentSolarTerm/, 'solar terms page should calculate the active current solar term')
assert.match(solarTermsPage, /currentSolarTerm|nextTerm/, 'solar terms page should highlight current or next solar term')

const oilPage = fs.readFileSync(oilPath, 'utf8')
assert.match(oilPage, /原油价格|国际原油/, 'oil price page should include a crude-oil card')
assert.match(oilPage, /getCrudeOilPrice/, 'oil price page should fetch crude oil prices')
assert.match(oilPage, /class="crude-oil-card"/, 'oil price page should render crude oil data in its own card')
assert.match(oilPage, /WTI|布伦特|Brent/, 'crude oil card should show common crude oil benchmarks')

const infoNewsPage = fs.readFileSync(infoNewsPagePath, 'utf8')
assert.match(infoNewsPage, /互联网资讯|电竞资讯|汽车新闻/, 'info news page should support requested news categories')
assert.match(infoNewsPage, /getInfoNews/, 'info news page should fetch category news')
assert.match(infoNewsPage, /v-for="item in newsList"/, 'info news page should render a news list')
assert.match(infoNewsPage, /\/pages\/news-detail\/index\?url=\$\{encodeURIComponent\(safeUrl\)\}/, 'info news cards should navigate to native detail page')
assert.match(infoNewsPage, /normalizeNewsUrl/, 'info news cards should normalize protocol-relative esports URLs before navigation')
assert.match(infoNewsPage, /url\.startsWith\('\/\/'\)[\s\S]*`https:\$\{url\}`/, 'protocol-relative esports URLs should be converted to https URLs')
assert.match(infoNewsPage, /onLoad/, 'info news page should read category from route query')
assert.doesNotMatch(infoNewsPage, /<text class="news-desc"/, 'info news list should show titles only, not article body text')
assert.doesNotMatch(infoNewsPage, /item\.description/, 'info news list should not render news descriptions for esports or auto')
assert.doesNotMatch(infoNewsPage, /\.news-desc/, 'info news page should not keep description styling when rows are title-only')

const newsDetailPage = fs.readFileSync(newsDetailPagePath, 'utf8')
assert.match(newsDetailPage, /getNewsDetail/, 'news detail page should fetch cached article detail')
assert.match(newsDetailPage, /detail\.title/, 'news detail page should render article title')
assert.match(newsDetailPage, /detail\.content/, 'news detail page should render cleaned article content')
assert.match(newsDetailPage, /copyOriginalUrl/, 'news detail page should keep original link copy fallback')
assert.match(newsDetailPage, /onLoad/, 'news detail page should read source url from route query')

const goldPage = fs.readFileSync(goldPagePath, 'utf8')
assert.match(goldPage, /黄金行情/, 'gold page should render title text')
assert.match(goldPage, /getGoldPrice/, 'gold page should fetch gold market data')
assert.match(goldPage, /v-for="item in goldList"/, 'gold page should render gold list')
assert.match(goldPage, /刷新行情/, 'gold page should provide a refresh action')

const backendMain = fs.readFileSync(backendMainPath, 'utf8')
const backendTianApi = fs.readFileSync(backendTianApiPath, 'utf8')
assert.match(backendMain, /@app\.get\("\/api\/news"/, 'backend should expose /api/news')
assert.match(backendMain, /@app\.get\("\/api\/news\/detail"/, 'backend should expose /api/news/detail')
assert.match(backendMain, /NewsDetailService\.fetch_detail/, 'backend news detail endpoint should call detail fetch service')
assert.match(backendMain, /@app\.get\("\/api\/gold-price"/, 'backend should expose /api/gold-price')
assert.match(backendMain, /@app\.get\("\/api\/crude-oil"/, 'backend should expose /api/crude-oil')
assert.match(backendTianApi, /get_info_news/, 'TianApi service should implement category news fetcher')
assert.match(backendTianApi, /get_gold_price/, 'TianApi service should implement gold price fetcher')
assert.match(backendTianApi, /get_crude_oil/, 'TianApi service should implement crude oil fetcher')
assert.match(backendTianApi, /"internet":\s*"\/internet\/index"/, 'internet news should use TianAPI /internet/index endpoint')
assert.match(backendTianApi, /"esports":\s*"\/esports\/index"/, 'esports news should use TianAPI /esports/index endpoint')
assert.match(backendTianApi, /"auto":\s*"\/auto\/index"/, 'auto news should use TianAPI /auto/index endpoint')
assert.match(backendTianApi, /kinds="au9999,au9995,agTplusD"/, 'gold price should send required TianAPI kinds parameter')
assert.match(backendTianApi, /"wti",\s*"blt"/, 'crude oil should query supported WTI and Brent codes')
assert.match(backendTianApi, /"\/crude\/index"/, 'crude oil should use TianAPI /crude/index endpoint')

console.log('market news, solar terms, crude oil, and gold features are valid')
