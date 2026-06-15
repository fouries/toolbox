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

      <view v-else>
        <view class="keyword-card card">
          <text class="keyword-label">热搜关键词</text>
          <text class="keyword-title">{{ hotKeyword }}</text>
          <view class="hot-image-section" v-if="displayImage">
            <image class="hot-image" :src="displayImage" mode="widthFix"></image>
          </view>
          <text class="keyword-desc" v-if="detail?.summary">{{ detail.summary }}</text>
          <view class="action-row">
            <button class="copy-btn" @tap="copyHotLink">复制{{ sourceUrl ? '原链接' : '关键词' }}</button>
          </view>
        </view>

        <view class="news-card card" v-if="relatedNews.length">
          <text class="news-title">相关资讯</text>
          <view class="news-list">
            <view class="news-item" v-for="(item, index) in relatedNews" :key="`${index}-${item.title}`" @tap="openNewsDetail(item)">
              <view class="news-main">
                <text class="news-item-title">{{ item.title }}</text>
                <view class="news-meta">
                  <text v-if="item.source">{{ item.source }}</text>
                  <text v-if="item.ctime">{{ item.ctime }}</text>
                  <text v-if="item.localUrl">已缓存正文</text>
                </view>
              </view>
              <text class="news-arrow">›</text>
            </view>
          </view>
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

const keyword = ref('')
const hot = ref('')
const description = ref('')
const sourceUrl = ref('')
const hotImage = ref('')
const rawHotData = ref('')
const loading = ref(false)
const error = ref('')
const detail = ref<HotSearchDetailData | null>(null)

const relatedNews = computed(() => detail.value?.relatedNews || [])

const decodeValue = (value: unknown) => {
  if (typeof value !== 'string') return ''
  try {
    return decodeURIComponent(value)
  } catch {
    return value
  }
}

const parseRawHotData = () => {
  if (!rawHotData.value) return null
  try {
    const parsed = JSON.parse(rawHotData.value)
    return parsed && typeof parsed === 'object' ? parsed as Record<string, unknown> : null
  } catch {
    return null
  }
}

const pickText = (record: Record<string, unknown> | null, keys: string[]) => {
  if (!record) return ''
  for (const key of keys) {
    const value = record[key]
    if (value !== undefined && value !== null && String(value).trim()) {
      return String(value).trim()
    }
  }
  return ''
}

const extractKeywordFromRaw = () => pickText(parseRawHotData(), ['keyword', 'word', 'hotword', 'title', 'query'])
const extractImageFromRaw = () => pickText(parseRawHotData(), ['image', 'img', 'pic', 'picUrl', 'avatar', 'cover'])

const hotKeyword = computed(() => detail.value?.keyword || keyword.value || extractKeywordFromRaw() || '未知热搜')
const displayImage = computed(() => hotImage.value || extractImageFromRaw())

const copyHotLink = () => {
  const data = sourceUrl.value || keyword.value
  if (!data) return
  uni.setClipboardData({ data })
  uni.showToast({ title: sourceUrl.value ? '原链接已复制' : '关键词已复制', icon: 'none' })
}

const openNewsDetail = (item: NewsItem) => {
  const safeUrl = item.url || sourceUrl.value || ''
  if (!safeUrl && !item.localUrl) {
    uni.showToast({ title: '暂无资讯链接', icon: 'none' })
    return
  }
  uni.navigateTo({ url: `/pages/news-detail/index?url=${encodeURIComponent(safeUrl)}&localUrl=${encodeURIComponent(item.localUrl || '')}` })
}

const loadDetail = async () => {
  if (!hotKeyword.value || hotKeyword.value === '未知热搜') {
    error.value = '缺少热搜关键词'
    return
  }
  keyword.value = hotKeyword.value
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
      sourceUrl.value = res.data.sourceUrl || sourceUrl.value
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
  keyword.value = decodeValue(options?.keyword || options?.title)
  hot.value = decodeValue(options?.hot)
  description.value = decodeValue(options?.description)
  sourceUrl.value = decodeValue(options?.url)
  hotImage.value = decodeValue(options?.image)
  rawHotData.value = decodeValue(options?.raw)
  if (!keyword.value) {
    keyword.value = extractKeywordFromRaw()
  }
  if (!hotImage.value) {
    hotImage.value = extractImageFromRaw()
  }
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
.news-card,
.error-box {
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid rgba(249, 115, 22, 0.14);
  box-shadow: 0 14rpx 38rpx rgba(194, 65, 12, 0.08);
}

.news-card {
  margin-top: 22rpx;
}

.keyword-label,
.keyword-title,
.keyword-desc,
.news-title,
.news-item-title,
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

.action-row {
  display: flex;
  margin-top: 24rpx;
}

.copy-btn,
.retry-btn {
  margin: 0;
  border: none;
  border-radius: 999rpx;
  background: #f97316;
  color: #fff;
  font-size: 25rpx;
  font-weight: 700;
}

.copy-btn {
  padding: 0 28rpx;
}

.news-title {
  color: #17233d;
  font-size: 30rpx;
  font-weight: 850;
}

.news-list {
  margin-top: 16rpx;
}

.news-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 20rpx 0;
  border-top: 1rpx solid #fed7aa;
}

.news-main {
  flex: 1;
  min-width: 0;
}

.news-item-title {
  color: #1e293b;
  font-size: 28rpx;
  font-weight: 760;
  line-height: 1.45;
}

.news-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 10rpx;
  color: #94a3b8;
  font-size: 22rpx;
}

.news-arrow {
  color: #fb923c;
  font-size: 44rpx;
  font-weight: 300;
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
