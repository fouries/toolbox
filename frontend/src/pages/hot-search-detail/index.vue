<template>
  <view :class="['container', themeClass]">
    <view class="page-shell detail-shell">
      <view class="page-header detail-header">
        <text class="title">🔥 热搜详情</text>
        <text class="subtitle">{{ platformTitle }}</text>
      </view>

      <view class="loading" v-if="loading">
        <text class="loading-icon">⏳</text>
        <text class="loading-text">正在生成热搜内容...</text>
      </view>

      <view class="error-box card" v-else-if="error">
        <text class="error-text">{{ error }}</text>
        <button class="retry-btn" @tap="loadDetail">重新加载</button>
        <button class="copy-btn secondary" @tap="copyHotLink">复制{{ sourceUrl ? '原链接' : '关键词' }}</button>
      </view>

      <view v-else>
        <view class="keyword-card card">
          <view class="keyword-top">
            <text class="keyword-label">热搜关键词</text>
            <text class="platform-tag">{{ platformName }}</text>
          </view>
          <text class="keyword-title">{{ detail?.keyword || keyword || '未知热搜' }}</text>
          <view class="hot-image-section" v-if="hotImage">
            <image class="hot-image" :src="hotImage" mode="widthFix"></image>
          </view>
          <text class="keyword-desc" v-if="detail?.summary">{{ detail.summary }}</text>
          <view class="keyword-meta">
            <text v-if="detail?.hot || hot">热度：{{ detail?.hot || hot }}</text>
            <text v-if="detail?.updatedAt">更新：{{ detail.updatedAt }}</text>
            <text>{{ sourceUrl ? '可复制原热搜链接' : '可复制关键词' }}</text>
          </view>
          <view class="action-row">
            <button class="copy-btn" @tap="copyHotLink">复制{{ sourceUrl ? '原链接' : '关键词' }}</button>
          </view>
        </view>

        <view class="content-card card" v-if="detail?.sections?.length">
          <text class="content-title">热搜内容</text>
          <view class="content-section" v-for="section in detail.sections" :key="section.title">
            <text class="section-subtitle">{{ section.title }}</text>
            <text class="section-body">{{ section.body }}</text>
          </view>
        </view>

        <view class="section-header">
          <text class="section-title">相关资讯</text>
          <button class="refresh-btn" @tap="loadDetail" :disabled="loading">刷新</button>
        </view>

        <view class="news-list" v-if="relatedNews.length">
          <view class="news-card card" v-for="item in relatedNews" :key="item.title" @tap="openNewsDetail(item)">
            <view class="news-main">
              <text class="news-title">{{ item.title }}</text>
              <text class="news-desc" v-if="item.description">{{ item.description }}</text>
              <view class="news-meta">
                <text>{{ item.source || '资讯' }}</text>
                <text v-if="item.ctime">{{ item.ctime }}</text>
              </view>
            </view>
            <text class="news-arrow">›</text>
          </view>
        </view>

        <view class="empty-card card" v-else>
          <text class="empty-text">暂未匹配到相关资讯，可稍后刷新或复制原链接查看。</text>
        </view>

        <view class="note-card card">
          <text class="note-title">说明</text>
          <text class="note-text">小程序不能直接打开微博、百度等第三方搜索页，本页由后端按热搜词聚合站内资讯并生成摘要；需要查看原搜索结果时可复制原链接。</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useTheme } from '@/utils/theme'
import { getHotSearchDetail, type HotSearchDetailData, type NewsItem } from '@/api'

const { themeClass } = useTheme()

const platform = ref('weibo')
const platformTitle = ref('热搜榜')
const keyword = ref('')
const hot = ref('')
const description = ref('')
const sourceUrl = ref('')
const hotImage = ref('')
const rawHotData = ref('')
const loading = ref(false)
const error = ref('')
const detail = ref<HotSearchDetailData | null>(null)

const platformName = computed(() => platform.value === 'baidu' ? '百度热搜榜' : '微博热搜榜')
const relatedNews = computed(() => detail.value?.relatedNews || [])

const normalizeNewsUrl = (url?: string): string => {
  if (!url) return ''
  if (url.startsWith('//')) return `https:${url}`
  return url
}

const isSafeNewsUrl = (url?: string): url is string => {
  if (!url) return false
  return /^https?:\/\//i.test(url)
}

const copyHotLink = () => {
  const data = sourceUrl.value || keyword.value
  if (!data) return
  uni.setClipboardData({
    data,
    success: () => uni.showToast({ title: sourceUrl.value ? '原链接已复制' : '关键词已复制', icon: 'none' })
  })
}

