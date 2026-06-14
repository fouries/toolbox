<template>
  <view :class="['container', themeClass]">
    <view class="page-shell">
      <view class="page-header">
        <text class="title">⛽ 今日油价查询</text>
        <text class="subtitle">数据来源：发改委，每日更新</text>
      </view>

      <view class="location-row">
        <text class="location-hint">📍 当前定位：{{ locationLabel || selectedProvince }}</text>
        <button class="location-btn" @click="() => useCurrentLocation()" :disabled="loading || locating">
          {{ locating ? '定位中...' : '重新定位' }}
        </button>
      </view>
      <text v-if="locationNotice" class="location-notice">{{ locationNotice }}</text>

      <!-- 快捷省份标签 -->
      <text class="section-label">常用省份</text>
      <view class="quick-provinces">
        <text
          v-for="prov in quickProvinces"
          :key="prov"
          class="province-tag"
          :class="{ active: selectedProvince === prov }"
          @click="selectProvince(prov)"
        >{{ prov }}</text>
      </view>

      <!-- 省份选择器 -->
      <text class="section-label">更多省份</text>
      <view class="select-box">
        <picker mode="selector" :range="provinces" @change="onProvinceChange">
          <view class="picker">
            <view>
              <text class="picker-label">手动选择省份</text>
              <text class="picker-value">{{ selectedProvince }}</text>
            </view>
            <uni-icons type="right" size="16" color="#999"></uni-icons>
          </view>
        </picker>
      </view>

      <view class="loading" v-if="loading">
        <uni-icons type="spinner-cycle" size="40" color="#007aff"></uni-icons>
        <text class="loading-text">加载中...</text>
      </view>

      <view class="realtime-oil-card" v-if="oilData && !loading">
        <view class="realtime-card-top">
          <view>
            <text class="realtime-title">实时油价参考</text>
            <text class="realtime-subtitle">{{ selectedProvince }} 汽柴油参考价 · 每日更新，接口缓存约 1 小时</text>
          </view>
          <text class="oil-province-label">单位：元/升</text>
        </view>

        <view class="update-time">
          <text>更新时间: {{ oilUpdateText() }}</text>
        </view>

        <view class="oil-grid">
          <view class="oil-item">
            <view class="oil-icon" style="background: #ffe8e8;">92</view>
            <text class="oil-label">92# 汽油</text>
            <text class="oil-price">¥{{ oilData[0]?.p92 || '--' }}</text>
          </view>
          <view class="oil-item">
            <view class="oil-icon" style="background: #fff3e0;">95</view>
            <text class="oil-label">95# 汽油</text>
            <text class="oil-price">¥{{ oilData[0]?.p95 || '--' }}</text>
          </view>
          <view class="oil-item">
            <view class="oil-icon" style="background: #e8f5e9;">98</view>
            <text class="oil-label">98# 汽油</text>
            <text class="oil-price">¥{{ oilData[0]?.p98 || '--' }}</text>
          </view>
          <view class="oil-item">
            <view class="oil-icon" style="background: #e3f2fd;">0#</view>
            <text class="oil-label">0# 柴油</text>
            <text class="oil-price">¥{{ oilData[0]?.p0 || '--' }}</text>
          </view>
        </view>
      </view>

      <view class="crude-oil-card" v-if="crudeOilData.length && !loading">
        <view class="oil-card-header">
          <text class="oil-province-name">国际原油价格</text>
          <text class="oil-province-label">WTI / Brent 原油期货</text>
        </view>
        <view class="update-time crude-update-time">
          <text>更新时间: {{ crudeOilUpdateText() }}</text>
        </view>
        <view class="crude-grid">
          <view class="crude-item" v-for="item in crudeOilData" :key="item.name || item.type">
            <text class="crude-name">{{ formatCrudeName(item) }}</text>
            <text class="crude-price">{{ formatCrudePrice(item) }}</text>
            <text class="crude-meta">{{ item.updown || '行情参考' }}</text>
          </view>
        </view>
      </view>

      <view class="error-box" v-if="error">
        <text class="error-text">{{ error }}</text>
        <button class="retry-btn" @click="fetchOilPrice">重新加载</button>
      </view>

      <view class="note card">
        <text class="note-title">💡 说明</text>
        <text class="note-text">• 油价单位：元/升</text>
        <text class="note-text">• 实时油价参考来自成品油接口，通常每日更新，本服务缓存约 1 小时</text>
        <text class="note-text">• 原油价格展示 WTI 原油、Brent 原油等国际原油期货行情参考</text>
        <text class="note-text">• 实际价格以加油站为准</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useTheme } from '@/utils/theme'
