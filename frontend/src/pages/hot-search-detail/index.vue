<template>
  <view :class="['container', themeClass]">
    <view class="page-shell detail-shell">
      <view class="page-header detail-header">
        <text class="title">🔎 热搜详情</text>
        <text class="subtitle">百度热搜榜</text>
      </view>

      <view class="loading" v-if="loading">
        <text class="loading-icon">⏳</text>
        <text class="loading-text">正在加载热搜摘要...</text>
      </view>

      <view class="error-box card" v-else-if="error">
        <text class="error-text">{{ error }}</text>
        <button class="retry-btn" @tap="loadDetail">重新加载</button>
      </view>

      <view class="keyword-card card" v-else>
        <text class="keyword-label">热搜关键词</text>
        <text class="keyword-title">{{ detail?.keyword || keyword || '未知热搜' }}</text>
        <view class="hot-image-section" v-if="hotImage">
          <image class="hot-image" :src="hotImage" mode="widthFix"></image>
        </view>
        <text class="keyword-desc" v-if="detail?.summary">{{ detail.summary }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useTheme } from '@/utils/theme'
import { getHotSearchDetail, type HotSearchDetailData } from '@/api'

const { themeClass } = useTheme()

const keyword = ref('')
const hot = ref('')
const description = ref('')
const sourceUrl = ref('')
const hotImage = ref('')
const rawHotData = ref('')
const loading = ref(false)
const error = ref('')
const detail = ref<HotSearchDetailData | null>(null)

const loadDetail = async () => {
  if (!keyword.value) {
    error.value = '缺少热搜关键词'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const res = await getHotSearchDetail({
      platform: 'baidu',
      keyword: keyword.value,
      hot: hot.value,
      description: description.value,
      url: sourceUrl.value,
      raw: rawHotData.value
    })
    if (res.code === 200 && res.data) {
      detail.value = res.data
      hot.value = res.data.hot || hot.value
      description.value = res.data.description || description.value
    } else {
      detail.value = null
      error.value = res.msg || '热搜摘要加载失败'
    }
  } catch (err: any) {
    detail.value = null
    error.value = err.message || '网络错误'
  } finally {
    loading.value = false
  }
}

onLoad((options: any) => {
  keyword.value = decodeURIComponent(options?.keyword || '')
  hot.value = decodeURIComponent(options?.hot || '')
  description.value = decodeURIComponent(options?.description || '')
  sourceUrl.value = decodeURIComponent(options?.url || '')
  hotImage.value = decodeURIComponent(options?.image || '')
  rawHotData.value = decodeURIComponent(options?.raw || '')
  loadDetail()
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 30rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #fff7ed 0%, #f8fafc 48%, #ffffff 100%);
}

.detail-shell {
  max-width: 980px;
}

.detail-header {
  margin-bottom: 24rpx;
}

.keyword-card,
.error-box {
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid rgba(249, 115, 22, 0.14);
  box-shadow: 0 14rpx 38rpx rgba(194, 65, 12, 0.08);
}

.keyword-label,
.keyword-title,
.keyword-desc,
.loading-icon,
.loading-text,
.error-text {
  display: block;
}

.keyword-label {
  color: #c2410c;
  font-size: 24rpx;
  font-weight: 700;
}

.keyword-title {
  margin-top: 18rpx;
  color: #17233d;
  font-size: 38rpx;
  font-weight: 850;
  line-height: 1.4;
}

.hot-image-section {
  margin-top: 16rpx;
}

.hot-image {
  display: block;
  width: 100%;
  border-radius: 20rpx;
  background: #ffedd5;
}

.keyword-desc {
  margin-top: 18rpx;
  color: #475569;
  font-size: 28rpx;
  line-height: 1.75;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 0;
  color: #f97316;
}

.loading-icon {
  font-size: 54rpx;
}

.loading-text {
  margin-top: 18rpx;
  font-size: 26rpx;
}

.retry-btn {
  margin: 0 auto;
  border: none;
  border-radius: 999rpx;
  background: #f97316;
  color: #fff;
  font-size: 25rpx;
  font-weight: 700;
}

.error-box {
  text-align: center;
}

.error-text {
  margin-bottom: 18rpx;
  color: #dc2626;
  font-size: 26rpx;
}
</style>
