import { readFileSync, existsSync } from 'node:fs'
import { join } from 'node:path'

const root = process.cwd()
const requiredFiles = [
  'src/pages/index/index.vue',
  'public/robots.txt',
  'public/sitemap.xml',
  'public/weather.html',
  'public/oil-price.html',
  'public/qrcode.html',
  'public/password.html',
]

const expected = {
  'src/pages/index/index.vue': [
    'hero-section',
    'main-panel',
    '@media (min-width: 768px)',
    'max-width: 1120px',
    'grid-template-columns: repeat(4, minmax(0, 1fr))',
  ],
  'public/robots.txt': ['User-agent: *', 'Allow: /', 'Sitemap: https://quan1234.com/sitemap.xml'],
  'public/sitemap.xml': [
    '<loc>https://quan1234.com/</loc>',
    '<loc>https://quan1234.com/weather.html</loc>',
    '<loc>https://quan1234.com/oil-price.html</loc>',
    '<loc>https://quan1234.com/qrcode.html</loc>',
    '<loc>https://quan1234.com/password.html</loc>',
  ],
  'public/weather.html': ['天气查询', '立即使用天气查询', 'https://quan1234.com/#/pages/weather/index', 'layout-grid', 'tool-preview', '@media (max-width: 720px)'],
  'public/oil-price.html': ['油价查询', '立即使用油价查询', 'https://quan1234.com/#/pages/oil-price/index', 'layout-grid', 'tool-preview', '@media (max-width: 720px)'],
  'public/qrcode.html': ['二维码生成器', '立即使用二维码生成器', 'https://quan1234.com/#/pages/qrcode/index', 'layout-grid', 'tool-preview', '@media (max-width: 720px)'],
  'public/password.html': ['随机密码生成器', '立即使用密码生成器', 'https://quan1234.com/#/pages/password/index', 'layout-grid', 'tool-preview', '@media (max-width: 720px)'],
}

const forbidden = {
  'src/pages/index/index.vue': [
    'PC/移动双端适配',
    '查看 SEO 首页',
    '查看SEO首页',
    '>搜索工具<',
    '@click="focusSearch"',
    '适合电脑和手机访问',
    '常用在线工具入口',
    '搜索引擎友好',
    'seo-panel',
  ],
}

const errors = []
for (const file of requiredFiles) {
  const path = join(root, file)
  if (!existsSync(path)) {
    errors.push(`Missing ${file}`)
    continue
  }
  const content = readFileSync(path, 'utf8')
  for (const snippet of expected[file]) {
    if (!content.includes(snippet)) {
      errors.push(`${file} missing snippet: ${snippet}`)
    }
  }
  for (const snippet of forbidden[file] || []) {
    if (content.includes(snippet)) {
      errors.push(`${file} contains forbidden snippet: ${snippet}`)
    }
  }
}

if (errors.length) {
  console.error(errors.join('\n'))
  process.exit(1)
}

console.log('SEO static files are valid')
