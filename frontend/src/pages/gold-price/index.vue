<template>
  <view :class="['container', themeClass]">
    <view class="page-shell gold-shell">
      <view class="page-header gold-header">
        <text class="title">🥇 黄金行情</text>
        <text class="subtitle">查询黄金、足金、金条等行情参考价</text>
      </view>

      <view class="toolbar-card card">
        <view>
          <text class="toolbar-label">行情列表</text>
          <text class="toolbar-desc">数据仅供参考，交易以实际报价为准</text>
        </view>
        <button class="refresh-btn" @tap="fetchGoldPrice" :disabled="loading">{{ loading ? '刷新中...' : '刷新行情' }}</button>
      </view>

      <view class="loading" v-if="loading">
        <text class="loading-icon">⏳</text>
        <text class="loading-text">正在加载黄金行情...</text>
      </view>

      <view class="error-box card" v-else-if="error">
        <text class="error-text">{{ error }}</text>
        <button class="retry-btn" @tap="fetchGoldPrice">重新加载</button>
      </view>

      <view class="gold-list" v-else>
        <view class="gold-card card" v-for="item in goldList" :key="item.name || item.type">
          <view class="gold-name-row">
            <text class="gold-name">{{ item.name || item.type || '黄金' }}</text>
            <text class="gold-tag">{{ item.unit || '元/克' }}</text>
          </view>
          <text class="gold-price">{{ formatPrice(item) }}</text>
          <view class="gold-meta">
            <text v-if="item.updown">涨跌：{{ item.updown }}</text>
            <text v-if="item.time">{{ item.time }}</text>
          </view>
        </view>
      </view>

      <view class="note-card card">
        <text class="note-title">风险提示</text>
        <text class="note-text">黄金价格会随国际市场、汇率、品牌工费波动，本页面只做查询参考，不构成投资建议。</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useTheme } from '@/utils/theme'
import { getGoldPrice, type GoldPriceItem } from '@/api'

const { themeClass } = useTheme()
const loading = ref(false)
const error = ref('')
const goldList = ref<GoldPriceItem[]>([])

const formatPrice = (item: GoldPriceItem) => {
  const price = item.price || item.latestpri || item.buypri || item.sellpri || '--'
  return String(price).startsWith('¥') ? String(price) : `¥${price}`
}

const fetchGoldPrice = async () => {
  loading.value = true
  error.value = ''
  try {
    const res: any = await getGoldPrice()
    if (res.code === 200 && Array.isArray(res.newslist)) {
      goldList.value = res.newslist
      if (!goldList.value.length) error.value = '暂无黄金行情数据'
    } else {
      error.value = res.msg || '黄金行情加载失败'
    }
  } catch (err: any) {
    error.value = err.message || '网络错误'
  } finally {
    loading.value = false
  }
}

onLoad(() => {
  fetchGoldPrice()
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 30rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #fffbeb 0%, #fefce8 48%, #ffffff 100%);
}

.gold-shell {
  max-width: 980px;
}

.gold-header {
  margin-bottom: 24rpx;
}

.toolbar-card,
.gold-card,
.note-card,
.error-box {
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid rgba(245, 158, 11, 0.16);
  box-shadow: 0 14rpx 38rpx rgba(146, 64, 14, 0.08);
}

.toolbar-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  margin-bottom: 22rpx;
}

.toolbar-label,
.toolbar-desc,
.gold-name,
.gold-price,
.note-title,
.note-text,
.loading-icon,
.loading-text,
.error-text {
  display: block;
}

.toolbar-label {
  color: #78350f;
  font-size: 32rpx;
  font-weight: 800;
}

.toolbar-desc {
  margin-top: 6rpx;
  color: #92400e;
  font-size: 23rpx;
}

.refresh-btn,
.retry-btn {
  margin: 0;
  border: none;
  border-radius: 999rpx;
  background: #f59e0b;
  color: #fff;
  font-size: 25rpx;
  font-weight: 700;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 0;
  color: #92400e;
}

.loading-icon {
  font-size: 54rpx;
}

.loading-text {
  margin-top: 18rpx;
  font-size: 26rpx;
}

.gold-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18rpx;
}

.gold-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.gold-name {
  color: #17233d;
  font-size: 30rpx;
  font-weight: 760;
}

.gold-tag {
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: #fef3c7;
  color: #92400e;
  font-size: 22rpx;
}

.gold-price {
  margin-top: 20rpx;
  color: #d97706;
  font-size: 46rpx;
  font-weight: 850;
}

.gold-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  margin-top: 14rpx;
  color: #94a3b8;
  font-size: 22rpx;
}

.error-box {
  text-align: center;
}

.error-text {
  color: #ef4444;
  font-size: 26rpx;
  margin-bottom: 24rpx;
}

.note-card {
  margin-top: 22rpx;
}

.note-title {
  color: #78350f;
  font-size: 28rpx;
  font-weight: 760;
}

.note-text {
  margin-top: 8rpx;
  color: #92400e;
  font-size: 24rpx;
  line-height: 1.65;
}

@media screen and (min-width: 768px) {
  .container {
    padding: 40px 24px 72px;
  }

  .toolbar-card,
  .gold-card,
  .note-card,
  .error-box {
    padding: 28px;
  }

  .gold-list {
    grid-template-columns: repeat(2, 1fr);
    gap: 18px;
  }
}
</style>
