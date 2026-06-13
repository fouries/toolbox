import { readFileSync, existsSync } from 'node:fs'
import { join } from 'node:path'

const root = process.cwd()
const requiredFiles = [
  'index.html',
  'src/pages/index/index.vue',
  'public/robots.txt',
  'public/sitemap.xml',
  'public/weather.html',
  'public/oil-price.html',
  'public/qrcode.html',
  'public/password.html',
  'public/gold-price.html',
  'public/info-news.html',
  'public/solar-terms.html',
]

const expected = {
  'index.html': [
    '<title>小巧的工具箱_在线实用工具集合</title>',
    '<meta name="description"',
    '<meta name="keywords"',
    '<link rel="canonical" href="https://quan1234.com/"',
    '<meta property="og:title"',
    '<meta name="theme-color"',
  ],
  'src/pages/index/index.vue': [
    'hero-section',
    'main-panel',
    '@media (min-width: 768px)',
    'max-width: 1120px',
    'grid-template-columns: repeat(4, minmax(0, 1fr))',
    'empty-state',
    '清空搜索',
  ],
  'public/robots.txt': ['User-agent: *', 'Allow: /', 'Sitemap: https://quan1234.com/sitemap.xml'],
  'public/sitemap.xml': [
    '<loc>https://quan1234.com/</loc>',
    '<loc>https://quan1234.com/weather.html</loc>',
    '<loc>https://quan1234.com/oil-price.html</loc>',
    '<loc>https://quan1234.com/qrcode.html</loc>',
    '<loc>https://quan1234.com/password.html</loc>',
    '<loc>https://quan1234.com/gold-price.html</loc>',
    '<loc>https://quan1234.com/info-news.html</loc>',
    '<loc>https://quan1234.com/solar-terms.html</loc>',
  ],
  'public/weather.html': ['天气查询', '立即使用天气查询', 'https://quan1234.com/#/pages/weather/index', 'layout-grid', 'tool-preview', '@media (max-width: 720px)', 'application/ld+json', 'FAQPage'],
  'public/oil-price.html': ['油价查询', '立即使用油价查询', 'https://quan1234.com/#/pages/oil-price/index', 'layout-grid', 'tool-preview', '@media (max-width: 720px)', 'application/ld+json', 'FAQPage'],
  'public/qrcode.html': ['二维码生成器', '立即使用二维码生成器', 'https://quan1234.com/#/pages/qrcode/index', 'layout-grid', 'tool-preview', '@media (max-width: 720px)', 'application/ld+json', 'FAQPage'],
  'public/password.html': ['随机密码生成器', '立即使用密码生成器', 'https://quan1234.com/#/pages/password/index', 'layout-grid', 'tool-preview', '@media (max-width: 720px)', 'application/ld+json', 'FAQPage'],
  'public/solar-terms.html': ['二十四节气', '立即使用二十四节气', 'https://quan1234.com/#/pages/solar-terms/index', 'layout-grid', 'tool-preview', '@media (max-width: 720px)', 'application/ld+json'],
  'public/info-news.html': ['互联网资讯', '电竞资讯', '汽车新闻', '立即使用资讯查询', 'https://quan1234.com/#/pages/info-news/index?category=internet', 'layout-grid', 'tool-preview', '@media (max-width: 720px)', 'application/ld+json'],
  'public/gold-price.html': ['黄金行情', '立即使用黄金行情', 'https://quan1234.com/#/pages/gold-price/index', 'layout-grid', 'tool-preview', '@media (max-width: 720px)', 'application/ld+json'],
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
