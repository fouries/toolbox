<template>
  <view :class="['container', themeClass]" @touchstart="onTouchStart" @touchend="onTouchEnd">
    <view class="page-shell detail-shell">
      <view class="page-header detail-header">
        <text class="title">{{ detailConfig.icon }} 热搜详情</text>
        <text class="subtitle">{{ detailConfig.title }}</text>
      </view>

      <view class="loading detail-loading-card card" v-if="loading">
        <view class="detail-loading-orbit">
          <view class="detail-loading-ring"></view>
          <text class="detail-loading-flame">🔥</text>
        </view>
        <view class="detail-loading-bars">
          <view class="detail-loading-bar detail-loading-bar-title"></view>
          <view class="detail-loading-bar detail-loading-bar-media"></view>
          <view class="detail-loading-bar"></view>
          <view class="detail-loading-bar detail-loading-bar-short"></view>
        </view>
      </view>

      <view class="error-box card" v-else-if="error">
        <text class="error-text">{{ error }}</text>
        <button class="retry-btn" @tap="loadDetail">重新加载</button>
      </view>

      <view v-else>
        <view class="keyword-card card">
          <view class="douyin-swipe-hint" v-if="platform === 'douyin' && hotList.length > 1">
            <text>上滑下一条，下滑上一条</text>
          </view>
          <text class="keyword-label">热搜关键词</text>
          <text class="keyword-title">{{ hotKeyword }}</text>
          <view class="video-section" v-if="hotVideos.length">
            <text class="video-title">相关视频</text>
            <view class="video-item" v-for="(video, index) in hotVideos" :key="`${index}-${video.url}`">
              <video
                :id="`douyin-hot-video-${index}`"
                class="hot-video"
                :src="video.url"
                :poster="video.poster || ''"
                :title="video.title || hotKeyword"
                controls
                show-fullscreen-btn
                show-center-play-btn
                enable-play-gesture
                enable-progress-gesture
                vslide-gesture-in-fullscreen
                object-fit="contain"
                @error="onVideoError"
                @fullscreenchange="onVideoFullscreenChange(index, $event)"
                @touchstart="onFullscreenVideoTouchStart(index, $event)"
                @touchend="onFullscreenVideoTouchEnd(index, $event)"
              ></video>
              <view class="video-meta" v-if="platform === 'douyin' || video.title || video.author || videoStats(video) || video.sourceUrl">
                <text class="video-desc" v-if="video.title">{{ video.title }}</text>
                <text class="video-author" v-if="video.author">@{{ video.author }}</text>
                <text class="video-stats" v-if="videoStats(video)">{{ videoStats(video) }}</text>
                <text class="video-proxy-note">{{ videoProxyNote }}</text>
                <view class="video-action-row">
                  <button class="video-fullscreen-btn" v-if="platform === 'douyin'" @tap.stop="openImmersiveVideo(index)">全屏播放</button>
                  <button class="video-source-btn" v-if="video.sourceUrl" @tap="openVideoSource(video.sourceUrl)">{{ videoSourceButtonText }}</button>
                </view>
              </view>
            </view>
          </view>
          <view class="hot-image-section" v-if="displayImage && !hotVideos.length">
            <image class="hot-image" :src="displayImage" mode="widthFix" @tap="previewHotImage(displayImage)"></image>
          </view>
          <view class="media-loading" v-if="mediaLoading && !hotVideos.length && !detailImage">
            <view class="media-loading-player">
              <view class="media-loading-wave media-loading-wave-a"></view>
              <view class="media-loading-wave media-loading-wave-b"></view>
              <view class="media-loading-wave media-loading-wave-c"></view>
            </view>
          </view>
          <text class="media-error" v-if="mediaError">{{ mediaError }}</text>
          <text class="keyword-desc" v-if="detail?.summary">{{ detail.summary }}</text>
          <view class="action-row">
            <button class="copy-btn" @tap="copyHotLink">复制{{ sourceUrl ? '原链接' : '关键词' }}</button>
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
import { computed, getCurrentInstance, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useTheme } from '@/utils/theme'
import { getHotSearchDetailBasic, getHotSearchDetailMedia, type HotSearchDetailData, type HotSearchItem, type HotSearchVideo } from '@/api'

