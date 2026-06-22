import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const pagePath = path.resolve('src/pages/document-converter/index.vue')
const apiPath = path.resolve('src/api/index.ts')
const pagesJsonPath = path.resolve('src/pages.json')
const homePath = path.resolve('src/pages/index/index.vue')
const packagePath = path.resolve('package.json')

const page = fs.readFileSync(pagePath, 'utf8')
const api = fs.readFileSync(apiPath, 'utf8')
const pagesJson = JSON.parse(fs.readFileSync(pagesJsonPath, 'utf8'))
const home = fs.readFileSync(homePath, 'utf8')
const pkg = JSON.parse(fs.readFileSync(packagePath, 'utf8'))

assert.ok(pagesJson.pages.some(page => page.path === 'pages/document-converter/index'), 'pages.json should register document converter route')
assert.match(home, /id:\s*'document-converter'[\s\S]*name:\s*'文档转换'[\s\S]*path:\s*'\/pages\/document-converter\/index'[\s\S]*implemented:\s*true/, 'home should expose enabled document converter tool card')
assert.match(api, /export interface DocumentConvertResult/, 'api should type document conversion result')
assert.match(api, /convertDocumentBase64\s*=\s*\(payload/, 'api should provide base64 document conversion helper')
assert.match(api, /\/api\/documents\/convert-base64/, 'api should call document conversion endpoint')

assert.match(page, /文档转换/, 'page should show document converter title')
assert.match(page, /TXT、HTML、Word、PDF|TXT、HTML、DOCX、PDF/, 'page should explain supported formats')
assert.match(page, /MAX_FILE_SIZE\s*=\s*5\s*\*\s*1024\s*\*\s*1024/, 'page should enforce 5MB upload limit')
assert.match(page, /chooseDocumentFile/, 'page should let users choose a document file')
assert.match(page, /wx\.chooseMessageFile/, 'mp-weixin should use chooseMessageFile for document upload')
assert.match(page, /uni\.chooseFile/, 'H5 should use chooseFile for document upload')
assert.match(page, /convertDocumentBase64\(/, 'page should call backend conversion API')
assert.match(page, /downloadConvertedFile/, 'page should provide converted file download/open action')
assert.match(page, /uni\.openDocument/, 'mp-weixin should open PDF/DOCX after conversion')
assert.match(page, /new Blob\(/, 'H5 should download converted file via Blob')
assert.match(page, /扫描件图片 PDF 暂不做 OCR/, 'page should disclose scanned PDF/OCR limitation')
assert.equal(pkg.scripts['test:document-converter'], 'node scripts/test-document-converter.mjs', 'package scripts should include document converter test')

console.log('document converter page, API, and home entry are valid')
