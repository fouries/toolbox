import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import vm from 'node:vm'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const ts = require('typescript')

const sourcePath = path.resolve('src/utils/location-format.ts')
const source = fs.readFileSync(sourcePath, 'utf8')
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 }
}).outputText

const module = { exports: {} }
vm.runInNewContext(compiled, { module, exports: module.exports, require }, { filename: sourcePath })
const { normalizeProvince, normalizeCity, resolveProvince, formatLocationLabel } = module.exports

assert.equal(normalizeProvince('广东省'), '广东')
assert.equal(normalizeProvince('广西壮族自治区'), '广西')
assert.equal(normalizeProvince('内蒙古自治区'), '内蒙古')
assert.equal(normalizeProvince('新疆维吾尔自治区'), '新疆')
assert.equal(normalizeCity('深圳市'), '深圳')
assert.equal(normalizeCity('湘西土家族苗族自治州'), '湘西')
assert.equal(resolveProvince('广东省', ['北京', '广东']), '广东')
assert.equal(resolveProvince('天津市', ['北京', '天津', '广东']), '天津')
assert.equal(resolveProvince('未知省份', ['北京', '广东']), '')
assert.equal(formatLocationLabel({ province: '广东', city: '深圳', district: '南山' }), '广东 深圳 南山')
assert.equal(formatLocationLabel({ province: '北京', city: '北京' }), '北京')

console.log('location format utilities are valid')
