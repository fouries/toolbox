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

export interface CrudeOilItem {
  name?: string
  type?: string
  price?: string
  latestpri?: string
  unit?: string
  updown?: string
  time?: string
}

export interface NewsItem {
  title: string
  description?: string
  ctime?: string
  source?: string
  url?: string
  picUrl?: string
}

export interface NewsDetail {
  title: string
  source?: string
  publishTime?: string
  description?: string
  content: string
  sourceUrl: string
  cachedAt?: string
  fromCache?: boolean
}

export interface DailyBriefItem {
  rank: number
  title: string
  url?: string
  source?: string
}

export interface DailyBriefData {
  date?: string
  source?: string
  items: DailyBriefItem[]
}

export interface HotSearchItem {
  rank: number
  title: string
  hot?: string
  description?: string
  url?: string
}

export interface HotSearchData {
  platform: string
  title: string
  updateTime?: string
  items: HotSearchItem[]
}

export interface HotSearchDetailSection {
  title: string
  body: string
}

export interface HotSearchDetailData {
  platform: string
  keyword: string
  title: string
  hot?: string
  description?: string
  sourceUrl?: string
  summary: string
  content: string
  sections: HotSearchDetailSection[]
  relatedNews: NewsItem[]
  updatedAt?: string
}

export interface GoldPriceItem {
  name?: string
  type?: string
  price?: string
  latestpri?: string
  buypri?: string
  sellpri?: string
  unit?: string
  updown?: string
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

export interface ReverseLocationResult {
  province?: string
  city?: string
  district?: string
  country?: string
}

export interface ToolPopularityItem {
  id: string
  clicks: number
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

export const getCrudeOilPrice = () => {
  return request<CrudeOilItem[]>('/api/crude-oil')
}

export const getInfoNews = (category: string = 'internet') => {
  return request<NewsItem[]>(`/api/news?category=${encodeURIComponent(category)}`)
}

export const getNewsDetail = (url: string) => {
  return request<NewsDetail>(`/api/news/detail?url=${encodeURIComponent(url)}`, { timeout: 20000 })
}

export const getDailyBrief = () => {
  return request<DailyBriefData>('/api/daily-brief')
}

export const getHotSearch = (platform: string = 'weibo') => {
  return request<HotSearchData>(`/api/hot-search?platform=${encodeURIComponent(platform)}`)
}

export const getHotSearchDetail = (params: {
  platform?: string
  keyword: string
  hot?: string
  description?: string
  url?: string
}) => {
  const query = buildQueryString(params as Record<string, unknown>)
  return request<HotSearchDetailData>(`/api/hot-search/detail?${query}`, { timeout: 20000 })
}

export const getGoldPrice = () => {
  return request<GoldPriceItem[]>('/api/gold-price')
}

export const getWeather = (city: string = '北京') => {
  return request<WeatherItem[]>(`/api/weather?city=${encodeURIComponent(city)}`)
}

export const reverseLocation = (latitude: number, longitude: number) => {
  return request<ReverseLocationResult>(`/api/location/reverse?latitude=${latitude}&longitude=${longitude}`)
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

export const getPopularTools = (limit: number = 4) => {
  return request<ToolPopularityItem[]>(`/api/tools/popular?limit=${limit}`)
}

export const recordToolClick = (toolId: string) => {
  return request<ToolPopularityItem>('/api/tools/click', {
    method: 'POST',
    data: { tool_id: toolId }
  })
}

export default {
  getOilPrice,
  getCrudeOilPrice,
  getInfoNews,
  getNewsDetail,
  getGoldPrice,
  getWeather,
  reverseLocation,
  getCalendar,
  generateQrcode,
  generatePassword,
  base64Encode,
  base64Decode,
  urlEncode,
  urlDecode,
  getPopularTools,
  recordToolClick
}
