import { copyFileSync, mkdirSync, existsSync } from 'node:fs'
import { join } from 'node:path'

const root = process.cwd()
const sourceDir = join(root, 'public')
const outputDir = join(root, 'dist/build/h5')
const files = [
  'robots.txt',
  'sitemap.xml',
  'weather.html',
  'oil-price.html',
  'qrcode.html',
  'password.html',
  'calendar.html',
  'history-today.html',
  'gold-price.html',
  'info-news.html',
  'solar-terms.html',
]

if (!existsSync(outputDir)) {
  throw new Error(`H5 output directory not found: ${outputDir}`)
}

mkdirSync(outputDir, { recursive: true })
for (const file of files) {
  const source = join(sourceDir, file)
  const target = join(outputDir, file)
  if (!existsSync(source)) {
    throw new Error(`SEO source file not found: ${source}`)
  }
  copyFileSync(source, target)
  console.log(`Copied ${file}`)
}
