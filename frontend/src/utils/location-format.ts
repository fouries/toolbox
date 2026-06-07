export interface LocationAddress {
  province?: string
  city?: string
  district?: string
}

const DIRECT_CITIES = ['北京', '上海', '天津', '重庆']

export function normalizeProvince(value?: string): string {
  if (!value) return ''
  return value
    .trim()
    .replace(/特别行政区$/, '')
    .replace(/壮族自治区$/, '')
    .replace(/回族自治区$/, '')
    .replace(/维吾尔自治区$/, '')
    .replace(/自治区$/, '')
    .replace(/省$/, '')
    .replace(/市$/, '')
}

export function normalizeCity(value?: string): string {
  if (!value) return ''
  return value
    .trim()
    .replace(/地区$/, '')
    .replace(/盟$/, '')
    .replace(/(?:藏族|回族|蒙古族|土家族苗族|哈尼族彝族|傣族景颇族|傈僳族|朝鲜族|哈萨克|柯尔克孜|布依族苗族|苗族侗族|壮族苗族|傣族)自治州$/, '')
    .replace(/自治州$/, '')
    .replace(/市$/, '')
}

export function resolveProvince(rawProvince: string | undefined, provinces: string[]): string {
  const normalized = normalizeProvince(rawProvince)
  if (!normalized) return ''
  if (provinces.includes(normalized)) return normalized
  return provinces.find(item => normalized.includes(item) || item.includes(normalized)) || ''
}

export function formatLocationLabel(address: LocationAddress): string {
  const province = normalizeProvince(address.province)
  const city = normalizeCity(address.city)
  const parts = [province]
  if (city && !DIRECT_CITIES.includes(province) && city !== province) {
    parts.push(city)
  }
  return parts.filter(Boolean).join(' ')
}
