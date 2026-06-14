import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const pagePath = path.resolve('src/pages/calendar/index.vue')
const lunarUtilPath = path.resolve('src/utils/lunar-calendar.ts')
const pagesJsonPath = path.resolve('src/pages.json')
const homePath = path.resolve('src/pages/index/index.vue')
const packagePath = path.resolve('package.json')
const calendarSeoPath = path.resolve('public/calendar.html')
const historySeoPath = path.resolve('public/history-today.html')
const copySeoPath = path.resolve('scripts/copy-seo-static.mjs')
const sitemapPath = path.resolve('public/sitemap.xml')
const historyPagePath = path.resolve('src/pages/history-today/index.vue')
const historyUtilPath = path.resolve('src/utils/history-today.ts')

assert.ok(fs.existsSync(pagePath), 'calendar page should exist at src/pages/calendar/index.vue')
assert.ok(fs.existsSync(lunarUtilPath), 'calendar page should share lunar/almanac logic in src/utils/lunar-calendar.ts')
assert.ok(fs.existsSync(historyPagePath), 'history today page should exist at src/pages/history-today/index.vue')
assert.ok(fs.existsSync(historyUtilPath), 'history today data utility should exist at src/utils/history-today.ts')

const page = fs.readFileSync(pagePath, 'utf8')
const lunarUtil = fs.readFileSync(lunarUtilPath, 'utf8')
const historyPage = fs.readFileSync(historyPagePath, 'utf8')
const historyUtil = fs.readFileSync(historyUtilPath, 'utf8')
const pagesJson = JSON.parse(fs.readFileSync(pagesJsonPath, 'utf8'))
const home = fs.readFileSync(homePath, 'utf8')
const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'))
const copySeo = fs.readFileSync(copySeoPath, 'utf8')
const sitemap = fs.readFileSync(sitemapPath, 'utf8')

assert.ok(fs.existsSync(calendarSeoPath), 'calendar should have an SEO static landing page at public/calendar.html')
assert.ok(fs.existsSync(historySeoPath), 'history today should have an SEO static landing page at public/history-today.html')
const calendarSeo = fs.readFileSync(calendarSeoPath, 'utf8')
const historySeo = fs.readFileSync(historySeoPath, 'utf8')

