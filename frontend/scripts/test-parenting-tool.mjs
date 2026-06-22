import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const pagePath = path.resolve('src/pages/parenting/index.vue')
const pagesJsonPath = path.resolve('src/pages.json')
const homePath = path.resolve('src/pages/index/index.vue')
const packagePath = path.resolve('package.json')

const page = fs.readFileSync(pagePath, 'utf8')
const pagesJson = JSON.parse(fs.readFileSync(pagesJsonPath, 'utf8'))
const home = fs.readFileSync(homePath, 'utf8')
const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'))

assert.ok(pagesJson.pages.some(page => page.path === 'pages/parenting/index'), 'pages.json should register parenting route')
assert.match(home, /id:\s*'parenting'[\s\S]*name:\s*'育儿工具'[\s\S]*path:\s*'\/pages\/parenting\/index'[\s\S]*implemented:\s*true/, 'home should expose enabled parenting tool card')
assert.equal(pkg.scripts['test:parenting'], 'node scripts/test-parenting-tool.mjs', 'package scripts should include parenting test')
assert.match(pkg.scripts.test, /test:parenting/, 'full frontend test script should include parenting test')

assert.match(page, /孕晚期/, 'page should include pregnancy stage')
assert.match(page, /0-1 岁/, 'page should include infant stage')
assert.match(page, /1-3 岁/, 'page should include toddler stage')
assert.match(page, /3-6 岁/, 'page should include preschool stage')
assert.match(page, /胎动计数/, 'page should provide fetal movement counter')
assert.match(page, /预产期/, 'page should provide due date calculator')
assert.match(page, /奶量估算/, 'page should provide feeding helper')
assert.match(page, /睡眠参考/, 'page should provide sleep helper')
assert.match(page, /疫苗\/体检提醒/, 'page should provide vaccine and checkup reminders')
assert.match(page, /阶段清单/, 'page should provide stage checklist')
assert.match(page, /需要及时就医\/咨询的情况/, 'page should include red-flag medical guidance')
assert.match(page, /不替代医生诊断/, 'page should include medical disclaimer')
assert.match(page, /toggleCheck/, 'page should support checklist interactions')
assert.match(page, /milkSuggestion/, 'page should calculate milk suggestions')
assert.match(page, /sleepSuggestion/, 'page should calculate sleep suggestions')

console.log('parenting tool page and home entry are valid')
