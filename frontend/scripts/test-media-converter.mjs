import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const pagePath = path.resolve('src/pages/media-converter/index.vue')
const apiPath = path.resolve('src/api/index.ts')
const pagesJsonPath = path.resolve('src/pages.json')
const homePath = path.resolve('src/pages/index/index.vue')
const packagePath = path.resolve('package.json')

const page = fs.readFileSync(pagePath, 'utf8')
const api = fs.readFileSync(apiPath, 'utf8')
const pagesJson = JSON.parse(fs.readFileSync(pagesJsonPath, 'utf8'))
const home = fs.readFileSync(homePath, 'utf8')
const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'))

assert.ok(pagesJson.pages.some(page => page.path === 'pages/media-converter/index'), 'pages.json should register media converter route')
assert.match(home, /id:\s*'media-converter'[\s\S]*name:\s*'音视频转换'[\s\S]*path:\s*'\/pages\/media-converter\/index'[\s\S]*implemented:\s*true/, 'home should expose enabled media converter tool card')
assert.match(api, /convertMediaBase64\s*=\s*\(payload/, 'api should provide base64 media conversion helper')
assert.match(api, /extractUrlAudioBase64\s*=\s*\(payload/, 'api should provide URL audio extraction helper')
assert.match(api, /\/api\/media\/convert-base64/, 'api should call media conversion endpoint')
assert.match(api, /\/api\/media\/extract-url-audio/, 'api should call URL audio extraction endpoint')

assert.match(page, /音视频转换/, 'page should show media converter title')
assert.match(page, /音频裁剪/, 'page should expose audio trimming')
assert.match(page, /音频拼接/, 'page should expose audio concatenation')
assert.match(page, /音频合并/, 'page should expose audio mixing')
assert.match(page, /声音转文字/, 'page should expose speech-to-text')
assert.match(page, /人声消除\/提取/, 'page should expose vocal remove/extract')
assert.match(page, /音量调节/, 'page should expose volume adjustment')
assert.match(page, /视频转音频/, 'page should expose video-to-audio')
assert.match(page, /链接提取音频/, 'page should expose URL audio extraction')
assert.match(page, /uni\.chooseFile/, 'page should choose local files')
assert.match(page, /wx\.chooseMessageFile/, 'page should choose files in mp-weixin')
assert.match(page, /MAX_FILE_SIZE\s*=\s*50\s*\*\s*1024\s*\*\s*1024/, 'page should enforce 50MB per file')
assert.match(page, /convertMediaBase64\(/, 'page should call backend media conversion API')
assert.match(page, /extractUrlAudioBase64\(/, 'page should call URL extraction API')
assert.match(page, /轻量声道处理|不是 Demucs 级 AI 分离/, 'page should disclose lightweight vocal separation limitation')
assert.match(page, /Whisper/, 'page should mention Whisper for speech-to-text')
assert.match(page, /new Blob\(/, 'H5 should download generated media via Blob')
assert.match(page, /writeFile\(/, 'mp-weixin should save generated media to user data path')
assert.equal(pkg.scripts['test:media-converter'], 'node scripts/test-media-converter.mjs', 'package scripts should include media converter test')

console.log('media converter page, API, and home entry are valid')
