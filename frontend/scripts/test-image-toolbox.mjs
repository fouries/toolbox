import { readFileSync } from 'node:fs'

const page = readFileSync(new URL('../src/pages/image-toolbox/index.vue', import.meta.url), 'utf8')
const api = readFileSync(new URL('../src/api/index.ts', import.meta.url), 'utf8')
const pagesJson = readFileSync(new URL('../src/pages.json', import.meta.url), 'utf8')
const home = readFileSync(new URL('../src/pages/index/index.vue', import.meta.url), 'utf8')

const checks = [
  [page.includes('图片工具箱'), 'image toolbox title'],
  [page.includes('图片压缩') && page.includes('格式转换') && page.includes('尺寸调整'), 'core image operations'],
  [page.includes('图片加水印') && page.includes('图片转 Base64'), 'watermark/base64 operations'],
  [page.includes('processImageBase64'), 'image API call'],
  [api.includes('/api/images/process-base64'), 'image API endpoint'],
  [pagesJson.includes('pages/image-toolbox/index'), 'image page route'],
  [home.includes("id: 'image-toolbox'") && home.includes('图片工具箱'), 'home entry']
]
for (const [ok, name] of checks) {
  if (!ok) throw new Error(`missing ${name}`)
}
console.log('image toolbox page checks passed')
