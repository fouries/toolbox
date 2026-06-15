<template>
  <view :class="['container', themeClass]">
    <view class="page-shell info-shell">
      <view class="page-header info-header">
        <text class="title">{{ currentConfig.icon }} {{ currentConfig.title }}</text>
        <text class="subtitle">{{ currentConfig.desc }}</text>
      </view>

      <view class="category-tabs card">
        <view
          class="category-tab"
          :class="{ active: activeCategory === item.id }"
          v-for="item in categories"
          :key="item.id"
          @tap="switchCategory(item.id)"
        >
          <text class="tab-icon">{{ item.icon }}</text>
          <text class="tab-name">{{ item.title }}</text>
        </view>
      </view>

      <view class="loading" v-if="loading">
        <text class="loading-icon">⏳</text>
        <text class="loading-text">正在加载资讯...</text>
      </view>

      <view class="error-box card" v-else-if="error">
        <text class="error-text">{{ error }}</text>
        <button class="retry-btn" @tap="fetchNews">重新加载</button>
      </view>

      <view class="news-list" v-else>
        <view class="news-card card" v-for="item in newsList" :key="item.title" @tap="openNews(item)">
          <view class="news-main">
            <text class="news-title">{{ item.title }}</text>
            <view class="news-meta">
              <text>{{ item.source || currentConfig.title }}</text>
              <text v-if="item.ctime">{{ item.ctime }}</text>
            </view>
          </view>
          <text class="news-arrow">›</text>
        </view>
      </view>

      <view class="note-card card">
        <text class="note-title">说明</text>
        <text class="note-text">资讯来自聚合接口，点击条目可在支持的端打开原文；接口不可用时会展示备用资讯。</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useTheme } from '@/utils/theme'
import { getInfoNews, type NewsItem } from '@/api'

const { themeClass } = useTheme()

const categories = [
  { id: 'internet', title: '互联网资讯', icon: '🌐', desc: '关注互联网产品、AI、科技公司与行业动态' },
  { id: 'esports', title: '电竞资讯', icon: '🎮', desc: '查看电竞赛事、战队动态和游戏产业消息' },
  { id: 'auto', title: '汽车新闻', icon: '🚗', desc: '了解新车上市、行业政策和用车资讯' }
]

const activeCategory = ref('internet')
const loading = ref(false)
const error = ref('')
const newsList = ref<NewsItem[]>([])
const currentConfig = computed(() => categories.find(item => item.id === activeCategory.value) || categories[0])

const fetchNews = async () => {
  loading.value = true
  error.value = ''
  try {
    const res: any = await getInfoNews(activeCategory.value)
    if (res.code === 200 && Array.isArray(res.newslist)) {
      newsList.value = res.newslist
      if (!newsList.value.length) error.value = '暂无资讯数据'
    } else {
      error.value = res.msg || '资讯加载失败'
    }
  } catch (err: any) {
    error.value = err.message || '网络错误'
  } finally {
    loading.value = false
  }
}

const switchCategory = (category: string) => {
  activeCategory.value = category
  fetchNews()
}

const normalizeNewsUrl = (url?: string): string => {
  if (!url) return ''
  if (url.startsWith('//')) return `https:${url}`
  return url
}

const isSafeNewsUrl = (url?: string): url is string => {
  if (!url) return false
  return /^https?:\/\//i.test(url)
}

const openNews = (item: NewsItem) => {
  const safeUrl = normalizeNewsUrl(item.url)
  if (!isSafeNewsUrl(safeUrl)) return
  uni.navigateTo({
    url: `/pages/news-detail/index?url=${encodeURIComponent(safeUrl)}&image=${encodeURIComponent(item.picUrl || '')}`,
    fail: () => {
      uni.setClipboardData({ data: safeUrl })
      uni.showToast({ title: '链接已复制，请到浏览器打开', icon: 'none' })
    }
  })
}

onLoad((options: any) => {
  if (options?.category && categories.some(item => item.id === options.category)) {
    activeCategory.value = options.category
  }
  fetchNews()
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 30rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #eff6ff 0%, #f8fafc 48%, #ffffff 100%);
}

.info-shell {
  max-width: 980px;
}

.info-header {
  margin-bottom: 24rpx;
}

.category-tabs,
.news-card,
.note-card,
.error-box {
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid rgba(37, 99, 235, 0.12);
  box-shadow: 0 14rpx 38rpx rgba(30, 64, 175, 0.08);
}

.category-tabs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12rpx;
  margin-bottom: 22rpx;
}

.category-tab {
  padding: 18rpx 12rpx;
  border-radius: 22rpx;
  text-align: center;
  background: #f8fafc;
  border: 1rpx solid #e2e8f0;
}

.category-tab.active {
  color: #fff;
  background: linear-gradient(135deg, #2563eb, #06b6d4);
  border-color: transparent;
}

.tab-icon,
.tab-name,
.news-title,
.note-title,
.note-text,
.loading-icon,
.loading-text,
.error-text {
  display: block;
}

.tab-icon {
  font-size: 34rpx;
}

.tab-name {
  margin-top: 6rpx;
  font-size: 23rpx;
  font-weight: 700;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 0;
  color: #64748b;
}

.loading-icon {
  font-size: 54rpx;
}

.loading-text {
  margin-top: 18rpx;
  font-size: 26rpx;
}

.news-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18rpx;
}

.news-card {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.news-main {
  flex: 1;
  min-width: 0;
}

.news-title {
  color: #17233d;
  font-size: 30rpx;
  font-weight: 760;
  line-height: 1.45;
}

.news-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  margin-top: 14rpx;
  color: #94a3b8;
  font-size: 22rpx;
}

.news-arrow {
  color: #2563eb;
  font-size: 46rpx;
}

.error-box {
  text-align: center;
}

.error-text {
  color: #ef4444;
  font-size: 26rpx;
  margin-bottom: 24rpx;
}

.retry-btn {
  border: none;
  border-radius: 999rpx;
  background: #2563eb;
  color: #fff;
  font-size: 26rpx;
}

.note-card {
  margin-top: 22rpx;
}

.note-title {
  color: #1e3a8a;
  font-size: 28rpx;
  font-weight: 760;
}

.note-text {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 24rpx;
  line-height: 1.65;
}

@media screen and (min-width: 768px) {
  .container {
    padding: 40px 24px 72px;
  }

  .category-tabs,
  .news-card,
  .note-card,
  .error-box {
    padding: 28px;
  }

  .news-list {
    gap: 18px;
  }

  .news-title {
    font-size: 22px;
  }
}
</style>
