<template>
  <view class="container">
    <view class="header">
      <text class="title">⛽ 今日油价查询</text>
      <text class="subtitle">数据来源：发改委，每日更新</text>
    </view>

    <!-- 省份选择 -->
    <view class="select-box">
      <picker mode="selector" :range="provinces" @change="onProvinceChange">
        <view class="picker">
          <text>{{ selectedProvince }}</text>
          <uni-icons type="right" size="16" color="#999"></uni-icons>
        </view>
      </picker>
    </view>

    <!-- 加载中 -->
    <view class="loading" v-if="loading">
      <uni-icons type="spinner-cycle" size="40" color="#007aff"></uni-icons>
      <text class="loading-text">加载中...</text>
    </view>

    <!-- 油价数据 -->
    <view class="oil-data" v-if="oilData && !loading">
      <view class="update-time">
        <text>更新时间: {{ oilData[0]?.time || '今日' }}</text>
      </view>

      <view class="oil-grid">
        <view class="oil-item" v-for="(item, index) in oilData" :key="index">
          <view class="oil-type">{{ item.province }}</view>
          <view class="oil-price-row">
            <view class="price-item">
              <text class="price-label">92#</text>
              <text class="price-value">¥{{ item.p92 }}</text>
            </view>
            <view class="price-item">
              <text class="price-label">95#</text>
              <text class="price-value">¥{{ item.p95 }}</text>
            </view>
            <view class="price-item">
              <text class="price-label">98#</text>
              <text class="price-value">¥{{ item.p98 }}</text>
            </view>
            <view class="price-item">
              <text class="price-label">0#柴油</text>
              <text class="price-value">¥{{ item.p0 }}</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 错误提示 -->
    <view class="error-box" v-if="error">
      <text class="error-text">{{ error }}</text>
      <button class="retry-btn" @click="fetchOilPrice">重新加载</button>
    </view>

    <!-- 说明 -->
    <view class="note">
      <text class="note-title">💡 说明</text>
      <text class="note-text">• 油价单位：元/升</text>
      <text class="note-text">• 数据每日凌晨更新</text>
      <text class="note-text">• 实际价格以加油站为准</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getOilPrice } from '@/api'

const loading = ref(false)
const error = ref('')
const oilData = ref<any[]>([])
const selectedProvince = ref('北京')

const provinces = ref([
  '北京', '上海', '广东', '江苏', '浙江', '山东', '四川', '河南', '湖北', '湖南',
  '河北', '福建', '安徽', '辽宁', '江西', '重庆', '陕西', '云南', '广西', '山西',
  '贵州', '黑龙江', '吉林', '甘肃', '内蒙古', '新疆', '海南', '宁夏', '青海', '西藏'
])

const onProvinceChange = (e: any) => {
  selectedProvince.value = provinces.value[e.detail.value]
  fetchOilPrice()
}

const fetchOilPrice = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const res: any = await getOilPrice(selectedProvince.value)
    if (res.code === 200 && res.newslist) {
      oilData.value = res.newslist
    } else if (res.newslist?.[0]?.note) {
      error.value = '请先配置天行数据API Key'
    } else {
      error.value = res.msg || '查询失败'
    }
  } catch (e: any) {
    error.value = e.message || '网络错误'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchOilPrice()
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  background: linear-gradient(180deg, #e3f2fd 0%, #f5f5f5 100%);
  padding: 30rpx;
}

.header {
  text-align: center;
  margin-bottom: 40rpx;
}

.title {
  display: block;
  font-size: 40rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 10rpx;
}

.subtitle {
  font-size: 24rpx;
  color: #999;
}

.select-box {
  background: #fff;
  border-radius: 20rpx;
  padding: 25rpx 30rpx;
  margin-bottom: 30rpx;
}

.picker {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 30rpx;
  color: #333;
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

.oil-data {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
}

.update-time {
  text-align: center;
  font-size: 24rpx;
  color: #999;
  margin-bottom: 30rpx;
}

.oil-grid {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.oil-item {
  background: #f8f9fa;
  border-radius: 15rpx;
  padding: 25rpx;
}

.oil-type {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 20rpx;
  text-align: center;
}

.oil-price-row {
  display: flex;
  justify-content: space-around;
}

.price-item {
  text-align: center;
}

.price-label {
  display: block;
  font-size: 24rpx;
  color: #999;
  margin-bottom: 8rpx;
}

.price-value {
  font-size: 36rpx;
  font-weight: bold;
  color: #007aff;
}

.error-box {
  background: #fff;
  border-radius: 20rpx;
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
}

.note {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
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
  color: #666;
  line-height: 1.8;
}
</style>
