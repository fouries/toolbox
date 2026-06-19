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
          <text v-if="detail.publishTime">{{ detail.publishTime }}</text>
          <text v-if="detail.fromCache">已缓存</text>
        </view>
        <image class="article-image" :src="detail.image" mode="widthFix" v-if="detail.image" @tap="previewImage(detail.image)"></image>
        <view class="article-content">
          <template v-for="(item, index) in paragraphs" :key="index">
            <text 
              v-if="item.type === 'text'"
              class="article-paragraph" 
              :class="{ 'special-note': isSpecialNote(item.content) }"
            >{{ item.content }}</text>
            <image 
              v-else-if="item.type === 'image'" 
              class="article-inline-image" 
              :src="item.url" 
              mode="widthFix"
              @tap="previewImage(item.url)"
            ></image>
          </template>
        </view>
        <view class="article-actions">
          <button class="copy-btn" @tap="copyOriginalUrl">复制原文链接</button>
        </view>

        <!-- 上一篇 / 下一篇导航 -->
        <view class="neighbor-navigation">
          <button 
            class="nav-btn prev-btn" 
            :disabled="!prevNews" 
            @tap="goPrev"
          >
            <text class="nav-arrow">‹</text>
            <text class="nav-text">{{ prevNews ? '上一篇' : '已经是第一篇' }}</text>
          </button>
          <button 
            class="nav-btn next-btn" 
            :disabled="!nextNews" 
            @tap="goNext"
          >
            <text class="nav-text">{{ nextNews ? '下一篇' : '已经是最后一篇' }}</text>
            <text class="nav-arrow">›</text>
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getNewsDetail, type NewsDetail, type NewsItem } from '@/api'
import { useTheme } from '@/utils/theme'

const { themeClass } = useTheme()

const sourceUrl = ref('')
const localUrl = ref('')
const preferredImage = ref('')
const category = ref('internet')  // 当前分类
const currentIndex = ref(-1)     // 当前在列表中的索引
const newsList = ref<NewsItem[]>([]) // 当前分类的新闻列表

const detail = ref<NewsDetail | null>(null)
const loading = ref(false)
const error = ref('')

// 计算上一篇/下一篇
const hasNeighbors = computed(() => newsList.value.length > 0)
const prevNews = computed(() => currentIndex.value > 0 ? newsList.value[currentIndex.value - 1] : null)
const nextNews = computed(() => currentIndex.value < newsList.value.length - 1 ? newsList.value[currentIndex.value + 1] : null)

const paragraphs = computed(() => {
  const content = detail.value?.content || ''
  const items = content
    .split(/\n+/)
    .map(item => item.trim())
    .filter(Boolean)
  
  // 解析段落和图片标记，返回混合数组 {type: 'text', content: string} | {type: 'image', url: string}
  const result: Array<{type: 'text', content: string} | {type: 'image', url: string}> = []
  const images = detail.value?.images || []
  
  for (const item of items) {
    const imageMatch = item.match(/^<!--IMAGE:(\d+)-->$/)
    if (imageMatch) {
      const idx = parseInt(imageMatch[1], 10)
      if (idx >= 0 && idx < images.length) {
        result.push({type: 'image', url: images[idx]})
      }
    } else {
      result.push({type: 'text', content: item})
    }
  }
  return result
})

const isSpecialNote = (paragraph: string) => {
  const p = paragraph.toLowerCase()
  return p.includes('特别说明') || p.includes('特别提示') || p.includes('声明') || p.includes('免责')
}

const copyOriginalUrl = () => {
  if (!sourceUrl.value) return
  uni.setClipboardData({ data: sourceUrl.value })
  uni.showToast({ title: '原文链接已复制', icon: 'none' })
}

const previewImage = (currentUrl: string) => {
  if (!detail.value?.images || detail.value.images.length === 0) {
    // 如果只有单张图片
    uni.previewImage({
      current: currentUrl,
      urls: currentUrl ? [currentUrl] : []
    })
  } else {
    // 多张图片，可以预览所有
    uni.previewImage({
      current: currentUrl,
      urls: detail.value.images
    })
  }
}

// 跳转到指定新闻
const navigateToNews = (item: NewsItem) => {
  const safeUrl = (item.url || '').startsWith('//') ? `https:${item.url}` : (item.url || '')
  if (!/^https?:\/\//i.test(safeUrl)) {
    uni.showToast({ title: '链接无效', icon: 'none' })
    return
  }
  const imageUrl = (item.picUrl || '').startsWith('//') ? `https:${item.picUrl}` : (item.picUrl || '')
  uni.redirectTo({
    url: `/pages/news-detail/index?url=${encodeURIComponent(safeUrl)}&category=${category.value}&index=${newsList.value.findIndex(n => n === item)}&image=${encodeURIComponent(imageUrl)}`
  })
}

const goPrev = () => {
  if (prevNews.value) {
    navigateToNews(prevNews.value)
  }
}

const goNext = () => {
  if (nextNews.value) {
    navigateToNews(nextNews.value)
  }
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
  // 获取分类和索引参数，用于上下篇跳转
  if (options?.category) {
    category.value = options.category as string
  }
  if (options?.index !== undefined) {
    currentIndex.value = parseInt(options.index, 10)
  }
  // 如果有分类，无论有没有索引，都加载新闻列表方便导航
  if (category.value) {
    fetchNewsList()
  }
  loadDetail()
})

// 获取当前分类的新闻列表
const fetchNewsList = async () => {
  try {
    const res: any = await getInfoNews(category.value)
    if (res.code === 200 && Array.isArray(res.newslist)) {
      newsList.value = res.newslist
    }
  } catch (err) {
    // 获取失败不影响主流程，只是不显示上下篇按钮
    console.error('Failed to fetch news list for navigation', err)
  }
}
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

.article-paragraph.special-note {
  color: #64748b;
  font-size: 28rpx;
  font-style: italic;
  background: #f1f5f9;
  padding: 16rpx 20rpx;
  border-radius: 12rpx;
}

.article-inline-image {
  width: 100%;
  margin: 24rpx 0;
  border-radius: 16rpx;
  background: #eff6ff;
  display: block;
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

/* 上一篇下一篇导航 */
.neighbor-navigation {
  margin-top: 36rpx;
  display: flex;
  gap: 24rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid #e2e8f0;
}

.nav-btn {
  flex: 1;
  border-radius: 16rpx;
  padding: 20rpx 16rpx;
  font-size: 26rpx;
  line-height: 1.5;
  border: 1rpx solid #e2e8f0;
  background: #f8fafc;
  color: #334155;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.nav-btn:disabled {
  opacity: 0.5;
  color: #94a3b8;
}

.nav-btn:not(:disabled):active {
  background: linear-gradient(135deg, #2563eb, #06b6d4);
  color: #fff;
}

.nav-arrow {
  font-size: 32rpx;
  font-weight: bold;
}

.nav-text {
  font-size: 26rpx;
}
</style>
