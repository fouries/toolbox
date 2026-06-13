import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const uniScss = fs.readFileSync(path.resolve('src/uni.scss'), 'utf8')
const pagesJson = JSON.parse(fs.readFileSync(path.resolve('src/pages.json'), 'utf8'))

assert.equal(
  pagesJson.tabBar?.position ?? 'bottom',
  'bottom',
  'native tabBar should stay bottom by default so mobile H5 and mini programs keep bottom tabs'
)

assert.match(
  uniScss,
  /#ifdef\s+H5[\s\S]*@media\s+screen\s+and\s+\(min-width:\s*768px\)/,
  'H5 styles should contain a desktop media query starting at 768px'
)

assert.match(
  uniScss,
  /@media\s+screen\s+and\s+\(max-width:\s*767px\)[\s\S]*\.uni-app--showtabbar\s+uni-page-wrapper[\s\S]*height:\s*calc\(100% - 56px - env\(safe-area-inset-bottom\)\)\s*!important;/,
  'mobile H5 should reserve viewport height for the fixed bottom tabbar'
)

assert.match(
  uniScss,
  /@media\s+screen\s+and\s+\(max-width:\s*767px\)[\s\S]*\.uni-app--showtabbar\s+\.container[\s\S]*padding-bottom:\s*calc\(24rpx \+ 56px \+ env\(safe-area-inset-bottom\)\)\s*!important;/,
  'mobile H5 should keep extra bottom safe spacing above the fixed bottom tabbar'
)

assert.match(
  uniScss,
  /uni-tabbar\.uni-tabbar-bottom\s+\.uni-tabbar[\s\S]*top:\s*18px;/,
  'desktop H5 should move the native bottom tabbar to the page top-right corner'
)

assert.match(
  uniScss,
  /uni-tabbar\.uni-tabbar-bottom\s+\.uni-tabbar[\s\S]*right:\s*max\(24px,\s*calc\(\(100vw - 1120px\) \/ 2 \+ 24px\)\);/,
  'desktop H5 should align the navigation to the right side of the page content'
)

assert.match(
  uniScss,
  /uni-tabbar\.uni-tabbar-bottom\s+\.uni-tabbar[\s\S]*left:\s*auto\s*!important;/,
  'desktop H5 should not stretch the navigation from the left edge'
)

assert.match(
  uniScss,
  /uni-tabbar\.uni-tabbar-bottom\s+\.uni-tabbar[\s\S]*bottom:\s*auto\s*!important;/,
  'desktop H5 should disable the bottom positioning of the tabbar'
)

assert.match(
  uniScss,
  /uni-tabbar\.uni-tabbar-bottom\s+\.uni-tabbar[\s\S]*width:\s*auto;/,
  'desktop H5 navigation should shrink-wrap its links instead of spanning full width'
)

assert.match(
  uniScss,
  /\.uni-app--showtabbar\s+uni-page-wrapper[\s\S]*padding-top:\s*88px\s*!important;/,
  'desktop H5 should reserve top space for the floating top-right navigation'
)

assert.match(
  uniScss,
  /\.uni-app--showtabbar\s+uni-page-wrapper::after[\s\S]*height:\s*0\s*!important;/,
  'desktop H5 should remove the mobile bottom placeholder space'
)

assert.match(
  uniScss,
  /uni-tabbar\.uni-tabbar-bottom\s+\.uni-tabbar__item[\s\S]*flex:\s*0\s+0\s+auto;/,
  'desktop H5 tab items should be compact top-nav links instead of stretched bottom items'
)

console.log('H5 tabBar has mobile-bottom and desktop top-right responsive styles')
