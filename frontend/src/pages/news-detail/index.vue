<template>
  <view :class="['container', themeClass]">
    <view class="page-shell detail-shell">
      <view class="loading" v-if="loading">
        <text class="loading-icon">⏳</text>
        <text class="loading-text">正在提取新闻正文...</text>
      </view>

      <view class="error-box card" v-else-if="error">
        <text class="error-title">正文加载失败</text>
        <text class="error-text">{{ error }}</text>
        <button class="copy-btn" @tap="copyOriginalUrl">复制原文链接</button>
        <button class="retry-btn" @tap="loadDetail">重新加载</button>
      </view>

      <view class="article-card card" v-else-if="detail">
        <text class="article-title">{{ detail.title }}</text>
        <view class="article-meta">
          <text v-if="detail.source">{{ detail.source }}</text>
          <text v-if="detail.publishTime">{{ detail.publishTime }}</text>
          <text v-if="detail.fromCache">已缓存</text>
        </view>
        <image class="article-image" :src="detail.image" mode="widthFix" v-if="detail.image"></image>
        <view class="article-content">
          <text class="article-paragraph" v-for="(paragraph, index) in paragraphs" :key="index">{{ paragraph }}</text>
        </view>
        <view class="article-actions">
          <button class="copy-btn" @tap="copyOriginalUrl">复制原文链接</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getNewsDetail, type NewsDetail } from '@/api'
import { useTheme } from '@/utils/theme'

const { themeClass } = useTheme()

const sourceUrl = ref('')
const localUrl = ref('')
const preferredImage = ref('')
const detail = ref<NewsDetail | null>(null)
const loading = ref(false)
const error = ref('')

const paragraphs = computed(() => {
  const content = detail.value?.content || ''
  return content
    .split(/\n+/)
    .map(item => item.trim())
    .filter(Boolean)
})

const copyOriginalUrl = () => {
  if (!sourceUrl.value) return
  uni.setClipboardData({ data: sourceUrl.value })
  uni.showToast({ title: '原文链接已复制', icon: 'none' })
}

const loadDetail = async () => {
  if (!sourceUrl.value && !localUrl.value) {
    error.value = '缺少新闻链接'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const res = await getNewsDetail(sourceUrl.value, localUrl.value, preferredImage.value)
    if (res.code === 200 && res.data) {
      detail.value = res.data
    } else {
      detail.value = null
      error.value = res.msg || '未能提取新闻正文'
    }
  } catch (err: any) {
    detail.value = null
    error.value = err.message || '网络请求失败'
  } finally {
    loading.value = false
  }
}

onLoad((options: any) => {
  sourceUrl.value = decodeURIComponent(options?.url || '')
  localUrl.value = decodeURIComponent(options?.localUrl || '')
  preferredImage.value = decodeURIComponent(options?.image || '')
  loadDetail()
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 30rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #eff6ff 0%, #f8fafc 50%, #ffffff 100%);
}

.detail-shell {
  max-width: 900px;
}

.article-card,
.error-box {
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid rgba(37, 99, 235, 0.12);
  box-shadow: 0 14rpx 38rpx rgba(30, 64, 175, 0.08);
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 100rpx 0;
  color: #64748b;
}

.loading-icon,
.loading-text,
.article-title,
.article-desc,
.article-image,
.article-paragraph,
.error-title,
.error-text {
  display: block;
}

.loading-icon {
  font-size: 56rpx;
}

.loading-text {
  margin-top: 18rpx;
  font-size: 26rpx;
}

.article-title {
  color: #17233d;
  font-size: 38rpx;
  font-weight: 820;
  line-height: 1.45;
}

.article-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-top: 18rpx;
  color: #94a3b8;
  font-size: 23rpx;
}

.article-image {
  width: 100%;
  margin-top: 24rpx;
  border-radius: 22rpx;
  background: #eff6ff;
}

.article-desc {
  margin-top: 22rpx;
  padding: 20rpx;
  border-radius: 20rpx;
  color: #475569;
  font-size: 26rpx;
  line-height: 1.65;
  background: #f8fafc;
}

.article-content {
  margin-top: 28rpx;
}

.article-paragraph {
  margin-bottom: 24rpx;
  color: #334155;
  font-size: 30rpx;
  line-height: 1.82;
  text-align: justify;
}

.article-actions {
  margin-top: 30rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid #e2e8f0;
}

.error-box {
  text-align: center;
}

.error-title {
  color: #17233d;
  font-size: 34rpx;
  font-weight: 780;
}

.error-text {
  margin-top: 16rpx;
  color: #ef4444;
  font-size: 26rpx;
  line-height: 1.6;
}

.copy-btn,
.retry-btn {
  margin-top: 24rpx;
  border: none;
  border-radius: 999rpx;
  color: #fff;
  font-size: 26rpx;
  line-height: 2.5;
  background: linear-gradient(135deg, #2563eb, #06b6d4);
}

.retry-btn {
  background: #e2e8f0;
  color: #334155;
}
</style>