// getCurrentPages 是全局可用的
declare function getCurrentPages(): any[];

const { themeClass } = useTheme()
const componentInstance = getCurrentInstance()

const getVideoContext = (index: number) => {
  const videoId = `douyin-hot-video-${index}`
  // 微信小程序里动态 id 的 video 在组件作用域内，传入当前实例可避免拿不到上下文。
  // H5 端不需要实例；保留 fallback 保证两端都可用。
  try {
    if (componentInstance?.proxy) {
      return uni.createVideoContext(videoId, componentInstance.proxy as any) as any
    }
  } catch {}
  return uni.createVideoContext(videoId) as any
}

const hotConfigs = {
  baidu: { title: '百度热搜榜', icon: '🔎' },
  douyin: { title: '抖音热搜榜', icon: '🎵' }
} as const

type HotPlatform = keyof typeof hotConfigs

const platform = ref<HotPlatform>('baidu')
const detailConfig = computed(() => hotConfigs[platform.value])
const videoSourceButtonText = computed(() => platform.value === 'douyin' ? '去抖音查看原视频' : '查看百度原视频')
const videoProxyNote = computed(() => platform.value === 'douyin' ? '视频按需代理播放，不下载保存' : '百度视频按需代理播放，不下载保存')
const keyword = ref('')
const hot = ref('')
const description = ref('')
const sourceUrl = ref('')
const hotImage = ref('')
const rawHotData = ref('')
const currentIndex = ref(-1)     // 当前在热搜列表中的索引
const loading = ref(false)
const mediaLoading = ref(false)
const error = ref('')
const mediaError = ref('')
const detail = ref<HotSearchDetailData | null>(null)

// 计算上一篇/下一篇
const hotList = ref<HotSearchItem[]>([])
const prevHot = computed(() => currentIndex.value > 0 ? hotList.value[currentIndex.value - 1] : null)
const nextHot = computed(() => currentIndex.value < hotList.value.length - 1 ? hotList.value[currentIndex.value + 1] : null)

const hotVideos = computed(() => (detail.value?.videos?.filter(item => item?.url) || []).slice(0, platform.value === 'douyin' ? 3 : 1))
const hasLoadedMedia = ref(false)
const shouldShowFallbackImage = computed(() => hasLoadedMedia.value && !mediaLoading.value)
const touchStartY = ref(0)
const touchStartX = ref(0)
const touchStartTime = ref(0)
const swipeNavigating = ref(false)
const fullscreenVideoIndex = ref(-1)