const loadDetail = async () => {
  if (!keyword.value) {
    error.value = '缺少热搜关键词'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const res = await getHotSearchDetail({
      platform: platform.value,
      keyword: keyword.value,
      hot: hot.value,
      description: description.value,
      url: sourceUrl.value,
      raw: rawHotData.value
    })
    if (res.code === 200 && res.data) {
      detail.value = res.data
      sourceUrl.value = res.data.sourceUrl || sourceUrl.value
      hot.value = res.data.hot || hot.value
      description.value = res.data.description || description.value
    } else {
      detail.value = null
      error.value = res.msg || '热搜内容加载失败'
    }
  } catch (err: any) {
    detail.value = null
    error.value = err.message || '网络错误'
  } finally {
    loading.value = false
  }
}

const openNewsDetail = (item: NewsItem) => {
  const safeUrl = normalizeNewsUrl(item.url)
  if (!isSafeNewsUrl(safeUrl)) {
    uni.showToast({ title: '该资讯暂无可打开链接', icon: 'none' })
    return
  }
  uni.navigateTo({
    url: `/pages/news-detail/index?url=${encodeURIComponent(safeUrl)}`,
    fail: () => {
      uni.setClipboardData({ data: safeUrl })
      uni.showToast({ title: '链接已复制，请到浏览器打开', icon: 'none' })
    }
  })
}

onLoad((options: any) => {
  platform.value = decodeURIComponent(options?.platform || 'weibo')
  platformTitle.value = decodeURIComponent(options?.title || platformName.value)
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
.content-card,
.news-card,
.note-card,
.empty-card,
.error-box {
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid rgba(249, 115, 22, 0.14);
  box-shadow: 0 14rpx 38rpx rgba(194, 65, 12, 0.08);
}

.keyword-card,
.content-card {
  margin-bottom: 22rpx;
}

.keyword-top,
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.keyword-label,
.keyword-title,
.keyword-desc,
.note-title,
.note-text,
.loading-icon,
.loading-text,
.error-text,
.news-title,
.news-desc,
.section-title,
.content-title,
.section-subtitle,
.section-body,
.empty-text {
  display: block;
}

.keyword-label {
  color: #c2410c;
  font-size: 24rpx;
  font-weight: 700;
}

.platform-tag {
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: #ffedd5;
  color: #c2410c;
  font-size: 22rpx;
  font-weight: 700;
}

.keyword-title {
  margin-top: 18rpx;
  color: #17233d;
  font-size: 38rpx;
  font-weight: 850;
  line-height: 1.4;
}

.keyword-desc {
  margin-top: 12rpx;
  color: #475569;
  font-size: 26rpx;
  line-height: 1.7;
}

.keyword-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  margin-top: 16rpx;
  color: #94a3b8;
  font-size: 22rpx;
}

.action-row {
  margin-top: 22rpx;
}

.copy-btn,
.refresh-btn,
.retry-btn {
  margin: 0;
  border: none;
  border-radius: 999rpx;
  background: #f97316;
  color: #fff;
  font-size: 25rpx;
  font-weight: 700;
}

.copy-btn.secondary {
  margin-top: 18rpx;
  background: #fb923c;
}

.content-title {
  color: #7c2d12;
  font-size: 30rpx;
  font-weight: 820;
  margin-bottom: 18rpx;
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

.content-section + .content-section {
  margin-top: 20rpx;
  padding-top: 18rpx;
  border-top: 1rpx solid #ffedd5;
}

.section-subtitle {
  color: #c2410c;
  font-size: 27rpx;
  font-weight: 760;
}

.section-body {
  margin-top: 8rpx;
  color: #475569;
  font-size: 25rpx;
  line-height: 1.75;
}

.section-header {
  margin: 28rpx 0 18rpx;
}

.section-title {
  color: #7c2d12;
  font-size: 30rpx;
  font-weight: 800;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 70rpx 0;
  color: #f97316;
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

.news-desc {
  margin-top: 10rpx;
  color: #64748b;
  font-size: 24rpx;
  line-height: 1.65;
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
  color: #f97316;
  font-size: 46rpx;
}

.error-box,
.empty-card {
  text-align: center;
}

.error-text,
.empty-text {
  color: #ef4444;
  font-size: 26rpx;
  margin-bottom: 24rpx;
}

.empty-text {
  color: #64748b;
  margin-bottom: 0;
}

.note-card {
  margin-top: 22rpx;
}

.note-title {
  color: #7c2d12;
  font-size: 28rpx;
  font-weight: 760;
}

.note-text {
  margin-top: 8rpx;
  color: #c2410c;
  font-size: 24rpx;
  line-height: 1.65;
}

@media screen and (min-width: 768px) {
  .container {
    padding: 40px 24px 72px;
  }

  .keyword-card,
  .content-card,
  .news-card,
  .note-card,
  .empty-card,
  .error-box {
    padding: 28px;
  }
}
</style>
