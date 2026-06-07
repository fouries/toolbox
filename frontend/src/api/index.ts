// API 基础配置
// 自动适配环境：H5 用相对路径，小程序用完整域名
const BASE_URL = (() => {
  // #ifdef H5
  return ''
  // #endif

  // #ifdef MP-WEIXIN
  return 'https://quan1234.com'
  // #endif

  return ''
})()

export interface ApiResponse<T = unknown> {
  code: number
  msg?: string
  data?: T
  newslist?: T
}

export interface OilPriceItem {
  province: string
  p0: string
  p92: string
  p95: string
  p98: string
  time?: string
}

export interface WeatherItem {
  area?: string
  date?: string
  week?: string
  real?: string
  weather?: string
  lowest?: string
  highest?: string
  wind?: string
  windsc?: string
  humidity?: string
  sunrise?: string
  sunset?: string
  uv_index?: string
  tips?: string
}

export interface PasswordParams {
  length?: number
  upper?: boolean
  lower?: boolean
  number?: boolean
  symbol?: boolean
  excludeAmbiguous?: boolean
}

export interface PasswordResult {
  password: string
}

export interface QrcodeResult {
  base64: string
}

function buildQueryString(params: Record<string, unknown>): string {
  if (!params || Object.keys(params).length === 0) return ''

  const pairs: string[] = []
  for (const key in params) {
    if (Object.prototype.hasOwnProperty.call(params, key)) {
      const value = params[key]
      if (value !== undefined && value !== null && value !== '') {
        pairs.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
      }
    }
  }
  return pairs.join('&')
}

const request = async <T = unknown>(url: string, options: any = {}): Promise<ApiResponse<T>> => {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method: options.method || 'GET',
      data: options.data || {},
      timeout: options.timeout || 15000,
      header: {
        'Content-Type': 'application/json',
        ...(options.header || {})
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as ApiResponse<T>)
        } else {
          reject(new Error(`请求失败: ${res.statusCode}`))
        }
      },
      fail: (err) => {
        reject(new Error(err.errMsg || '网络请求失败'))
      }
    })
  })
}

export const getOilPrice = (province: string = '北京') => {
  return request<OilPriceItem[]>(`/api/oil-price?province=${encodeURIComponent(province)}`)
}

export const getWeather = (city: string = '北京') => {
  return request<WeatherItem[]>(`/api/weather?city=${encodeURIComponent(city)}`)
}

export const getCalendar = (date?: string) => {
  const url = date ? `/api/calendar?date=${encodeURIComponent(date)}` : '/api/calendar'
  return request(url)
}

export const generateQrcode = (text: string, size: number = 256) => {
  return request<QrcodeResult>(`/api/qrcode?text=${encodeURIComponent(text)}&size=${size}`)
}

export const generatePassword = (params: PasswordParams = {}) => {
  const query = buildQueryString(params as Record<string, unknown>)
  return request<PasswordResult>(query ? `/api/password?${query}` : '/api/password')
}

export const base64Encode = (text: string) => {
  return request(`/api/base64/encode?text=${encodeURIComponent(text)}`)
}

export const base64Decode = (encoded: string) => {
  return request(`/api/base64/decode?encoded=${encodeURIComponent(encoded)}`)
}

export const urlEncode = (text: string) => {
  return request(`/api/url/encode?text=${encodeURIComponent(text)}`)
}

export const urlDecode = (encoded: string) => {
  return request(`/api/url/decode?encoded=${encodeURIComponent(encoded)}`)
}

export default {
  getOilPrice,
  getWeather,
  getCalendar,
  generateQrcode,
  generatePassword,
  base64Encode,
  base64Decode,
  urlEncode,
  urlDecode
}
