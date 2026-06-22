<template>
  <view :class="['container', themeClass]">
    <view class="page-shell">
      <view class="hero-card">
        <text class="title">🧾 反馈后台</text>
        <text class="subtitle">查看用户反馈、按状态筛选并标记处理进度。管理密钥只保存在本机缓存，不写入代码。</text>
      </view>

      <view class="card auth-card">
        <text class="section-title">管理密钥</text>
        <input class="text-input" password v-model="adminKey" placeholder="请输入 ADMIN_KEY" />
        <button class="primary-btn" @click="loadFeedback" :disabled="loading || !adminKey.trim()">{{ loading ? '加载中...' : '加载反馈' }}</button>
      </view>

      <view class="card filter-card">
        <text class="section-title">状态筛选</text>
        <view class="status-tabs">
          <view class="status-tab" :class="{ active: statusFilter === item.value }" v-for="item in statusOptions" :key="item.value" @click="switchStatus(item.value)">{{ item.label }}</view>
        </view>
      </view>

      <view class="summary-card card" v-if="feedbackList.length">
        <text class="summary-title">共 {{ feedbackList.length }} 条反馈</text>
        <text class="summary-desc">建议优先处理 bug 和联系方式完整的反馈。</text>
      </view>

      <view class="feedback-list">
        <view class="feedback-card card" v-for="item in feedbackList" :key="item.id">
          <view class="feedback-head">
            <text class="feedback-category">{{ categoryLabel(item.category) }}</text>
            <text class="feedback-status">{{ item.status }}</text>
          </view>
          <text class="feedback-content">{{ item.content }}</text>
          <text class="feedback-meta">{{ item.page || '未知页面' }} · {{ item.created_at || '' }}</text>
          <text class="feedback-meta" v-if="item.contact">联系方式：{{ item.contact }}</text>
          <view class="action-row">
            <button size="mini" class="small-btn" @click="updateStatus(item.id, 'new')">待处理</button>
            <button size="mini" class="small-btn progress" @click="updateStatus(item.id, 'processing')">处理中</button>
            <button size="mini" class="small-btn done" @click="updateStatus(item.id, 'done')">已处理</button>
          </view>
        </view>
      </view>

      <view class="empty-card card" v-if="!loading && adminKey && feedbackList.length === 0">
        <text class="empty-icon">📭</text>
        <text class="empty-text">暂无符合条件的反馈</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getAdminFeedbackList, updateAdminFeedbackStatus, type FeedbackResult } from '@/api'
import { useTheme } from '@/utils/theme'

const { themeClass } = useTheme()
const ADMIN_KEY_STORAGE = 'toolbox_admin_key'
const adminKey = ref('')
const statusFilter = ref('')
const loading = ref(false)
const feedbackList = ref<FeedbackResult[]>([])
const statusOptions = [
  { value: '', label: '全部' },
  { value: 'new', label: '待处理' },
  { value: 'processing', label: '处理中' },
  { value: 'done', label: '已处理' }
]

const categoryLabel = (category: string) => ({ idea: '功能建议', bug: '问题反馈', other: '其他' }[category] || category || '反馈')
const switchStatus = (status: string) => { statusFilter.value = status; if (adminKey.value) void loadFeedback() }

const loadFeedback = async () => {
  if (!adminKey.value.trim()) return
  loading.value = true
  try {
    uni.setStorageSync(ADMIN_KEY_STORAGE, adminKey.value.trim())
    const res = await getAdminFeedbackList({ admin_key: adminKey.value.trim(), status: statusFilter.value, limit: 100 })
    if (res.code === 200) feedbackList.value = (res.data || res.newslist || []) as FeedbackResult[]
    else uni.showToast({ title: res.msg || '加载失败', icon: 'none' })
  } catch (error: any) {
    uni.showToast({ title: error?.message || '加载失败', icon: 'none' })
  } finally { loading.value = false }
}

const updateStatus = async (id: number | undefined, status: string) => {
  if (!id || !adminKey.value.trim()) return
  try {
    const res = await updateAdminFeedbackStatus({ admin_key: adminKey.value.trim(), feedback_id: id, status })
    if (res.code === 200) {
      uni.showToast({ title: '已更新', icon: 'success' })
      await loadFeedback()
    } else uni.showToast({ title: res.msg || '更新失败', icon: 'none' })
  } catch (error: any) { uni.showToast({ title: error?.message || '更新失败', icon: 'none' }) }
}

onMounted(() => {
  const stored = uni.getStorageSync(ADMIN_KEY_STORAGE)
  if (typeof stored === 'string') adminKey.value = stored
})
</script>

<style scoped>
.container { min-height:100vh; background:var(--theme-bg,#f5f7fb); }
.page-shell { padding:28rpx; }
.hero-card,.card { border-radius:28rpx; background:var(--theme-card,#fff); box-shadow:0 12rpx 34rpx rgba(15,23,42,.08); }
.hero-card { padding:36rpx; background:linear-gradient(135deg,#334155,#0f172a); color:#fff; }
.title { display:block; font-size:42rpx; font-weight:900; margin-bottom:12rpx; }
.subtitle { display:block; font-size:26rpx; line-height:1.6; opacity:.9; }
.card { margin-top:24rpx; padding:28rpx; }
.section-title { display:block; font-size:30rpx; font-weight:800; margin-bottom:18rpx; color:var(--theme-text,#111827); }
.text-input { box-sizing:border-box; width:100%; height:82rpx; padding:0 22rpx; border:2rpx solid var(--theme-border,#e5e7eb); border-radius:18rpx; background:var(--theme-muted,#f8fafc); }
.primary-btn { margin-top:18rpx; border:none; border-radius:20rpx; background:#2563eb; color:#fff; font-weight:800; }
.status-tabs,.action-row { display:flex; gap:12rpx; flex-wrap:wrap; }
.status-tab { padding:14rpx 24rpx; border-radius:999rpx; background:#f1f5f9; color:#64748b; font-size:24rpx; }
.status-tab.active { background:#2563eb; color:#fff; font-weight:800; }
.summary-title,.feedback-content { display:block; color:var(--theme-text,#111827); font-weight:800; line-height:1.6; }
.summary-desc,.feedback-meta { display:block; margin-top:8rpx; color:var(--theme-text-secondary,#64748b); font-size:23rpx; line-height:1.5; }
.feedback-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:12rpx; }
.feedback-category { font-weight:800; color:#2563eb; }
.feedback-status { padding:6rpx 14rpx; border-radius:999rpx; background:#e0f2fe; color:#0284c7; font-size:22rpx; }
.small-btn { margin:0; background:#f1f5f9; color:#475569; font-size:23rpx; }
.small-btn.progress { background:#fef3c7; color:#b45309; }
.small-btn.done { background:#dcfce7; color:#16a34a; }
.empty-card { text-align:center; }
.empty-icon { display:block; font-size:60rpx; }
.empty-text { display:block; margin-top:12rpx; color:#64748b; }
</style>
