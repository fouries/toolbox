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

        <!-- 上一篇 / 下一篇导航 -->
        <view class="neighbor-navigation">
          <button 
            class="nav-btn prev-btn" 
            :disabled="!prevHot" 
            @tap="goPrev"
          >
            <text class="nav-arrow">‹</text>
            <text class="nav-text">{{ prevHot ? '上一篇' : '已经是第一篇' }}</text>
          </button>
          <button 
            class="nav-btn next-btn" 
            :disabled="!nextHot" 
            @tap="goNext"
          >
            <text class="nav-text">{{ nextHot ? '下一篇' : '已经是最后一篇' }}</text>
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
import { useTheme } from '@/utils/theme'
import { getHotSearchDetail, type HotSearchDetailData, type HotSearchItem } from '@/api'

// getCurrentPages 是全局可用的
declare function getCurrentPages(): any[];

const { themeClass } = useTheme()

const keyword = ref('')
const hot = ref('')
const description = ref('')
const sourceUrl = ref('')
const hotImage = ref('')
const rawHotData = ref('')
const currentIndex = ref(-1)     // 当前在热搜列表中的索引
const loading = ref(false)
const error = ref('')
const detail = ref<HotSearchDetailData | null>(null)

// 计算上一篇/下一篇
const hotList = ref<HotSearchItem[]>([])
const prevHot = computed(() => currentIndex.value > 0 ? hotList.value[currentIndex.value - 1] : null)
const nextHot = computed(() => currentIndex.value < hotList.value.length - 1 ? hotList.value[currentIndex.value + 1] : null)

const relatedNews = computed(() => detail.value?.relatedNews || [])

const decodeValue = (value: unknown) => {
  if (typeof value !== 'string') return ''
  try {
    // 多次解码，处理双重编码
    while (value.includes('%')) {
      value = decodeURIComponent(value)
    }
    return value
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

// 跳转到指定热搜
const navigateToHot = (item: HotSearchItem) => {
  if (!item.title) {
    uni.showToast({ title: '链接无效', icon: 'none' })
    return
  }
  // 直接跳转，索引已经正确，不用获取列表
  uni.redirectTo({
    url: `/pages/hot-search-detail/index?platform=baidu&title=百度热搜&keyword=${encodeURIComponent(item.title)}&hot=${encodeURIComponent(item.hot || '')}&description=${encodeURIComponent(item.description || '')}&url=${encodeURIComponent(item.url || '')}&image=${encodeURIComponent(item.image || '')}&index=${hotList.value.findIndex(n => n === item)}&raw=${encodeURIComponent(JSON.stringify(item.raw || item))}`
  })
}

const goPrev = () => {
  if (prevHot.value) {
    navigateToHot(prevHot.value)
  }
}

const goNext = () => {
  if (nextHot.value) {
    navigateToHot(nextHot.value)
  }
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
  // 获取索引参数，用于上下篇跳转
  if (options?.index !== undefined) {
    currentIndex.value = parseInt(decodeValue(options.index), 10)
  }
  // 获取热搜列表，尝试从内存/缓存获取
  // 1. 优先从页面栈获取
  const pages = getCurrentPages()
  console.log('[hot-nav] current pages length: ', pages.length)
  let gotList = false
  if (pages.length >= 2) {
    const prevPage = pages[pages.length - 2]
    console.log('[hot-nav] prevPage route: ', prevPage.route)
    let hotItemsData: any = null
    if (prevPage.vm && prevPage.vm.$setup && prevPage.vm.$setup.hotItems) {
      hotItemsData = prevPage.vm.$setup.hotItems
    } else if (prevPage.$vm && prevPage.$vm._setup && prevPage.$vm._setup.hotItems) {
      hotItemsData = prevPage.$vm._setup.hotItems
    } else if (prevPage.data && prevPage.data.hotItems) {
      hotItemsData = { value: prevPage.data.hotItems }
    }
    if (hotItemsData && Array.isArray(hotItemsData.value)) {
      hotList.value = hotItemsData.value
      gotList = true
    }
  }
  // 2. 如果从页面栈获取不到，尝试从uni.getStorageSync获取
  if (!gotList) {
    try {
      const cached = uni.getStorageSync('hot_search_current_list')
      if (Array.isArray(cached) && cached.length > 0) {
        hotList.value = cached
        gotList = true
        console.log('[hot-nav] 从缓存获取热搜列表成功, length=', hotList.value.length)
      }
    } catch (e) {
      console.warn('[hot-nav] read cache failed', e)
    }
  }
  // 修剪列表
  if (hotList.value.length > 21) {
    hotList.value = hotList.value.slice(0, 21)
  }
  if (gotList) {
    console.log('[hot-nav] 获取热搜列表成功, length=', hotList.value.length)
    // 如果索引不正确，根据当前keyword重新查找
    if (currentIndex.value === -1 || !hotList.value[currentIndex.value] || hotList.value[currentIndex.value].title !== keyword.value) {
      const foundIndex = hotList.value.findIndex(item => item.title === keyword.value)
      console.log('[hot-nav] 查找当前关键词索引: ', keyword.value, 'found=', foundIndex)
      if (foundIndex >= 0) {
        currentIndex.value = foundIndex
        console.log('[hot-nav] 更新索引到: ', foundIndex)
      }
    }
  } else {
    console.log('[hot-nav] 获取热搜列表失败')
  }
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

/* 上一篇下一篇导航 */
.neighbor-navigation {
  margin-top: 36rpx;
  display: flex;
  gap: 24rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid #fed7aa;
}

.nav-btn {
  flex: 1;
  border-radius: 16rpx;
  padding: 20rpx 16rpx;
  font-size: 26rpx;
  line-height: 1.5;
  border: 1rpx solid #e2e8f0;
  background: #fff7f2;
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
  background: linear-gradient(135deg, #f97316, #fb923c);
  color: #fff;
  border-color: transparent;
}

.nav-arrow {
  font-size: 32rpx;
  font-weight: bold;
}

.nav-text {
  font-size: 26rpx;
}
</style>
