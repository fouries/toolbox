<template>
  <view :class="['container', themeClass]">
    <view class="page-shell brief-shell">
      <view class="page-header brief-header">
        <text class="title">🗞️ 每日简报</text>
        <text class="subtitle">每天快速了解重要新闻与热点动态</text>
      </view>

      <view class="toolbar-card card">
        <view>
          <text class="toolbar-label">{{ briefDate }}</text>
          <text class="toolbar-desc">{{ briefSource }}</text>
        </view>
        <button class="refresh-btn" @tap="fetchDailyBrief" :disabled="loading">{{ loading ? '刷新中...' : '刷新简报' }}</button>
      </view>

      <view class="loading" v-if="loading">
        <text class="loading-icon">⏳</text>
        <text class="loading-text">正在加载每日简报...</text>
      </view>

      <view class="error-box card" v-else-if="error">
        <text class="error-text">{{ error }}</text>
        <button class="retry-btn" @tap="fetchDailyBrief">重新加载</button>
      </view>

      <view class="brief-list" v-else>
        <view class="brief-card card" v-for="item in briefItems" :key="`${item.rank}-${item.title}`">
          <text class="brief-rank">{{ item.rank }}</text>
          <view class="brief-main">
            <text class="brief-title">{{ item.title }}</text>
            <text class="brief-source" v-if="item.source">{{ item.source }}</text>
          </view>
        </view>
      </view>

      <view class="note-card card">
        <text class="note-title">说明</text>
        <text class="note-text">简报内容来自聚合接口并做缓存展示；热点新闻会随时间变化，点击刷新可获取最新内容。</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useTheme } from '@/utils/theme'
import { getDailyBrief, type DailyBriefItem } from '@/api'

const { themeClass } = useTheme()
const loading = ref(false)
const error = ref('')
const briefItems = ref<DailyBriefItem[]>([])
const briefDateValue = ref('')
const briefSourceValue = ref('')

const briefDate = computed(() => briefDateValue.value || '今日简报')
const briefSource = computed(() => briefSourceValue.value || '数据来源：每日简报')

const fetchDailyBrief = async () => {
  loading.value = true
  error.value = ''
  try {
    const res: any = await getDailyBrief()
    const data = res.data || res.newslist
    if (res.code === 200 && data && Array.isArray(data.items)) {
      briefItems.value = data.items
      briefDateValue.value = data.date || ''
      briefSourceValue.value = data.source || ''
      if (!briefItems.value.length) error.value = '暂无简报内容'
    } else {
      error.value = res.msg || '每日简报加载失败'
    }
  } catch (err: any) {
    error.value = err.message || '网络错误'
  } finally {
    loading.value = false
  }
}

onLoad(() => {
  fetchDailyBrief()
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 30rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #eef2ff 0%, #f8fafc 48%, #ffffff 100%);
}

.brief-shell {
  max-width: 980px;
}

.brief-header {
  margin-bottom: 24rpx;
}

.toolbar-card,
.brief-card,
.note-card,
.error-box {
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid rgba(79, 70, 229, 0.14);
  box-shadow: 0 14rpx 38rpx rgba(67, 56, 202, 0.08);
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
.brief-title,
.brief-source,
.note-title,
.note-text,
.loading-icon,
.loading-text,
.error-text {
  display: block;
}

.toolbar-label {
  color: #312e81;
  font-size: 32rpx;
  font-weight: 800;
}

.toolbar-desc {
  margin-top: 6rpx;
  color: #6366f1;
  font-size: 23rpx;
}

.refresh-btn,
.retry-btn {
  margin: 0;
  border: none;
  border-radius: 999rpx;
  background: #4f46e5;
  color: #fff;
  font-size: 25rpx;
  font-weight: 700;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 0;
  color: #4f46e5;
}

.loading-icon {
  font-size: 54rpx;
}

.loading-text {
  margin-top: 18rpx;
  font-size: 26rpx;
}

.brief-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18rpx;
}

.brief-card {
  display: flex;
  align-items: flex-start;
  gap: 18rpx;
}

.brief-rank {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48rpx;
  height: 48rpx;
  flex: 0 0 48rpx;
  border-radius: 16rpx;
  background: #e0e7ff;
  color: #4338ca;
  font-size: 24rpx;
  font-weight: 800;
}

.brief-main {
  flex: 1;
  min-width: 0;
}

.brief-title {
  color: #17233d;
  font-size: 30rpx;
  font-weight: 760;
  line-height: 1.55;
}

.brief-source {
  margin-top: 10rpx;
  color: #94a3b8;
  font-size: 22rpx;
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
  color: #312e81;
  font-size: 28rpx;
  font-weight: 760;
}

.note-text {
  margin-top: 8rpx;
  color: #6366f1;
  font-size: 24rpx;
  line-height: 1.65;
}

@media screen and (min-width: 768px) {
  .container {
    padding: 40px 24px 72px;
  }

  .toolbar-card,
  .brief-card,
  .note-card,
  .error-box {
    padding: 28px;
  }
}
</style>
