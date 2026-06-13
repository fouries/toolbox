import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const pagePath = path.resolve('src/pages/calendar/index.vue')
const lunarUtilPath = path.resolve('src/utils/lunar-calendar.ts')
const pagesJsonPath = path.resolve('src/pages.json')
const homePath = path.resolve('src/pages/index/index.vue')
const packagePath = path.resolve('package.json')
const calendarSeoPath = path.resolve('public/calendar.html')
const copySeoPath = path.resolve('scripts/copy-seo-static.mjs')
const sitemapPath = path.resolve('public/sitemap.xml')

assert.ok(fs.existsSync(pagePath), 'calendar page should exist at src/pages/calendar/index.vue')
assert.ok(fs.existsSync(lunarUtilPath), 'calendar page should share lunar/almanac logic in src/utils/lunar-calendar.ts')

const page = fs.readFileSync(pagePath, 'utf8')
const lunarUtil = fs.readFileSync(lunarUtilPath, 'utf8')
const pagesJson = JSON.parse(fs.readFileSync(pagesJsonPath, 'utf8'))
const home = fs.readFileSync(homePath, 'utf8')
const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'))
const copySeo = fs.readFileSync(copySeoPath, 'utf8')
const sitemap = fs.readFileSync(sitemapPath, 'utf8')

assert.ok(fs.existsSync(calendarSeoPath), 'calendar should have an SEO static landing page at public/calendar.html')
const calendarSeo = fs.readFileSync(calendarSeoPath, 'utf8')

assert.ok(
  pagesJson.pages.some(page => page.path === 'pages/calendar/index'),
  'pages.json should register the 黄历日历 page route'
)

assert.match(
  home,
  /id:\s*'calendar'[\s\S]*implemented:\s*true/,
  'home calendar tool should be enabled after the feature is implemented'
)
assert.doesNotMatch(
  home,
  /id:\s*'calendar'[\s\S]*status:\s*'即将上线'/,
  'home calendar tool should no longer show the upcoming badge'
)

assert.match(page, /<picker[^>]+mode="date"[^>]+@change="onDateChange"/s, 'calendar page should provide a date picker')
assert.match(page, /class="month-grid"/, 'calendar page should render a month grid')
assert.match(page, /v-for="day in monthDays"/, 'calendar page should render every date in the month grid')
assert.match(page, /@tap="selectDay\(day\)"/, 'month grid days should be selectable')
assert.match(page, /selectedDay\.lunarText/, 'selected day should show lunar date text')
assert.match(page, /selectedDay\.suit/, 'selected day should show 宜 items')
assert.match(page, /selectedDay\.avoid/, 'selected day should show 忌 items')
assert.match(page, /selectedDay\.solarTerm/, 'selected day should show solar terms when available')
assert.match(page, /goPrevMonth/, 'calendar page should allow navigating to previous month')
assert.match(page, /goNextMonth/, 'calendar page should allow navigating to next month')
assert.match(page, /goToday/, 'calendar page should provide a return-to-today action')

assert.match(lunarUtil, /const\s+lunarInfo\s*=\s*\[/, 'lunar utility should include lunar calendar data')
assert.match(lunarUtil, /export\s+function\s+getCalendarDay/, 'lunar utility should export getCalendarDay')
assert.match(lunarUtil, /export\s+function\s+buildMonthDays/, 'lunar utility should export buildMonthDays')
assert.match(lunarUtil, /const\s+solarTerms\s*=/, 'lunar utility should include solar term lookup')
assert.match(lunarUtil, /const\s+suitPool\s*=/, 'lunar utility should generate daily 宜 items')
assert.match(lunarUtil, /const\s+avoidPool\s*=/, 'lunar utility should generate daily 忌 items')

assert.match(
  pkg.scripts.test,
  /test:calendar/,
  'npm test should include the calendar page regression test'
)
assert.match(copySeo, /'calendar\.html'/, 'H5 build should copy calendar.html SEO page')
assert.match(sitemap, /https:\/\/quan1234\.com\/calendar\.html/, 'sitemap should include calendar.html')
assert.match(calendarSeo, /<title>[^<]*黄历日历/, 'calendar SEO page should have a descriptive title')
assert.match(calendarSeo, /href="https:\/\/quan1234\.com\/calendar\.html"/, 'calendar SEO page should have a canonical URL')
assert.match(calendarSeo, /#\/pages\/calendar\/index/, 'calendar SEO page should link to the UniApp calendar route')

console.log('calendar page route, lunar almanac logic, and UI controls are valid')
