<template>
  <view class="container">
    <view class="search-section">
      <view class="search-box">
        <input 
          v-model="city" 
          placeholder="输入城市名称（如：北京、上海）"
          class="search-input"
          @confirm="fetchWeather"
        />
        <button class="search-btn" @click="fetchWeather">查询</button>
      </view>
      
      <view class="hot-cities">
        <text class="hot-label">热门城市:</text>
        <view class="city-tags">
          <text 
            v-for="c in hotCities" 
            :key="c" 
            class="city-tag"
            :class="{ active: city === c }"
            @click="selectCity(c)"
          >{{ c }}</text>
        </view>
      </view>
    </view>

    <view v-if="loading" class="loading">
      <text>加载中...</text>
    </view>

    <view v-else-if="weatherData" class="weather-card">
      <!-- 主要天气信息 -->
      <view class="weather-main">
        <view class="city-info">
          <text class="city-name">{{ weatherData.area || city }}</text>
          <text class="update-time">{{ weatherData.date }} {{ weatherData.week }}</text>
        </view>
        <view class="weather-icon">
          <text class="temp">{{ formatTemp(weatherData.real) }}</text>
          <text class="weather">{{ weatherData.weather }}</text>
        </view>
      </view>

      <!-- 详细信息 -->
      <view class="weather-details">
        <view class="detail-item">
          <text class="detail-label">🌡️ 温度范围</text>
          <text class="detail-value">{{ formatTemp(weatherData.lowest) }} ~ {{ formatTemp(weatherData.highest) }}</text>
        </view>
        <view class="detail-item">
          <text class="detail-label">💨 风向风力</text>
          <text class="detail-value">{{ weatherData.wind }} {{ weatherData.windsc }}</text>
        </view>
        <view class="detail-item">
          <text class="detail-label">💧 湿度</text>
          <text class="detail-value">{{ weatherData.humidity }}%</text>
        </view>
        <view class="detail-item">
          <text class="detail-label">🌅 日出</text>
          <text class="detail-value">{{ weatherData.sunrise }}</text>
        </view>
        <view class="detail-item">
          <text class="detail-label">🌇 日落</text>
          <text class="detail-value">{{ weatherData.sunset }}</text>
        </view>
        <view class="detail-item">
          <text class="detail-label">☀️ 紫外线</text>
          <text class="detail-value">{{ getUvLevel(weatherData.uv_index) }}</text>
        </view>
      </view>

      <!-- 未来天气预报 -->
      <view v-if="forecastList.length > 1" class="forecast-section">
        <text class="forecast-title">📆 未来7天预报</text>
        <scroll-view class="forecast-scroll" scroll-x="true" show-scrollbar="false">
          <view class="forecast-list">
            <view 
              v-for="(item, index) in forecastList.slice(1)" 
              :key="index"
              class="forecast-item"
            >
              <text class="forecast-date">{{ item.date.slice(5) }}</text>
              <text class="forecast-week">{{ item.week }}</text>
              <text class="forecast-icon">{{ getWeatherIcon(item.weather) }}</text>
              <text class="forecast-weather">{{ item.weather }}</text>
              <text class="forecast-temp">{{ formatTemp(item.lowest) }} ~ {{ formatTemp(item.highest) }}</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 生活指数提示 -->
      <view v-if="weatherData.tips" class="tips-card">
        <text class="tips-title">💡 生活提示</text>
        <text class="tips-content">{{ weatherData.tips }}</text>
      </view>
    </view>

    <view v-else-if="errorMsg" class="error">
      <text>{{ errorMsg }}</text>
    </view>

    <view v-else class="placeholder">
      <text class="placeholder-icon">🌤️</text>
      <text class="placeholder-text">输入城市名称查询天气</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import api from '@/api'

const city = ref('北京')
const weatherData = ref<any>(null)
const forecastList = ref<any[]>([])
const loading = ref(false)
const errorMsg = ref('')

const hotCities = ['北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安']

const selectCity = (c: string) => {
  city.value = c
  fetchWeather()
}

const fetchWeather = async () => {
  if (!city.value.trim()) {
    errorMsg.value = '请输入城市名称'
    return
  }

  loading.value = true
  errorMsg.value = ''
  weatherData.value = null
  forecastList.value = []

  try {
    const res: any = await api.get('/weather', { city: city.value })
    console.log('天气响应:', res)
    
    if (res.code === 200 && res.newslist && res.newslist.length > 0) {
      forecastList.value = res.newslist
      weatherData.value = res.newslist[0]
      errorMsg.value = ''
    } else {
      errorMsg.value = res.msg || '查询失败，请检查城市名称是否正确'
    }
  } catch (err: any) {
    console.error('查询失败:', err)
    errorMsg.value = err.message || '网络错误，请稍后重试'
  } finally {
    loading.value = false
  }
}