import { ref, onMounted } from 'vue'
import { getCrudeOilPrice, getOilPrice, type CrudeOilItem, type OilPriceItem } from '@/api'
import { getCurrentAddress } from '@/utils/location'
import { resolveProvince } from '@/utils/location-format'

const { themeClass } = useTheme()
const loading = ref(false)
const locating = ref(false)
const error = ref('')
const locationLabel = ref('')
const locationNotice = ref('')
const oilData = ref<OilPriceItem[]>([])
const crudeOilData = ref<CrudeOilItem[]>([])
const selectedProvince = ref('北京')

const quickProvinces = ['北京', '上海', '天津', '广东', '江苏', '浙江', '山东', '四川']

const provinces = ref([
  '北京', '上海', '天津', '广东', '江苏', '浙江', '山东', '四川', '河南', '湖北', '湖南',
  '河北', '福建', '安徽', '辽宁', '江西', '重庆', '陕西', '云南', '广西', '山西',
  '贵州', '黑龙江', '吉林', '甘肃', '内蒙古', '新疆', '海南', '宁夏', '青海', '西藏'
])

const selectProvince = (prov: string) => {
  selectedProvince.value = prov
  locationLabel.value = ''
  locationNotice.value = ''
  fetchOilPrice()
}

const useCurrentLocation = async (options: { initial?: boolean } = {}) => {
  locating.value = true
  error.value = ''
  locationNotice.value = ''
  try {
    const address = await getCurrentAddress()
    const province = resolveProvince(address.province, provinces.value)
    if (!province) {
      throw new Error('未能识别当前位置所在省份')
    }
    selectedProvince.value = province
    locationLabel.value = address.label || province
    await fetchOilPrice()
  } catch (err: any) {
    const message = err.message || '定位失败，请手动选择省份'
    if (options.initial) {
      locationNotice.value = `${message}，已展示默认地区，可手动选择省份`
      uni.showToast({ title: '定位失败，已展示默认地区', icon: 'none' })
      await fetchOilPrice()
    } else {
      locationNotice.value = message
      uni.showToast({ title: message, icon: 'none' })
    }
  } finally {
    locating.value = false
  }
}

const onProvinceChange = (e: any) => {
  selectedProvince.value = provinces.value[e.detail.value]
  locationLabel.value = ''
  locationNotice.value = ''
  fetchOilPrice()
}

const fetchOilPrice = async () => {
  loading.value = true
  error.value = ''

  try {
    const oilRes: any = await getOilPrice(selectedProvince.value)
    if (oilRes.code === 200 && oilRes.newslist) {
      oilData.value = oilRes.newslist
    } else if (oilRes.newslist?.[0]?.note) {
      error.value = '请先配置天行数据 API Key'
    } else {
      error.value = oilRes.msg || '查询失败'
    }
  } catch (e: any) {
    error.value = e.message || '网络错误'
  } finally {
    loading.value = false
  }

  try {
    const crudeRes: any = await getCrudeOilPrice()
    if (crudeRes.code === 200 && Array.isArray(crudeRes.newslist)) {
      crudeOilData.value = crudeRes.newslist
    } else {
      crudeOilData.value = []
    }
  } catch (e) {
    crudeOilData.value = []
  }
}

const oilUpdateText = () => {
  return oilData.value[0]?.time || '接口未返回具体时间（每日更新）'
}

const crudeOilUpdateText = () => {
  return crudeOilData.value.find(item => item.time)?.time || '接口未返回具体时间（行情参考）'
}

const formatCrudeName = (item: CrudeOilItem) => {
  const raw = `${item.type || ''} ${item.name || ''}`.toLowerCase()
  if (raw.includes('wti')) return 'WTI 原油'
  if (raw.includes('brent') || raw.includes('blt') || raw.includes('布伦特')) return 'Brent 原油'
  return item.type ? `${String(item.type).toUpperCase()} 原油` : '原油'
}

const formatCrudePrice = (item: CrudeOilItem) => {
  const price = item.price || item.latestpri || '--'
  return item.unit ? `${price} ${item.unit}` : `${price}`
}

const initOilPricePage = async () => {
  await useCurrentLocation({ initial: true })
}