assert.ok(
  pagesJson.pages.some(page => page.path === 'pages/calendar/index'),
  'pages.json should register the 黄历日历 page route'
)
assert.ok(
  pagesJson.pages.some(page => page.path === 'pages/history-today/index'),
  'pages.json should register the 历史上的今天 page route'
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
assert.match(page, /day\.holiday\?\.isOffDay/, 'month grid should mark official rest days')
assert.match(page, /class="holiday-rest-badge"/, 'calendar day cells should show a rest-day badge')
assert.match(page, /selectedDay\.holiday\?\.isOffDay/, 'selected day details should show official rest-day information')
assert.match(page, /selectedDay\.holiday\?\.isWorkday/, 'selected day details should distinguish adjusted workdays')
assert.match(page, /\.day-cell\.rest-day/, 'official rest days should have a visible calendar-cell style')
assert.match(page, /\.holiday-rest-badge/, 'official rest day badge should have a visible style')
assert.match(page, /goPrevMonth/, 'calendar page should allow navigating to previous month')
assert.match(page, /goNextMonth/, 'calendar page should allow navigating to next month')
assert.match(page, /goToday/, 'calendar page should provide a return-to-today action')
assert.match(page, /class="history-entry-card"/, 'calendar page should show a history-today entry card')
assert.match(page, /历史上的今天/, 'calendar page should label the history-today entry')
assert.match(page, /goHistoryToday/, 'calendar page should provide a jump handler for history today')
assert.match(page, /date=\$\{selectedDay\.value\.dateText\}/, 'calendar page should pass the selected date to history today')
assert.match(page, /uni\.navigateTo\(\{\s*url:\s*`\/pages\/history-today\/index\?date=/s, 'calendar page should navigate to the history today page with a date query')

assert.match(historyPage, /历史上的今天/, 'history today page should render title text')
assert.match(historyPage, /<picker[^>]+mode="date"[^>]+@change="onDateChange"/s, 'history today page should provide a date picker')
assert.match(historyPage, /getHistoryTodayEvents/, 'history today page should load events from the utility')
assert.match(historyPage, /onLoad/, 'history today page should read the date passed by the calendar route')
assert.match(historyPage, /options\?\.date/, 'history today page should accept a date route parameter')
assert.match(historyPage, /stripHtml/, 'history today page should strip HTML from remote history event titles and descriptions')
assert.match(historyPage, /v-for="event in events"/, 'history today page should render events list')
assert.match(historyPage, /event\.year/, 'history today page should show event years')
assert.match(historyPage, /class="event-card"/, 'history today page should use event cards')
assert.match(historyPage, /goCalendar/, 'history today page should provide a way back to the calendar')

assert.match(historyUtil, /export\s+interface\s+HistoryTodayEvent/, 'history utility should export HistoryTodayEvent type')
assert.match(historyUtil, /export\s+function\s+getHistoryTodayEvents/, 'history utility should export getHistoryTodayEvents')
assert.match(historyUtil, /export\s+async\s+function\s+fetchHistoryTodayEvents/, 'history utility should export async remote history fetcher')
assert.match(historyUtil, /baike\.baidu\.com\/cms\/home\/eventsOnHistory/, 'history utility should fetch full daily history data from Baidu Baike')
assert.match(historyUtil, /const\s+historyTodayData\s*=/, 'history utility should include local historical event data')
assert.match(historyUtil, /fallbackEvents/, 'history utility should provide fallback events for sparse dates')

assert.match(lunarUtil, /const\s+lunarInfo\s*=\s*\[/, 'lunar utility should include lunar calendar data')
assert.match(lunarUtil, /export\s+function\s+getCalendarDay/, 'lunar utility should export getCalendarDay')
assert.match(lunarUtil, /export\s+function\s+buildMonthDays/, 'lunar utility should export buildMonthDays')
assert.match(lunarUtil, /const\s+solarTerms\s*=/, 'lunar utility should include solar term lookup')
assert.match(lunarUtil, /const\s+suitPool\s*=/, 'lunar utility should generate daily 宜 items')
assert.match(lunarUtil, /const\s+avoidPool\s*=/, 'lunar utility should generate daily 忌 items')
assert.match(lunarUtil, /export\s+interface\s+HolidayInfo/, 'lunar utility should expose official holiday metadata')
assert.match(lunarUtil, /const\s+officialHolidayMap\s*=/, 'lunar utility should include official holiday rest/workday lookup')
assert.match(lunarUtil, /2026-02-15[\s\S]*春节[\s\S]*isOffDay:\s*true/, '2026 Spring Festival official rest days should be included')
assert.match(lunarUtil, /2026-02-14[\s\S]*春节调休上班[\s\S]*isWorkday:\s*true/, '2026 adjusted Spring Festival workdays should be included')
assert.match(lunarUtil, /holiday:\s*getHolidayInfo\(dayDate\)/, 'calendar day model should include official holiday info')

assert.match(
  pkg.scripts.test,
  /test:calendar/,
  'npm test should include the calendar page regression test'
)
assert.match(copySeo, /'calendar\.html'/, 'H5 build should copy calendar.html SEO page')
assert.match(copySeo, /'history-today\.html'/, 'H5 build should copy history-today.html SEO page')
assert.match(sitemap, /https:\/\/quan1234\.com\/calendar\.html/, 'sitemap should include calendar.html')
assert.match(sitemap, /https:\/\/quan1234\.com\/history-today\.html/, 'sitemap should include history-today.html')
assert.match(calendarSeo, /<title>[^<]*黄历日历/, 'calendar SEO page should have a descriptive title')
assert.match(calendarSeo, /href="https:\/\/quan1234\.com\/calendar\.html"/, 'calendar SEO page should have a canonical URL')
assert.match(calendarSeo, /#\/pages\/calendar\/index/, 'calendar SEO page should link to the UniApp calendar route')
assert.match(historySeo, /<title>[^<]*历史上的今天/, 'history today SEO page should have a descriptive title')
assert.match(historySeo, /href="https:\/\/quan1234\.com\/history-today\.html"/, 'history today SEO page should have a canonical URL')
assert.match(historySeo, /#\/pages\/history-today\/index/, 'history today SEO page should link to the UniApp history today route')

console.log('calendar page route, lunar almanac logic, and UI controls are valid')