const formatTemp = (temp: string) => {
  if (!temp) return '--'
  // 去掉℃符号，只保留数字
  return temp.replace('℃', '') + '°'
}

const getUvLevel = (index: string) => {
  const val = Number(index) || 0
  if (val <= 2) return '弱'
  if (val <= 5) return '中等'
  if (val <= 7) return '强'
  if (val <= 10) return '很强'
  return '极强'
}

const getWeatherIcon = (weather: string) => {
  if (!weather) return '☁️'
  if (weather.includes('晴')) return '☀️'
  if (weather.includes('云') || weather.includes('阴')) return '☁️'
  if (weather.includes('雨') && weather.includes('雷')) return '⛈️'
  if (weather.includes('雨')) return '🌧️'
  if (weather.includes('雪')) return '❄️'
  if (weather.includes('雾') || weather.includes('霾')) return '🌫️'
  if (weather.includes('风')) return '💨'
  return '🌤️'
}

// 页面加载时自动查询
fetchWeather()
</script>

<style lang="scss" scoped>
.container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 30rpx;
}

.search-section {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
}

.search-box {
  display: flex;
  gap: 20rpx;
  margin-bottom: 30rpx;
}

.search-input {
  flex: 1;
  height: 80rpx;
  padding: 0 30rpx;
  background: #f5f5f5;
  border-radius: 40rpx;
  font-size: 28rpx;
}

.search-btn {
  width: 140rpx;
  height: 80rpx;
  line-height: 80rpx;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 40rpx;
  font-size: 28rpx;
  border: none;
  padding: 0;
}

.hot-cities {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 20rpx;
}

.hot-label {
  font-size: 26rpx;
  color: #666;
}

.city-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 15rpx;
}

.city-tag {
  padding: 10rpx 25rpx;
  background: #f0f0f0;
  border-radius: 30rpx;
  font-size: 24rpx;
  color: #666;
  transition: all 0.3s;
}

.city-tag.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.loading, .placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100rpx 0;
  color: white;
}

.placeholder-icon {
  font-size: 120rpx;
  margin-bottom: 30rpx;
}

.placeholder-text {
  font-size: 28rpx;
  opacity: 0.8;
}

.weather-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 30rpx;
  overflow: hidden;
}

.weather-main {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 50rpx 40rpx;
  color: white;
}

.city-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40rpx;
}

.city-name {
  font-size: 40rpx;
  font-weight: bold;
}

.update-time {
  font-size: 24rpx;
  opacity: 0.8;
}

.weather-icon {
  display: flex;
  align-items: baseline;
  gap: 30rpx;
}

.temp {
  font-size: 120rpx;
  font-weight: 200;
  line-height: 1;
}

.weather {
  font-size: 36rpx;
  opacity: 0.9;
}

.weather-details {
  padding: 40rpx;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30rpx;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.detail-label {
  font-size: 24rpx;
  color: #999;
}

.detail-value {
  font-size: 30rpx;
  color: #333;
  font-weight: 500;
}

/* 未来预报 */
.forecast-section {
  padding: 0 40rpx 40rpx;
  border-top: 1px solid #eee;
}

.forecast-title {
  display: block;
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
  margin: 30rpx 0 20rpx;
}

.forecast-scroll {
  white-space: nowrap;
}

.forecast-list {
  display: flex;
  gap: 20rpx;
}

.forecast-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  padding: 20rpx;
  background: #f8f9fa;
  border-radius: 15rpx;
  min-width: 140rpx;
}

.forecast-date {
  font-size: 22rpx;
  color: #666;
}

.forecast-week {
  font-size: 20rpx;
  color: #999;
}

.forecast-icon {
  font-size: 40rpx;
  margin: 5rpx 0;
}

.forecast-weather {
  font-size: 22rpx;
  color: #333;
}

.forecast-temp {
  font-size: 20rpx;
  color: #666;
}

/* 生活提示 */
.tips-card {
  padding: 40rpx;
  border-top: 1px solid #eee;
}

.tips-title {
  display: block;
  font-size: 28rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
}

.tips-content {
  font-size: 26rpx;
  color: #666;
  line-height: 1.8;
}

.error {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20rpx;
  padding: 60rpx 40rpx;
  text-align: center;
}

.error text {
  display: block;
  color: #ff4757;
  font-size: 28rpx;
}
</style>
