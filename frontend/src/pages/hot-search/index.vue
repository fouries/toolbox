<template>
  <view :class="['container', themeClass]">
    <view class="page-shell hot-shell">
      <view class="page-header hot-header">
        <text class="title">{{ currentConfig.icon }} {{ currentConfig.title }}</text>
        <text class="subtitle">{{ currentConfig.desc }}</text>
      </view>

      <view class="platform-tabs card">
        <view
          class="platform-tab"
          :class="{ active: activePlatform === item.id }"
          v-for="item in platformTabs"
          :key="item.id"
          @tap="switchPlatform(item.id)"
        >
          <text class="tab-icon">{{ item.icon }}</text>
          <text class="tab-name">{{ item.title }}</text>
        </view>
      </view>

      <view class="toolbar-card card">
        <view>
          <text class="toolbar-label">{{ updateTimeText }}</text>
          <text class="toolbar-desc">热搜实时变化，点击可复制搜索链接</text>
        </view>
        <button class="refresh-btn" @tap="fetchHotSearch" :disabled="loading">{{ loading ? '刷新中...' : '刷新热搜' }}</button>
      </view>

      <view class="loading" v-if="loading">
        <text class="loading-icon">⏳</text>
        <text class="loading-text">正在加载热搜榜...</text>
      </view>

      <view class="error-box card" v-else-if="error">
        <text class="error-text">{{ error }}</text>
        <button class="retry-btn" @tap="fetchHotSearch">重新加载</button>
      </view>

      <view class="hot-list" v-else>
        <view class="hot-card card" v-for="item in displayedHotItems" :key="`${item.rank}-${item.title}`" @tap="openHotDetail(item)">
          <text class="hot-rank" :class="{ top: item.rank <= 3 }">{{ item.rank }}</text>
          <view class="hot-main">
            <text class="hot-title">{{ item.title }}</text>
            <text class="hot-desc" v-if="shouldShowHotDescription && item.description">{{ item.description }}</text>
            <view class="hot-meta">
              <text v-if="item.hot">热度：{{ item.hot }}</text>
              <text>{{ item.url ? '点击查看详情' : '点击查看相关资讯' }}</text>
            </view>
          </view>
          <text class="hot-arrow">›</text>
        </view>
      </view>

      <view class="note-card card">
        <text class="note-title">说明</text>
        <text class="note-text">点击热搜条目会进入小程序原生详情页，展示关键词、热度和相关资讯；详情页仍保留复制原链接兜底。</text>
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

type PlatformId = 'weibo' | 'baidu'

const platformTabs: Array<{ id: PlatformId; title: string; icon: string; desc: string }> = [
  { id: 'weibo', title: '微博热搜榜', icon: '🔥', desc: '查看微博实时热门话题' },
  { id: 'baidu', title: '百度热搜榜', icon: '🔎', desc: '查看百度搜索热点排行' }
]

const activePlatform = ref<PlatformId>('weibo')
const loading = ref(false)
const error = ref('')
const hotItems = ref<HotSearchItem[]>([])
const updateTime = ref('')

const currentConfig = computed(() => platformTabs.find(item => item.id === activePlatform.value) || platformTabs[0])
const updateTimeText = computed(() => updateTime.value ? `更新时间：${updateTime.value}` : '实时热搜')
const shouldShowHotDescription = computed(() => activePlatform.value !== 'baidu')
const displayedHotItems = computed(() => activePlatform.value === 'baidu' ? hotItems.value.slice(0, 50) : hotItems.value)

const fetchHotSearch = async () => {
  loading.value = true
  error.value = ''
  try {
    const res: any = await getHotSearch(activePlatform.value)
    const data = res.data || res.newslist
    if (res.code === 200 && data && Array.isArray(data.items)) {
      hotItems.value = data.items
      updateTime.value = data.updateTime || ''
      if (!hotItems.value.length) error.value = '暂无热搜数据'
    } else {
      error.value = res.msg || '热搜榜加载失败'
    }
  } catch (err: any) {
    error.value = err.message || '网络错误'
  } finally {
    loading.value = false
  }
}

const switchPlatform = (platform: PlatformId) => {
  activePlatform.value = platform
  fetchHotSearch()
}

const openHotDetail = (item: HotSearchItem) => {
  if (!item.title) return
  const params = [
    `platform=${encodeURIComponent(activePlatform.value)}`,
    `title=${encodeURIComponent(currentConfig.value.title)}`,
    `keyword=${encodeURIComponent(item.title)}`,
    `hot=${encodeURIComponent(item.hot || '')}`,
    `description=${encodeURIComponent(item.description || '')}`,
    `url=${encodeURIComponent(item.url || '')}`,
    `raw=${encodeURIComponent(JSON.stringify(item.raw || item))}`
  ].join('&')
  uni.navigateTo({ url: `/pages/hot-search-detail/index?${params}` })
}

onLoad((options: any) => {
  if (options?.platform === 'baidu') activePlatform.value = 'baidu'
  if (options?.platform === 'weibo') activePlatform.value = 'weibo'
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

.platform-tabs,
.toolbar-card,
.hot-card,
.note-card,
.error-box {
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid rgba(249, 115, 22, 0.14);
  box-shadow: 0 14rpx 38rpx rgba(194, 65, 12, 0.08);
}

.platform-tabs {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12rpx;
  margin-bottom: 18rpx;
}

.platform-tab {
  padding: 18rpx 12rpx;
  border-radius: 22rpx;
  text-align: center;
  background: #fff7ed;
  border: 1rpx solid #fed7aa;
}

.platform-tab.active {
  color: #fff;
  background: linear-gradient(135deg, #f97316, #ef4444);
  border-color: transparent;
}

.tab-icon,
.tab-name,
.toolbar-label,
.toolbar-desc,
.hot-title,
.hot-desc,
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

.toolbar-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  margin-bottom: 22rpx;
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

.hot-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18rpx;
}

.hot-card {
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.hot-rank {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50rpx;
  height: 50rpx;
  flex: 0 0 50rpx;
  border-radius: 16rpx;
  background: #ffedd5;
  color: #c2410c;
  font-size: 24rpx;
  font-weight: 850;
}

.hot-rank.top {
  background: linear-gradient(135deg, #ef4444, #f97316);
  color: #fff;
}

.hot-main {
  flex: 1;
  min-width: 0;
}

.hot-title {
  color: #17233d;
  font-size: 30rpx;
  font-weight: 760;
  line-height: 1.45;
}

.hot-desc {
  margin-top: 10rpx;
  color: #64748b;
  font-size: 24rpx;
  line-height: 1.55;
}

.hot-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  margin-top: 14rpx;
  color: #94a3b8;
  font-size: 22rpx;
}

.hot-arrow {
  color: #f97316;
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

  .platform-tabs,
  .toolbar-card,
  .hot-card,
  .note-card,
  .error-box {
    padding: 28px;
  }
}
</style>