onMounted(() => {
  initOilPricePage()
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  background: linear-gradient(180deg, #e3f2fd 0%, #f5f5f5 100%);
  padding: 30rpx;
}

.location-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  margin: 0 4rpx 22rpx;
}

.location-hint,
.location-notice,
.section-label,
.picker-label,
.picker-value {
  display: block;
}

.location-hint {
  font-size: 24rpx;
  color: #667085;
  flex: 1;
  min-width: 0;
  line-height: 1.5;
}

.location-notice {
  margin: 0 0 20rpx 4rpx;
  font-size: 24rpx;
  color: #f59e0b;
  line-height: 1.5;
}

.location-btn {
  min-width: 148rpx;
  height: 58rpx;
  line-height: 58rpx;
  border-radius: 999rpx;
  background: #007aff;
  color: #fff;
  font-size: 24rpx;
  border: none;
  padding: 0;
  flex-shrink: 0;
}

.location-btn[disabled] {
  opacity: 0.65;
}

.section-label {
  font-size: 24rpx;
  color: #667085;
  margin: 0 0 14rpx 4rpx;
  font-weight: 600;
}

.quick-provinces {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.province-tag {
  padding: 12rpx 24rpx;
  background: rgba(255, 255, 255, 0.88);
  border-radius: 999rpx;
  font-size: 24rpx;
  color: #667085;
  border: 2rpx solid #eef2f7;
}

.province-tag.active {
  background: #007aff;
  color: #fff;
  border-color: #007aff;
}

.select-box {
  background: #fff;
  border-radius: var(--radius-md);
  padding: 25rpx 30rpx;
  margin-bottom: 30rpx;
}

.picker {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #333;
}

.picker-label {
  font-size: 24rpx;
  color: #98a2b3;
  margin-bottom: 6rpx;
}

.picker-value {
  font-size: 30rpx;
  color: #243044;
  font-weight: 600;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 0;
}

.loading-text {
  margin-top: 20rpx;
  font-size: 26rpx;
  color: #999;
}

.realtime-oil-card,
.crude-oil-card {
  background: #fff;
  border-radius: var(--radius-md);
  padding: 30rpx;
  margin-bottom: 30rpx;
}

.update-time {
  text-align: center;
  font-size: 24rpx;
  color: #999;
  margin-bottom: 24rpx;
}

.crude-update-time {
  margin-top: -12rpx;
  text-align: left;
}

.realtime-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 18rpx;
}

.realtime-title,
.realtime-subtitle {
  display: block;
}

.realtime-title {
  font-size: 36rpx;
  font-weight: 800;
  color: #172033;
}

.realtime-subtitle {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #667085;
}

.oil-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30rpx;
}

.oil-province-name {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}

.oil-province-label {
  font-size: 22rpx;
  color: #999;
}

.oil-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
}

.oil-item {
  background: #f8f9fa;
  border-radius: 18rpx;
  padding: 30rpx 20rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.oil-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 800;
  color: #333;
  margin-bottom: 16rpx;
}

.oil-label {
  font-size: 24rpx;
  color: #667085;
  margin-bottom: 10rpx;
}

.oil-price {
  font-size: 40rpx;
  font-weight: 800;
  color: #007aff;
}

.crude-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18rpx;
}

.crude-item {
  padding: 24rpx;
  border-radius: 20rpx;
  background: linear-gradient(135deg, #f8fafc 0%, #eff6ff 100%);
  border: 1rpx solid #e2e8f0;
}

.crude-name,
.crude-price,
.crude-meta {
  display: block;
}

.crude-name {
  color: #334155;
  font-size: 26rpx;
  font-weight: 700;
}

.crude-price {
  margin-top: 12rpx;
  color: #0f172a;
  font-size: 36rpx;
  font-weight: 850;
}

.crude-meta {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 22rpx;
}

.error-box {
  background: #fff;
  border-radius: var(--radius-md);
  padding: 60rpx 30rpx;
  text-align: center;
}

.error-text {
  display: block;
  font-size: 28rpx;
  color: #ff6b6b;
  margin-bottom: 30rpx;
}

.retry-btn {
  background: #007aff;
  color: #fff;
  border: none;
  border-radius: 50rpx;
  font-size: 28rpx;
  width: 280rpx;
}

.note-title {
  display: block;
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
  margin-bottom: 15rpx;
}

.note-text {
  display: block;
  font-size: 24rpx;
  color: #667085;
  line-height: 1.8;
}

@media (min-width: 768px) {
  .oil-grid,
  .crude-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
</style>