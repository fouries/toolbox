<template>
  <view :class="['container', themeClass]">
    <view class="page-shell hot-shell">
      <view class="page-header hot-header">
        <text class="title">{{ currentConfig.icon }} {{ currentConfig.title }}</text>
        <text class="subtitle">{{ currentConfig.desc }}</text>
      </view>

      <view class="toolbar-card card">
        <view>
          <text class="toolbar-label">{{ updateTimeText }}</text>
          <text class="toolbar-desc">{{ currentConfig.sourceText }}，列表仅显示标题</text>
        </view>
        <button class="refresh-btn" @tap="fetchHotSearch" :disabled="loading">{{ loading ? '刷新中...' : '刷新热搜' }}</button>
      </view>

      <view class="loading hot-loading-card card" v-if="loading">
        <view class="hot-loading-orbit">
          <view class="hot-loading-ring"></view>
          <text class="hot-loading-flame">🔥</text>
        </view>
        <view class="hot-loading-skeletons">
          <view class="hot-loading-skeleton" v-for="item in 4" :key="item">
            <view class="skeleton-rank"></view>
            <view class="skeleton-lines">
              <view class="skeleton-line skeleton-line-title"></view>
              <view class="skeleton-line skeleton-line-meta"></view>
            </view>
          </view>
        </view>
      </view>

      <view class="error-box card" v-else-if="error">
        <text class="error-text">{{ error }}</text>
        <button class="retry-btn" @tap="fetchHotSearch">重新加载</button>
      </view>

      <view class="hot-list" v-else>
        <!-- 第一条置顶 -->
        <view class="hot-card card hot-card-sticky" v-if="displayedHotItems.length > 0" :key="`sticky-${displayedHotItems[0].title}`" @tap="openHotDetail(displayedHotItems[0], 0)">
          <text class="hot-rank hot-rank-sticky">⬆️</text>
          <view class="hot-main">
            <text class="hot-title">{{ displayedHotItems[0].title }}</text>
            <view class="hot-meta">
              <text v-if="displayedHotItems[0].hot">热度：{{ displayedHotItems[0].hot }}</text>
              <text>点击查看摘要</text>
            </view>
          </view>
          <text class="hot-arrow">›</text>
        </view>
        <!-- 后面1-20条 -->
        <view class="hot-card card" v-for="(item, index) in displayedHotItems.slice(1)" :key="`${index+1}-${item.title}`" @tap="openHotDetail(item, index + 1)">
          <text class="hot-rank" :class="{ top: index+1 <= 3 }">{{ index+1 }}</text>
          <view class="hot-main">
            <text class="hot-title">{{ item.title }}</text>
            <view class="hot-meta">
              <text v-if="item.hot">热度：{{ item.hot }}</text>
              <text>点击查看摘要</text>
            </view>
          </view>
          <text class="hot-arrow">›</text>
        </view>
      </view>

      <view class="note-card card">
        <text class="note-title">说明</text>
        <text class="note-text">{{ currentConfig.title }}列表共展示 21 条，第一条置顶，后续从 1 到 20 编号；点击标题进入详情页，展示关键词、热度和摘要。</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useTheme } from '@/utils/theme'
import { getHotSearch, type HotSearchItem } from '@/api'

const { themeClass } = useTheme()

const hotConfigs = {
  baidu: { id: 'baidu', title: '百度热搜榜', icon: '🔎', desc: '查看百度搜索热点排行', sourceText: '百度实时热点' },
  douyin: { id: 'douyin', title: '抖音热搜榜', icon: '🎵', desc: '使用天聚数行 API 查看抖音热门搜索排行', sourceText: '天聚数行抖音实时热点' }
} as const

type HotPlatform = keyof typeof hotConfigs

const activePlatform = ref<HotPlatform>('baidu')
const currentConfig = computed(() => hotConfigs[activePlatform.value])
const loading = ref(false)
const error = ref('')
const hotItems = ref<HotSearchItem[]>([])
const updateTime = ref('')

const updateTimeText = computed(() => updateTime.value ? `更新时间：${updateTime.value}` : '实时热搜')
const displayedHotItems = computed(() => hotItems.value.slice(0, 21))

const fetchHotSearch = async () => {
  loading.value = true
  error.value = ''
  try {
    const res: any = await getHotSearch(activePlatform.value)
    const data = res.data || res.newslist
    if (res.code === 200 && data && Array.isArray(data.items)) {
      hotItems.value = data.items
      // 缓存热搜列表给详情页上下篇导航用
      try {
        uni.setStorageSync(`hot_search_current_list_${activePlatform.value}`, hotItems.value.slice(0, 21))
      } catch (e) {
        console.warn('Cache hot search list failed', e)
      }
      updateTime.value = data.updateTime || ''
      if (!hotItems.value.length) error.value = `暂无${currentConfig.value.title}数据`
    } else {
      error.value = res.msg || `${currentConfig.value.title}加载失败`
    }
  } catch (err: any) {
    error.value = err.message || '网络错误'
  } finally {
    loading.value = false
  }
}

