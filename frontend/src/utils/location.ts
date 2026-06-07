import { reverseLocation, type ApiResponse, type ReverseLocationResult } from '@/api'
import { formatLocationLabel } from '@/utils/location-format'

export interface LocatedAddress extends ReverseLocationResult {
  label: string
}

function requestDeviceLocation(): Promise<{ latitude: number; longitude: number }> {
  return new Promise((resolve, reject) => {
    uni.getLocation({
      type: 'wgs84',
      isHighAccuracy: true,
      success: (res) => {
        resolve({ latitude: res.latitude, longitude: res.longitude })
      },
      fail: (err) => {
        reject(new Error(normalizeLocationError(err?.errMsg || '定位失败')))
      }
    })
  })
}

function normalizeLocationError(message: string): string {
  if (message.includes('auth') || message.includes('authorize') || message.includes('denied') || message.includes('permission')) {
    return '定位权限未开启，请允许获取位置后重试'
  }
  if (message.includes('timeout')) {
    return '定位超时，请检查网络或 GPS 后重试'
  }
  return '定位失败，请允许获取位置或手动选择城市/省份'
}

export async function getCurrentAddress(): Promise<LocatedAddress> {
  const coords = await requestDeviceLocation()
  const res = await reverseLocation(coords.latitude, coords.longitude) as ApiResponse<ReverseLocationResult>
  if (res.code !== 200 || !res.data) {
    throw new Error(res.msg || '当前位置解析失败')
  }

  return {
    ...res.data,
    label: formatLocationLabel(res.data)
  }
}