const decodeValue = (value: unknown): string => {
  if (typeof value !== 'string') return ''
  let decoded = value
  try {
    // 多次解码，处理双重编码
    while (decoded.includes('%')) {
      decoded = decodeURIComponent(decoded)
    }
    return decoded
  } catch {
    return decoded
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
const detailImage = computed(() => detail.value?.image || detail.value?.images?.[0] || '')
const displayImage = computed(() => detailImage.value || (shouldShowFallbackImage.value ? (hotImage.value || extractImageFromRaw()) : ''))

const previewHotImage = (currentUrl: string) => {
  const urls = detail.value?.images?.length ? detail.value.images : (currentUrl ? [currentUrl] : [])
  if (!urls.length) return
  uni.previewImage({ current: currentUrl, urls })
}

const detailParams = () => ({
  platform: platform.value,
  keyword: keyword.value,
  hot: hot.value,
  description: description.value,
  url: sourceUrl.value,
  raw: rawHotData.value
})

const applyDetail = (data: HotSearchDetailData) => {
  detail.value = data
  hot.value = data.hot || hot.value
  description.value = data.description || description.value
  sourceUrl.value = data.sourceUrl || sourceUrl.value
  if (!hotImage.value && (data.image || data.images?.[0])) {
    hotImage.value = data.image || data.images?.[0] || ''
  }
}

const onVideoError = () => {
  uni.showToast({ title: platform.value === 'douyin' ? '视频暂时无法播放，可复制原链接去抖音查看' : '视频暂时无法播放，可点击原链接查看', icon: 'none' })
}

const openImmersiveVideo = (index: number) => {
  if (platform.value !== 'douyin') return
  if (!hotVideos.value[index]?.url) {
    uni.showToast({ title: '视频暂时不可播放', icon: 'none' })
    return
  }
  resetSwipeTouch()
  swipeNavigating.value = false
  fullscreenVideoIndex.value = index
  const context = getVideoContext(index)
  if (context?.requestFullScreen) {
    context.requestFullScreen({
      direction: 0,
      fail: () => {
        fullscreenVideoIndex.value = -1
        uni.showToast({ title: '当前环境不支持全屏播放', icon: 'none' })
      }
    })
    return
  }
  fullscreenVideoIndex.value = -1
  uni.showToast({ title: '当前环境不支持全屏播放', icon: 'none' })
}

const exitFullscreenVideo = () => {
  const index = fullscreenVideoIndex.value
  if (index >= 0) {
    const context = getVideoContext(index)
    if (context?.exitFullScreen) {
      context.exitFullScreen()
    }
  }
  fullscreenVideoIndex.value = -1
  resetSwipeTouch()
}

const onVideoFullscreenChange = (index: number, event: any) => {
  const fullScreen = Boolean(event?.detail?.fullScreen ?? event?.detail?.fullscreen)
  fullscreenVideoIndex.value = fullScreen ? index : -1
  if (!fullScreen) resetSwipeTouch()
}

const openVideoSource = (url?: string) => {
  if (!url) return
  // #ifdef H5
  window.open(url, '_blank')
  // #endif
  // #ifndef H5
  uni.setClipboardData({ data: url })
  uni.showToast({ title: '原链接已复制', icon: 'none' })
  // #endif
}

const formatCount = (value?: string) => {
  const num = Number(value || 0)
  if (!Number.isFinite(num) || num <= 0) return ''
  if (num >= 10000) return `${(num / 10000).toFixed(num >= 100000 ? 0 : 1)}万`
  return String(num)
}

const videoStats = (video: { likeCount?: string; commentCount?: string; shareCount?: string }) => {
  const parts = [
    formatCount(video.likeCount) ? `赞 ${formatCount(video.likeCount)}` : '',
    formatCount(video.commentCount) ? `评 ${formatCount(video.commentCount)}` : '',
    formatCount(video.shareCount) ? `转 ${formatCount(video.shareCount)}` : ''
  ].filter(Boolean)
  return parts.join(' · ')
}

const copyHotLink = () => {
  const data = sourceUrl.value || keyword.value
  if (!data) return
  uni.setClipboardData({ data })
  uni.showToast({ title: sourceUrl.value ? '原链接已复制' : '关键词已复制', icon: 'none' })
}


// 跳转到指定热搜
const navigateToHot = (item: HotSearchItem) => {
  if (!item.title) {
    uni.showToast({ title: '链接无效', icon: 'none' })
    return
  }
  // 直接跳转，索引已经正确，不用获取列表
  uni.redirectTo({
    url: `/pages/hot-search-detail/index?platform=${encodeURIComponent(platform.value)}&title=${encodeURIComponent(detailConfig.value.title)}&keyword=${encodeURIComponent(item.title)}&hot=${encodeURIComponent(item.hot || '')}&description=${encodeURIComponent(item.description || '')}&url=${encodeURIComponent(item.url || '')}&image=${encodeURIComponent(item.image || '')}&index=${hotList.value.findIndex(n => n === item)}&raw=${encodeURIComponent(JSON.stringify(item.raw || item))}`
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

const firstTouch = (event: any) => event?.changedTouches?.[0] || event?.touches?.[0]

const resetSwipeTouch = () => {
  touchStartTime.value = 0
}

const onTouchStart = (event: any) => {
  if (platform.value !== 'douyin') return
  const touch = firstTouch(event)
  if (!touch) return
  touchStartY.value = Number(touch.clientY || 0)
  touchStartX.value = Number(touch.clientX || 0)
  touchStartTime.value = Date.now()
  swipeNavigating.value = false
}

const onTouchEnd = (event: any) => {
  if (platform.value !== 'douyin' || loading.value || swipeNavigating.value) return
  const touch = firstTouch(event)
  if (!touch || !touchStartTime.value) return
  const deltaY = Number(touch.clientY || 0) - touchStartY.value
  const deltaX = Number(touch.clientX || 0) - touchStartX.value
  const duration = Date.now() - touchStartTime.value
  resetSwipeTouch()
  if (duration > 900 || Math.abs(deltaY) < 90 || Math.abs(deltaY) < Math.abs(deltaX) * 1.4) return
  const target = deltaY < 0 ? nextHot.value : prevHot.value
  if (!target) {
    uni.showToast({ title: deltaY < 0 ? '已经是最后一条' : '已经是第一条', icon: 'none' })
    return
  }
  swipeNavigating.value = true
  exitFullscreenVideo()
  navigateToHot(target)
}

const onFullscreenVideoTouchStart = (index: number, event: any) => {
  if (fullscreenVideoIndex.value !== index) return
  onTouchStart(event)
}

const onFullscreenVideoTouchEnd = (index: number, event: any) => {
  if (fullscreenVideoIndex.value !== index) return
  onTouchEnd(event)
}

const loadMediaDetail = async () => {
  mediaLoading.value = true
  hasLoadedMedia.value = false
  mediaError.value = ''
  try {
    const res = await getHotSearchDetailMedia(detailParams())
    if (res.code === 200 && res.data) {
      applyDetail(res.data)
    } else {
      mediaError.value = res.msg || '内容稍后再试'
    }
  } catch (err: any) {
    mediaError.value = err.message || '内容暂时加载失败'
  } finally {
    hasLoadedMedia.value = true
    mediaLoading.value = false
  }
}

const loadDetail = async () => {
  if (!hotKeyword.value || hotKeyword.value === '未知热搜') {
    error.value = '缺少热搜关键词'
    return
  }
  keyword.value = hotKeyword.value
  loading.value = true
  mediaLoading.value = false
  hasLoadedMedia.value = false
  error.value = ''
  mediaError.value = ''
  try {
    const res = await getHotSearchDetailBasic(detailParams())
    if (res.code === 200 && res.data) {
      applyDetail(res.data)
      loading.value = false
      loadMediaDetail()
    } else {
      detail.value = null
      error.value = res.msg || '热搜摘要加载失败'
      loading.value = false
    }
  } catch (err: any) {
    detail.value = null
    error.value = err.message || '网络错误'
    loading.value = false
  }
}

onLoad((options: any) => {
  const routePlatform = decodeValue(options?.platform)
  platform.value = routePlatform === 'douyin' ? 'douyin' : 'baidu'
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
      const cached = uni.getStorageSync(`hot_search_current_list_${platform.value}`) || uni.getStorageSync('hot_search_current_list')
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

.douyin-swipe-hint {
  display: inline-flex;
  align-items: center;
  margin-bottom: 18rpx;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  color: #9a3412;
  background: #ffedd5;
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

.hot-image-section {
  margin-top: 16rpx;
}

.hot-image {
  display: block;
  width: 100%;
  border-radius: 20rpx;
  background: #ffedd5;
}

.video-section {
  margin-top: 22rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid #fed7aa;
}

.video-title {
  display: block;
}

.video-title {
  color: #c2410c;
  font-size: 28rpx;
  font-weight: 800;
}

.video-item {
  margin-top: 16rpx;
  padding: 18rpx;
  border-radius: 22rpx;
  background: #fff7ed;
}

.hot-video {
  width: 100%;
  height: 420rpx;
  border-radius: 20rpx;
  overflow: hidden;
  background: #0f172a;
}

.video-meta {
  margin-top: 14rpx;
}

.video-desc,
.video-author,
.video-stats,
.video-proxy-note {
  display: block;
  line-height: 1.5;
}

.video-desc {
  color: #17233d;
  font-size: 26rpx;
  font-weight: 700;
}

.video-author,
.video-stats,
.video-proxy-note {
  margin-top: 6rpx;
  color: #9a3412;
  font-size: 23rpx;
}

.video-proxy-note {
  color: #78716c;
}

.video-action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 14rpx;
}

.video-source-btn,
.video-fullscreen-btn {
  margin: 0;
  padding: 0 20rpx;
  width: fit-content;
  height: 58rpx;
  line-height: 58rpx;
  border-radius: 999rpx;
  color: #fff;
  background: linear-gradient(135deg, #111827, #ef4444);
  font-size: 23rpx;
  font-weight: 700;
}

.video-fullscreen-btn {
  background: linear-gradient(135deg, #f97316, #ef4444);
}

.media-loading,
.related-loading {
  margin-top: 18rpx;
  padding: 22rpx 20rpx;
  border-radius: 18rpx;
  background: #fff7ed;
}

.media-loading {
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.media-loading-player {
  position: relative;
  flex: 0 0 86rpx;
  width: 86rpx;
  height: 58rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  border-radius: 16rpx;
  background: linear-gradient(135deg, #f97316, #ef4444);
  box-shadow: 0 10rpx 24rpx rgba(249, 115, 22, 0.2);
  overflow: hidden;
}

.media-loading-player::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, transparent 0%, rgba(255, 255, 255, 0.24) 48%, transparent 100%);
  animation: video-shine 1.2s ease-in-out infinite;
}

.media-loading-wave {
  position: relative;
  z-index: 2;
  width: 8rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.72);
  transform-origin: center;
  animation: video-wave 0.9s ease-in-out infinite;
}

.media-loading-wave-a {
  height: 18rpx;
}

.media-loading-wave-b {
  height: 30rpx;
  animation-delay: 0.14s;
}

.media-loading-wave-c {
  height: 18rpx;
}

.related-loading-text,
.media-error {
  display: block;
  color: #c2410c;
  font-size: 24rpx;
  line-height: 1.5;
}

.media-error {
  margin-top: 16rpx;
  color: #dc2626;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes flame-pulse {
  0%, 100% { transform: scale(0.92); opacity: 0.82; }
  50% { transform: scale(1.08); opacity: 1; }
}

@keyframes skeleton-flow {
  0% { background-position: 120% 0; }
  100% { background-position: -120% 0; }
}

@keyframes loading-shine {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

@keyframes video-shine {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

@keyframes video-wave {
  0%, 100% { transform: scaleY(0.65); opacity: 0.58; }
  50% { transform: scaleY(1.2); opacity: 1; }
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
  padding: 52rpx 28rpx;
  color: #f97316;
}

.detail-loading-card {
  position: relative;
  overflow: hidden;
}

.detail-loading-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 50% 20%, rgba(249, 115, 22, 0.14), transparent 34%), linear-gradient(120deg, transparent 0%, rgba(251, 146, 60, 0.08) 44%, rgba(249, 115, 22, 0.18) 50%, rgba(251, 146, 60, 0.08) 56%, transparent 100%);
  animation: loading-shine 1.8s ease-in-out infinite;
}

.detail-loading-orbit {
  position: relative;
  width: 108rpx;
  height: 108rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-loading-ring {
  position: absolute;
  inset: 0;
  border-radius: 999rpx;
  border: 8rpx solid #fed7aa;
  border-top-color: #f97316;
  border-right-color: #ef4444;
  animation: spin 0.9s linear infinite;
}

.detail-loading-flame {
  position: relative;
  z-index: 1;
  font-size: 44rpx;
  animation: flame-pulse 1.1s ease-in-out infinite;
}

.loading-text {
  position: relative;
  z-index: 1;
  margin-top: 18rpx;
  font-size: 26rpx;
  font-weight: 760;
}

.detail-loading-bars {
  position: relative;
  z-index: 1;
  width: 100%;
  margin-top: 30rpx;
}

.detail-loading-bar {
  height: 22rpx;
  margin-top: 18rpx;
  border-radius: 999rpx;
  background: linear-gradient(90deg, #ffedd5 0%, #fed7aa 45%, #fff7ed 90%);
  background-size: 220% 100%;
  animation: skeleton-flow 1.3s ease-in-out infinite;
}

.detail-loading-bar-title {
  width: 56%;
  height: 34rpx;
}

.detail-loading-bar-media {
  width: 100%;
  height: 180rpx;
  border-radius: 22rpx;
}

.detail-loading-bar-short {
  width: 68%;
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
