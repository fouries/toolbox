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
          <text class="toolbar-desc">百度实时热点，列表仅显示标题</text>
        </view>
        <button class="refresh-btn" @tap="fetchHotSearch" :disabled="loading">{{ loading ? '刷新中...' : '刷新热搜' }}</button>
      </view>

      <view class="loading" v-if="loading">
        <text class="loading-icon">⏳</text>
        <text class="loading-text">正在加载百度热搜榜...</text>
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
        <text class="note-text">百度热搜列表共展示 21 条，第一条置顶，后续从 1 到 20 编号；点击标题进入详情页，只展示关键词、图片和摘要。</text>
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

const currentConfig = { id: 'baidu', title: '百度热搜榜', icon: '🔎', desc: '查看百度搜索热点排行' }
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
    const res: any = await getHotSearch('baidu')
    const data = res.data || res.newslist
    if (res.code === 200 && data && Array.isArray(data.items)) {
      hotItems.value = data.items
      updateTime.value = data.updateTime || ''
      if (!hotItems.value.length) error.value = '暂无百度热搜数据'
    } else {
      error.value = res.msg || '百度热搜榜加载失败'
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
    `platform=${encodeURIComponent('baidu')}`,
    `title=${encodeURIComponent(currentConfig.title)}`,
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

onLoad(() => {
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
