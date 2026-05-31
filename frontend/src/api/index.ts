// API 基础配置
// 自动适配环境：H5用相对路径，小程序用完整域名
const BASE_URL = (() => {
  // #ifdef H5
  return ''  // H5环境用相对路径
  // #endif
  
  // #ifdef MP-WEIXIN
  return 'https://quan1234.com'  // 小程序环境用完整域名
  // #endif
  
  return ''
})()

// 手动构建查询字符串（兼容小程序环境）
function buildQueryString(params: any): string {
  if (!params || Object.keys(params).length === 0) return ''
  
  const pairs: string[] = []
  for (const key in params) {
    if (params.hasOwnProperty(key)) {
      const value = params[key]
      pairs.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    }
  }
  return pairs.join('&')
}

// 请求封装
const request = async (url: string, options: any = {}) => {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE_URL + url,
      method: options.method || 'GET',
      data: options.data || {},
      header: {
        'Content-Type': 'application/json',
        ...options.header
      },
      success: (res: any) => {
        if (res.statusCode === 200) {
          resolve(res.data)
        } else {
          reject(new Error(`请求失败: ${res.statusCode}`))
        }
      },
      fail: (err: any) => {
        console.error('API请求失败:', err)
        uni.showToast({
          title: '网络请求失败',
          icon: 'none'
        })
        reject(err)
      }
    })
  })
}

// 油价查询
export const getOilPrice = (province: string = '北京') => {
  return request(`/api/oil-price?province=${encodeURIComponent(province)}`)
}

// 天气预报
export const getWeather = (city: string = '北京') => {
  return request(`/api/weather?city=${encodeURIComponent(city)}`)
}

// 快递查询
export const getExpress = (no: string) => {
  return request(`/api/express?no=${encodeURIComponent(no)}`)
}

// 手机号归属地
export const getPhoneLocation = (phone: string) => {
  return request(`/api/phone?phone=${encodeURIComponent(phone)}`)
}

// 身份证查询
export const getIdcardInfo = (idcard: string) => {
  return request(`/api/idcard?idcard=${encodeURIComponent(idcard)}`)
}

// 黄历查询
export const getCalendar = (date?: string) => {
  const url = date ? `/api/calendar?date=${date}` : '/api/calendar'
  return request(url)
}

// 二维码生成
export const generateQrcode = (text: string, size: number = 256) => {
  return request(`/api/qrcode?text=${encodeURIComponent(text)}&size=${size}`)
}

// IP查询
export const getIpInfo = (ip?: string) => {
  const url = ip ? `/api/ip?ip=${encodeURIComponent(ip)}` : '/api/ip'
  return request(url)
}

// 生成密码
export const generatePassword = (params: any = {}) => {
  const query = buildQueryString(params)
  return request(`/api/password?${query}`)
}

// Base64编码
export const base64Encode = (text: string) => {
  return request(`/api/base64/encode?text=${encodeURIComponent(text)}`)
}

// Base64解码
export const base64Decode = (encoded: string) => {
  return request(`/api/base64/decode?encoded=${encodeURIComponent(encoded)}`)
}

// URL编码
export const urlEncode = (text: string) => {
  return request(`/api/url/encode?text=${encodeURIComponent(text)}`)
}

// URL解码
export const urlDecode = (encoded: string) => {
  return request(`/api/url/decode?encoded=${encodeURIComponent(encoded)}`)
}

export default {
  getOilPrice,
  getWeather,
  getExpress,
  getPhoneLocation,
  getIdcardInfo,
  getCalendar,
  generateQrcode,
  getIpInfo,
  generatePassword,
  base64Encode,
  base64Decode,
  urlEncode,
  urlDecode
}
