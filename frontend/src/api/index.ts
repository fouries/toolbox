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
  localUrl?: string
  picUrl?: string
  image?: string
  images?: string[]
}

export interface NewsDetail {
  title: string
  source?: string
  publishTime?: string
  description?: string
  image?: string
  originalImage?: string
  content: string
  images?: string[]  // 所有图片URL列表（代理后）
  localUrl?: string
  localId?: string
  sourceUrl: string
  cachedAt?: string
  fromCache?: boolean
  fromLocal?: boolean
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
  image?: string
  url?: string
  raw?: Record<string, unknown>
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

export interface HotSearchVideo {
  url: string
  originalUrl?: string
  poster?: string
  title?: string
  sourceUrl?: string
  author?: string
  awemeId?: string
  likeCount?: string
  commentCount?: string
  shareCount?: string
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
  videos?: HotSearchVideo[]
  image?: string
  images?: string[]
  rawHotItem?: Record<string, unknown>
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

export interface UserIdentity {
  id: number
  user_key: string
  user_type: string
}

export interface FavoriteToolResult {
  tool_id: string
  favorited: boolean
}

export interface FeedbackResult {
  id: number
  category: string
  content: string
  contact?: string
  page?: string
  status: string
  created_at?: string
}

export interface ReminderSubscription {
  id: number
  reminder_type: string
  title: string
  reminder_time: string
  enabled: boolean
  wx_subscribe_enabled?: boolean
  has_wechat_template?: boolean
  created_at?: string
  updated_at?: string
}

export interface WechatSubscribeConfig {
  enabled: boolean
  templates: Record<string, string>
}

export interface DocumentConvertResult {
  filename: string
  media_type: string
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

export const getCrudeOilPrice = () => {
  return request<CrudeOilItem[]>('/api/crude-oil')
}

export const getInfoNews = (category: string = 'internet') => {
  return request<NewsItem[]>(`/api/news?category=${encodeURIComponent(category)}`)
}

export const getNewsDetail = (url: string, localUrl?: string, image?: string) => {
  const target = localUrl || `/api/news/detail?url=${encodeURIComponent(url)}${image ? `&image=${encodeURIComponent(image)}` : ''}`
  return request<NewsDetail>(target, { timeout: 20000 })
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
  raw?: string
}) => {
  const query = buildQueryString(params as Record<string, unknown>)
  return request<HotSearchDetailData>(`/api/hot-search/detail?${query}`, { timeout: 20000 })
}

export const getHotSearchDetailBasic = (params: {
  platform?: string
  keyword: string
  hot?: string
  description?: string
  url?: string
  raw?: string
}) => {
  const query = buildQueryString(params as Record<string, unknown>)
  return request<HotSearchDetailData>(`/api/hot-search/detail-basic?${query}`, { timeout: 8000 })
}

export const getHotSearchDetailMedia = (params: {
  platform?: string
  keyword: string
  hot?: string
  description?: string
  url?: string
  raw?: string
}) => {
  const query = buildQueryString(params as Record<string, unknown>)
  return request<HotSearchDetailData>(`/api/hot-search/detail-media?${query}`, { timeout: 20000 })
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

export const ensureAnonymousUser = (userKey: string) => {
  return request<UserIdentity>('/api/users/anonymous', {
    method: 'POST',
    data: { user_key: userKey }
  })
}

export const getUserFavorites = (userKey: string) => {
  return request<string[]>(`/api/users/favorites?user_key=${encodeURIComponent(userKey)}`)
}

export const addUserFavorite = (userKey: string, toolId: string) => {
  return request<FavoriteToolResult>('/api/users/favorites', {
    method: 'POST',
    data: { user_key: userKey, tool_id: toolId }
  })
}

export const removeUserFavorite = (userKey: string, toolId: string) => {
  return request<FavoriteToolResult>('/api/users/favorites', {
    method: 'DELETE',
    data: { user_key: userKey, tool_id: toolId }
  })
}

export const submitFeedback = (payload: {
  user_key: string
  category: string
  content: string
  contact?: string
  page?: string
}) => {
  return request<FeedbackResult>('/api/feedback', {
    method: 'POST',
    data: payload
  })
}

export const getFeedbackList = (userKey: string) => {
  return request<FeedbackResult[]>(`/api/feedback?user_key=${encodeURIComponent(userKey)}`)
}

export const getReminderSubscriptions = (userKey: string) => {
  return request<ReminderSubscription[]>(`/api/reminders?user_key=${encodeURIComponent(userKey)}`)
}

export const getWechatSubscribeConfig = () => {
  return request<WechatSubscribeConfig>('/api/wechat/subscribe-config')
}

export const bindWechatLogin = (payload: { user_key: string; code: string }) => {
  return request<{ bound: boolean }>('/api/wechat/login', {
    method: 'POST',
    data: payload
  })
}

export const saveReminderSubscription = (payload: {
  user_key: string
  reminder_type: string
  title: string
  reminder_time: string
  enabled: boolean
  wx_template_id?: string
  wx_subscribe_enabled?: boolean
}) => {
  return request<ReminderSubscription>('/api/reminders', {
    method: 'POST',
    data: payload
  })
}

export const disableReminderSubscription = (userKey: string, reminderType: string) => {
  return request<ReminderSubscription>('/api/reminders', {
    method: 'DELETE',
    data: { user_key: userKey, reminder_type: reminderType, title: '', reminder_time: '08:00', enabled: false }
  })
}

export const convertDocumentBase64 = (payload: {
  filename: string
  content_base64: string
  target_format: string
}) => {
  return request<DocumentConvertResult>('/api/documents/convert-base64', {
    method: 'POST',
    timeout: 60000,
    data: payload
  })
}

export const operatePdfBase64 = (payload: {
  operation: string
  files: Array<{ filename: string; content_base64: string }>
  pages?: string
  text?: string
  compression_level?: string
}) => {
  return request<DocumentConvertResult>('/api/documents/pdf-operation-base64', {
    method: 'POST',
    timeout: 60000,
    data: payload
  })
}

export const scanDocumentBase64 = (payload: {
  files: Array<{ filename: string; content_base64: string }>
  target_format: string
  title?: string
  mode?: string
}) => {
  return request<DocumentConvertResult>('/api/documents/scan-base64', {
    method: 'POST',
    timeout: 60000,
    data: payload
  })
}

export interface MediaConvertResult {
  filename?: string
  media_type?: string
  base64?: string
  text?: string
  language?: string
  duration?: number | null
}

export interface MediaTaskResult {
  task_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  message?: string
  operation?: string
  error?: string
  filename?: string
  media_type?: string
  download_url?: string
  text?: string
  language?: string
  duration?: number | null
}

export const createMediaTask = (payload: {
  operation: string
  files: Array<{ name: string; path?: string; raw?: File | Blob; file?: File | Blob; tempFilePath?: string }>
  options?: Record<string, unknown>
}) => {
  const formData = {
    operation: payload.operation,
    options: JSON.stringify(payload.options || {})
  }

  // #ifdef H5
  const body = new FormData()
  body.append('operation', formData.operation)
  body.append('options', formData.options)
  payload.files.forEach((item, index) => {
    const raw = item.file || item.raw
    if (raw instanceof Blob) body.append('files', raw, item.name || `media-${index}`)
  })
  return new Promise<ApiResponse<MediaTaskResult>>((resolve, reject) => {
    fetch(BASE_URL + '/api/media/tasks', { method: 'POST', body })
      .then(async response => {
        const data = await response.json()
        if (response.ok) resolve(data as ApiResponse<MediaTaskResult>)
        else reject(new Error(data?.msg || data?.detail || `请求失败: ${response.status}`))
      })
      .catch(error => reject(new Error(error?.message || '上传失败')))
  })
  // #endif

  // #ifdef MP-WEIXIN
  return new Promise<ApiResponse<MediaTaskResult>>(async (resolve, reject) => {
    try {
      const init = await request<MediaTaskResult>('/api/media/tasks/init', {
        method: 'POST',
        timeout: 15000,
        data: { operation: payload.operation, options: payload.options || {} }
      })
      const taskId = init.data?.task_id
      if (!taskId) throw new Error('任务初始化失败')
      for (const item of payload.files) {
        await new Promise<void>((uploadResolve, uploadReject) => {
          uni.uploadFile({
            url: BASE_URL + `/api/media/tasks/${encodeURIComponent(taskId)}/files`,
            filePath: item.path || item.tempFilePath || '',
            name: 'file',
            timeout: 180000,
            success: (res) => {
              if (res.statusCode >= 200 && res.statusCode < 300) uploadResolve()
              else uploadReject(new Error(`上传失败: ${res.statusCode}`))
            },
            fail: (error) => uploadReject(new Error(error.errMsg || '上传失败'))
          })
        })
      }
      const started = await request<MediaTaskResult>(`/api/media/tasks/${encodeURIComponent(taskId)}/start`, {
        method: 'POST',
        timeout: 15000
      })
      resolve(started)
    } catch (error: any) {
      reject(new Error(error?.message || '上传失败'))
    }
  })
  // #endif
}

export const createMediaUrlTask = (payload: {
  url: string
  target_format?: string
}) => {
  return request<MediaTaskResult>('/api/media/url-tasks', {
    method: 'POST',
    timeout: 15000,
    data: payload
  })
}

export const getMediaTask = (taskId: string) => {
  return request<MediaTaskResult>(`/api/media/tasks/${encodeURIComponent(taskId)}`, { timeout: 15000 })
}

export const getMediaTaskDownloadUrl = (downloadUrl: string) => {
  if (/^https?:\/\//.test(downloadUrl)) return downloadUrl
  return BASE_URL + downloadUrl
}

export const convertMediaBase64 = (payload: {
  operation: string
  files: Array<{ filename: string; content_base64: string }>
  options?: Record<string, unknown>
}) => {
  return request<MediaConvertResult>('/api/media/convert-base64', {
    method: 'POST',
    timeout: 180000,
    data: payload
  })
}

export const extractUrlAudioBase64 = (payload: {
  url: string
  target_format?: string
}) => {
  return request<MediaConvertResult>('/api/media/extract-url-audio', {
    method: 'POST',
    timeout: 180000,
    data: payload
  })
}


export interface ImageToolboxResult {
  filename?: string
  media_type?: string
  base64?: string
  text?: string
  size?: number
}

export const processImageBase64 = (payload: {
  filename: string
  content_base64: string
  operation: string
  options?: Record<string, unknown>
}) => {
  return request<ImageToolboxResult>('/api/images/process-base64', {
    method: 'POST',
    timeout: 60000,
    data: payload
  })
}

export const generateBarcode = (text: string, height: number = 120) => {
  return request<QrcodeResult>(`/api/barcode?text=${encodeURIComponent(text)}&height=${height}`)
}

export const getAdminFeedbackList = (params: { admin_key: string; status?: string; category?: string; limit?: number }) => {
  const query = buildQueryString({ status: params.status || '', category: params.category || '', limit: params.limit || 100 })
  return request<FeedbackResult[]>(`/api/admin/feedback?${query}`, {
    header: { 'X-Admin-Key': params.admin_key }
  })
}

export const updateAdminFeedbackStatus = (payload: { admin_key: string; feedback_id: number; status: string }) => {
  return request<FeedbackResult>(`/api/admin/feedback/${encodeURIComponent(String(payload.feedback_id))}`, {
    method: 'PATCH',
    header: { 'X-Admin-Key': payload.admin_key },
    data: { status: payload.status }
  })
}

export default {
  getOilPrice,
  getCrudeOilPrice,
  getInfoNews,
  getNewsDetail,
  getHotSearch,
  getHotSearchDetail,
  getHotSearchDetailBasic,
  getHotSearchDetailMedia,
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
  recordToolClick,
  ensureAnonymousUser,
  getUserFavorites,
  addUserFavorite,
  removeUserFavorite,
  submitFeedback,
  getFeedbackList,
  getReminderSubscriptions,
  saveReminderSubscription,
  disableReminderSubscription,
  convertDocumentBase64,
  operatePdfBase64,
  scanDocumentBase64,
  createMediaTask,
  createMediaUrlTask,
  getMediaTask,
  getMediaTaskDownloadUrl,
  convertMediaBase64,
  extractUrlAudioBase64,
  processImageBase64,
  generateBarcode,
  getAdminFeedbackList,
  updateAdminFeedbackStatus
}
