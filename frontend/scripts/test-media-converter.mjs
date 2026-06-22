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
assert.match(api, /createMediaTask\s*=\s*\(payload/, 'api should provide multipart media task helper')
assert.match(api, /createMediaUrlTask\s*=\s*\(payload/, 'api should provide URL media task helper')
assert.match(api, /getMediaTask\s*=\s*\(taskId/, 'api should provide media task polling helper')
assert.match(api, /\/api\/media\/tasks/, 'api should call async media task endpoints')
assert.match(api, /\/api\/media\/url-tasks/, 'api should call async URL task endpoint')
assert.match(api, /\/api\/media\/tasks\/init/, 'api should initialize mp-weixin multi-file tasks')
assert.match(api, /\/api\/media\/tasks\/\$\{encodeURIComponent\(taskId\)\}\/files/, 'api should upload mp-weixin files to task')
assert.match(api, /\/api\/media\/tasks\/\$\{encodeURIComponent\(taskId\)\}\/start/, 'api should start mp-weixin uploaded task')
assert.match(api, /uni\.uploadFile/, 'mp-weixin should upload original media files')
assert.match(api, /new FormData\(/, 'H5 should upload original media files with multipart form data')
assert.match(api, /convertMediaBase64\s*=\s*\(payload/, 'api should keep base64 media conversion helper for compatibility')
assert.match(api, /extractUrlAudioBase64\s*=\s*\(payload/, 'api should keep URL base64 extraction helper for compatibility')
assert.match(api, /\/api\/media\/convert-base64/, 'api should keep legacy media conversion endpoint')
assert.match(api, /\/api\/media\/extract-url-audio/, 'api should keep legacy URL audio extraction endpoint')

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
assert.match(page, /createMediaTask\(/, 'page should create async media conversion tasks')
assert.match(page, /createMediaUrlTask\(/, 'page should create async URL extraction tasks')
assert.match(page, /getMediaTask\(/, 'page should poll task status')
assert.match(page, /任务进度/, 'page should show task progress')
assert.match(page, /download_url/, 'page should download completed task result')
assert.doesNotMatch(page, /readFileAsBase64/, 'page should not base64 encode large media before upload')
assert.match(page, /轻量声道处理|不是 Demucs 级 AI 分离/, 'page should disclose lightweight vocal separation limitation')
assert.match(page, /Whisper/, 'page should mention Whisper for speech-to-text')
assert.match(page, /getMediaTaskDownloadUrl\(/, 'H5 should download generated media through task download URL')
assert.match(page, /uni\.downloadFile\(/, 'mp-weixin should download generated media through task download URL')
assert.equal(pkg.scripts['test:media-converter'], 'node scripts/test-media-converter.mjs', 'package scripts should include media converter test')

console.log('media converter page, API, and home entry are valid')

const extraMediaChecks = ['视频压缩', '视频裁剪', '视频转 GIF', '提取封面', 'video_compress', 'video_trim', 'video_to_gif', 'extract_cover']
for (const token of extraMediaChecks) {
  if (!page.includes(token)) throw new Error(`missing video extra operations token: ${token}`)
}
console.log('video extra operations checks passed')
