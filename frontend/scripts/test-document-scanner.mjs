import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const pagePath = path.resolve('src/pages/document-scanner/index.vue')
const apiPath = path.resolve('src/api/index.ts')
const pagesJsonPath = path.resolve('src/pages.json')
const homePath = path.resolve('src/pages/index/index.vue')
const packagePath = path.resolve('package.json')

const page = fs.readFileSync(pagePath, 'utf8')
const api = fs.readFileSync(apiPath, 'utf8')
const pagesJson = JSON.parse(fs.readFileSync(pagesJsonPath, 'utf8'))
const home = fs.readFileSync(homePath, 'utf8')
const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'))

assert.ok(pagesJson.pages.some(page => page.path === 'pages/document-scanner/index'), 'pages.json should register document scanner route')
assert.match(home, /id:\s*'document-scanner'[\s\S]*name:\s*'拍照扫描'[\s\S]*path:\s*'\/pages\/document-scanner\/index'[\s\S]*implemented:\s*true/, 'home should expose enabled document scanner tool card')
assert.match(api, /scanDocumentBase64\s*=\s*\(payload/, 'api should provide base64 document scan helper')
assert.match(api, /\/api\/documents\/scan-base64/, 'api should call document scan endpoint')

assert.match(page, /拍照扫描/, 'scanner page should show title')
assert.match(page, /调用摄像头拍照/, 'scanner page should provide camera capture button')
assert.match(page, /从相册选择图片/, 'scanner page should provide album selection button')
assert.match(page, /uni\.chooseImage/, 'scanner page should use chooseImage')
assert.match(page, /sourceType:\s*\['camera'\]/, 'camera scan should request camera source')
assert.match(page, /sourceType:\s*\['album'\]/, 'scanner should allow album images')
assert.match(page, /MAX_FILE_SIZE\s*=\s*5\s*\*\s*1024\s*\*\s*1024/, 'scanner page should enforce 5MB per image')
assert.match(page, /一次最多 10 张/, 'scanner page should limit image count')
assert.match(page, /imageExts\s*=\s*\['jpg', 'jpeg', 'png', 'webp'\]/, 'scanner should define supported image extensions')
assert.match(page, /scanTargetFormats/, 'scanner should define output formats')
assert.match(page, /PDF/, 'scanner should support PDF output')
assert.match(page, /Word/, 'scanner should support Word output')
assert.match(page, /PPT/, 'scanner should support PPT output')
assert.match(page, /scanDocumentBase64\(/, 'scanner page should call backend scan API')
assert.match(page, /当前是图片扫描生成文档，不做 OCR 文字识别/, 'scanner page should disclose OCR limitation')
assert.match(page, /downloadConvertedFile/, 'scanner page should provide file download/open action')
assert.match(page, /uni\.openDocument/, 'mp-weixin should open generated document')
assert.match(page, /new Blob\(/, 'H5 should download generated file via Blob')
assert.equal(pkg.scripts['test:document-scanner'], 'node scripts/test-document-scanner.mjs', 'package scripts should include document scanner test')

console.log('document scanner page, API, and home entry are valid')

const scanModeChecks = ['扫描模式', '自动增强', '灰度扫描', '黑白扫描', 'mode: scanMode.value']
for (const token of scanModeChecks) {
  if (!page.includes(token)) throw new Error(`missing scan mode token: ${token}`)
}
console.log('scan mode checks passed')