const openHotDetail = (item: HotSearchItem, index: number) => {
  if (!item.title) return
  const params = [
    `platform=${encodeURIComponent(activePlatform.value)}`,
    `title=${encodeURIComponent(currentConfig.value.title)}`,
    `keyword=${encodeURIComponent(item.title)}`,
    `hot=${encodeURIComponent(item.hot || '')}`,
    `description=${encodeURIComponent(item.description || '')}`,
    `url=${encodeURIComponent(item.url || '')}`,
    `image=${encodeURIComponent(item.image || '')}`,
    `raw=${encodeURIComponent(JSON.stringify(item.raw || item))}`,
    `index=${index}`
  ].join('&')
  uni.navigateTo({ url: `/pages/hot-search-detail/index?${params}` })
}

onLoad((options: any) => {
  const platform = String(options?.platform || 'baidu')
  activePlatform.value = platform === 'douyin' ? 'douyin' : 'baidu'
  fetchHotSearch()
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 30rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #fff7ed 0%, #f8fafc 48%, #ffffff 100%);
}

.hot-shell {
  max-width: 980px;
}

.hot-header {
  margin-bottom: 24rpx;
}

.toolbar-card,
.hot-card,
.note-card,
.error-box {
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid rgba(249, 115, 22, 0.14);
  box-shadow: 0 14rpx 38rpx rgba(194, 65, 12, 0.08);
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
.hot-title,
.note-title,
.note-text,
.loading-icon,
.loading-text,
.error-text {
  display: block;
}

.toolbar-label {
  color: #7c2d12;
  font-size: 28rpx;
  font-weight: 800;
}

.toolbar-desc {
  margin-top: 6rpx;
  color: #c2410c;
  font-size: 23rpx;
}

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

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 52rpx 28rpx;
  color: #f97316;
}

.hot-loading-card {
  position: relative;
  overflow: hidden;
}

.hot-loading-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, transparent 0%, rgba(251, 146, 60, 0.08) 44%, rgba(249, 115, 22, 0.18) 50%, rgba(251, 146, 60, 0.08) 56%, transparent 100%);
  animation: loading-shine 1.8s ease-in-out infinite;
}

.hot-loading-orbit {
  position: relative;
  width: 104rpx;
  height: 104rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.hot-loading-ring {
  position: absolute;
  inset: 0;
  border-radius: 999rpx;
  border: 8rpx solid #fed7aa;
  border-top-color: #f97316;
  border-right-color: #ef4444;
  animation: spin 0.9s linear infinite;
}

.hot-loading-flame {
  position: relative;
  z-index: 1;
  font-size: 44rpx;
  animation: flame-pulse 1.1s ease-in-out infinite;
}

.loading-text {
  margin-top: 18rpx;
  font-size: 26rpx;
  font-weight: 760;
}

.hot-loading-skeletons {
  position: relative;
  z-index: 1;
  width: 100%;
  margin-top: 30rpx;
}

.hot-loading-skeleton {
  display: grid;
  grid-template-columns: 52rpx 1fr;
  gap: 18rpx;
  align-items: center;
  padding: 18rpx 0;
  border-top: 1rpx solid rgba(254, 215, 170, 0.8);
}

.skeleton-rank,
.skeleton-line {
  overflow: hidden;
  background: linear-gradient(90deg, #ffedd5 0%, #fed7aa 45%, #fff7ed 90%);
  background-size: 220% 100%;
  animation: skeleton-flow 1.3s ease-in-out infinite;
}

.skeleton-rank {
  width: 52rpx;
  height: 52rpx;
  border-radius: 18rpx;
}

.skeleton-line {
  height: 22rpx;
  border-radius: 999rpx;
}

.skeleton-line-title {
  width: 78%;
}

.skeleton-line-meta {
  width: 42%;
  margin-top: 14rpx;
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

.hot-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18rpx;
}

.hot-card {
  display: grid;
  grid-template-columns: 60rpx 1fr 28rpx;
  gap: 18rpx;
  align-items: center;
  padding: 24rpx;
}

.hot-rank {
  width: 52rpx;
  height: 52rpx;
  line-height: 52rpx;
  border-radius: 18rpx;
  text-align: center;
  color: #9a3412;
  background: #ffedd5;
  font-size: 26rpx;
  font-weight: 800;
}

.hot-rank.top {
  color: #fff;
  background: linear-gradient(135deg, #f97316, #ef4444);
}

.hot-card-sticky {
  border: 2rpx solid #f97316;
  background: linear-gradient(135deg, #fff7ed 0%, rgba(255, 247, 237, 0.92) 100%);
}

.hot-rank-sticky {
  width: 52rpx;
  height: 52rpx;
  line-height: 52rpx;
  border-radius: 18rpx;
  text-align: center;
  color: #fff;
  background: linear-gradient(135deg, #f97316, #ef4444);
  font-size: 28rpx;
  font-weight: 800;
}

.hot-title {
  color: #17233d;
  font-size: 30rpx;
  font-weight: 800;
  line-height: 1.45;
}

.hot-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-top: 12rpx;
  color: #c2410c;
  font-size: 23rpx;
}

.hot-arrow {
  color: #fb923c;
  font-size: 48rpx;
  font-weight: 300;
}

.note-card {
  margin-top: 24rpx;
}

.note-title {
  color: #7c2d12;
  font-size: 28rpx;
  font-weight: 800;
}

.note-text {
  margin-top: 10rpx;
  color: #64748b;
  font-size: 24rpx;
  line-height: 1.7;
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
