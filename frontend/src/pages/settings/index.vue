<template>
  <view :class="['container', themeClass]">
    <view class="page-shell settings-shell">
      <view class="profile-card">
        <view class="profile-avatar">🧰</view>
        <view class="profile-info">
          <text class="profile-title">小巧的工具箱</text>
          <text class="profile-desc">设置、反馈、订阅提醒和关于信息</text>
        </view>
      </view>

      <view class="settings-card">
        <view class="menu-list">
          <view class="menu-item" @click="showThemePicker">
            <view class="menu-left">
              <text class="menu-icon">🎨</text>
              <text class="menu-name">主题设置</text>
            </view>
            <view class="menu-right">
              <text class="current-theme">{{ currentTheme.icon }} {{ currentTheme.name }}</text>
              <text class="menu-arrow">></text>
            </view>
          </view>
          <view class="menu-item" @click="clearRecentTools">
            <view class="menu-left">
              <text class="menu-icon">🕘</text>
              <text class="menu-name">清空最近使用</text>
            </view>
            <view class="menu-right">
              <text class="menu-hint">本机缓存</text>
              <text class="menu-arrow">></text>
            </view>
          </view>
          <view class="menu-item" @click="openFeedbackPanel">
            <view class="menu-left">
              <text class="menu-icon">💬</text>
              <text class="menu-name">反馈建议</text>
            </view>
            <view class="menu-right">
              <text class="menu-hint">在线提交</text>
              <text class="menu-arrow">></text>
            </view>
          </view>
          <view class="menu-item" @click="openReminderPanel">
            <view class="menu-left">
              <text class="menu-icon">🔔</text>
              <text class="menu-name">订阅提醒</text>
            </view>
            <view class="menu-right">
              <text class="menu-hint">{{ enabledReminderCount ? `${enabledReminderCount} 个已开启` : '未开启' }}</text>
              <text class="menu-arrow">></text>
            </view>
          </view>
          <view class="menu-item" @click="openCustomerServicePanel">
            <view class="menu-left">
              <text class="menu-icon">👩‍💻</text>
              <text class="menu-name">联系客服</text>
            </view>
            <view class="menu-right">
              <text class="menu-hint">微信沟通</text>
              <text class="menu-arrow">></text>
            </view>
          </view>
          <view class="menu-item" @click="showAbout">
            <view class="menu-left">
              <text class="menu-icon">ℹ️</text>
              <text class="menu-name">关于小巧的工具箱</text>
            </view>
            <view class="menu-right">
              <text class="menu-hint">v1.0</text>
              <text class="menu-arrow">></text>
            </view>
          </view>
        </view>
      </view>

      <view v-if="activePanel" class="panel-mask" @click="closeActivePanel">
        <view class="panel-sheet" @click.stop>
          <view class="sheet-handle"></view>
          <view v-if="activePanel === 'feedback'" id="feedback-form" class="engagement-card feedback-form">
            <view class="card-header">
              <view>
                <text class="card-title">反馈建议</text>
                <text class="card-desc">遇到问题、内容错误或想要新功能，都可以直接告诉我。</text>
              </view>
              <text class="card-icon">💬</text>
            </view>

            <view class="form-row">
              <text class="form-label">反馈类型</text>
              <picker :range="feedbackCategoryLabels" :value="feedbackCategoryIndex" @change="changeFeedbackCategory">
                <view class="picker-value">{{ feedbackCategoryLabels[feedbackCategoryIndex] }} ></view>
              </picker>
            </view>
            <view class="form-row form-row-block">
              <text class="form-label">反馈内容</text>
              <textarea
                v-model="feedbackForm.content"
                class="feedback-textarea"
                maxlength="1000"
                placeholder="请描述你遇到的问题或建议，至少 5 个字"
                :show-confirm-bar="false"
              />
            </view>
            <view class="form-row form-row-block">
              <text class="form-label">联系方式（选填）</text>
              <input v-model="feedbackForm.contact" class="text-input" maxlength="128" placeholder="微信/邮箱，便于需要时联系你" />
            </view>
            <button class="primary-button" :disabled="submittingFeedback" @click="submitFeedbackForm">
              {{ submittingFeedback ? '提交中...' : '提交反馈' }}
            </button>

            <view v-if="feedbackList.length" class="feedback-history">
              <text class="section-title">我的反馈记录</text>
              <view v-for="item in feedbackList" :key="item.id" class="history-item">
                <view class="history-top">
                  <text class="history-tag">{{ feedbackCategoryMap[item.category] || item.category }}</text>
                  <text class="history-status">{{ item.status === 'submitted' ? '已提交' : item.status }}</text>
                </view>
                <text class="history-content">{{ item.content }}</text>
              </view>
            </view>
          </view>

          <view v-else-if="activePanel === 'reminders'" class="engagement-card reminder-card">
            <view class="card-header">
              <view>
                <text class="card-title">订阅提醒</text>
                <text class="card-desc">微信小程序端开启时会申请订阅消息授权，到点后通过微信服务通知提醒。</text>
              </view>
              <text class="card-icon">🔔</text>
            </view>

            <view class="wechat-subscribe-tip">
              <text>微信订阅消息：{{ wechatSubscribeReady ? '已配置，可授权接收服务通知' : '模板待配置，当前仅保存提醒偏好' }}</text>
            </view>

            <view v-for="option in reminderOptions" :key="option.type" class="reminder-item">
              <view class="reminder-main">
                <text class="reminder-icon">{{ option.icon }}</text>
                <view class="reminder-text">
                  <text class="reminder-title">{{ option.title }}</text>
                  <text class="reminder-desc">{{ option.desc }}</text>
                </view>
              </view>
              <view class="reminder-actions">
                <picker mode="time" :value="getReminderTime(option.type)" @change="changeReminderTime(option, $event)">
                  <view class="time-pill">{{ getReminderTime(option.type) }}</view>
                </picker>
                <switch :checked="isReminderEnabled(option.type)" color="#2563eb" @change="toggleReminder(option, $event)" />
              </view>
            </view>
          </view>

          <view v-else class="engagement-card customer-service-card">
            <view class="card-header">
              <view>
                <text class="card-title">联系客服</text>
                <text class="card-desc">有疑问、建议或需要更快回复，可以通过微信联系我。</text>
              </view>
              <text class="card-icon">👩‍💻</text>
            </view>

            <!-- #ifdef MP-WEIXIN -->
            <button class="primary-button customer-contact-button" open-type="contact">
              打开微信客服
            </button>
            <text class="customer-tip">会话由微信小程序官方客服能力提供。</text>
            <!-- #endif -->

            <!-- #ifdef H5 -->
            <view class="wechat-qr-wrap">
              <image class="wechat-qr" src="/static/customer-service-wechat.jpg" mode="widthFix" @click="previewCustomerQr" />
              <text class="customer-tip">长按或点击放大二维码，添加时请备注：小巧的工具箱反馈。</text>
            </view>
            <!-- #endif -->
          </view>
        </view>
      </view>

      <!-- #ifdef H5 -->
      <view class="beian-card" @click="navigateToBeian">
        <text>粤ICP备2026056747号</text>
      </view>
      <!-- #endif -->
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  bindWechatLogin,
  disableReminderSubscription,
  getFeedbackList,
  getReminderSubscriptions,
  getWechatSubscribeConfig,
  saveReminderSubscription,
  submitFeedback,
  type FeedbackResult,
  type ReminderSubscription,
  type WechatSubscribeConfig
} from '@/api'
import { useTheme } from '@/utils/theme'

const TOOLBOX_USER_KEY = 'toolbox_user_key'

const { themes, currentTheme, themeClass, setTheme, showThemePicker } = useTheme()
void themes
void setTheme

const feedbackCategoryMap: Record<string, string> = {
  bug: '问题反馈',
  idea: '功能建议',
  content: '内容纠错',
  other: '其他'
}
const feedbackCategories = Object.keys(feedbackCategoryMap)
const feedbackCategoryLabels = feedbackCategories.map(key => feedbackCategoryMap[key])
const feedbackCategoryIndex = ref(1)
const activePanel = ref<'feedback' | 'reminders' | 'customerService' | ''>('')
const submittingFeedback = ref(false)
const feedbackList = ref<FeedbackResult[]>([])
const reminderSubscriptions = ref<ReminderSubscription[]>([])
const wechatSubscribeConfig = ref<WechatSubscribeConfig>({ enabled: false, templates: {} })

const feedbackForm = reactive({
  category: 'idea',
  content: '',
  contact: ''
})

const reminderOptions = [
  { type: 'daily_brief', title: '每日简报', desc: '每天固定时间看重点资讯', icon: '📰', defaultTime: '08:30' },
  { type: 'weather', title: '天气预报', desc: '出门前查看天气和温度', icon: '🌤️', defaultTime: '07:30' },
  { type: 'hot_search', title: '热搜榜提醒', desc: '关注百度/抖音热点变化', icon: '🔥', defaultTime: '12:00' },
  { type: 'gold_price', title: '黄金行情提醒', desc: '关注黄金价格走势', icon: '🥇', defaultTime: '09:30' }
]

const reminderMap = computed(() => {
  const map: Record<string, ReminderSubscription> = {}
  reminderSubscriptions.value.forEach(item => {
    map[item.reminder_type] = item
  })
  return map
})

const enabledReminderCount = computed(() => reminderSubscriptions.value.filter(item => item.enabled).length)
const wechatSubscribeReady = computed(() => Boolean(wechatSubscribeConfig.value.enabled && Object.values(wechatSubscribeConfig.value.templates || {}).some(Boolean)))

const ensureUserKey = () => {
  try {
    const existing = uni.getStorageSync(TOOLBOX_USER_KEY)
    if (typeof existing === 'string' && existing.length >= 8) return existing
    const created = `anon_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`
    uni.setStorageSync(TOOLBOX_USER_KEY, created)
    return created
  } catch {
    return `anon_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`
  }
}

const currentPagePath = () => {
  try {
    const pages = getCurrentPages()
    const current = pages[pages.length - 1] as { route?: string } | undefined
    return current?.route ? `/${current.route}` : '/pages/settings/index'
  } catch {
    return '/pages/settings/index'
  }
}

const loadEngagementData = async () => {
  const userKey = ensureUserKey()
  try {
    const [feedbackRes, reminderRes] = await Promise.all([
      getFeedbackList(userKey),
      getReminderSubscriptions(userKey)
    ])
    if (feedbackRes.code === 200 && Array.isArray(feedbackRes.data)) feedbackList.value = feedbackRes.data
    if (reminderRes.code === 200 && Array.isArray(reminderRes.data)) reminderSubscriptions.value = reminderRes.data
    const subscribeConfig = await getWechatSubscribeConfig()
    if (subscribeConfig.code === 200 && subscribeConfig.data) wechatSubscribeConfig.value = subscribeConfig.data
  } catch (err) {
    console.warn('load engagement data failed', err)
  }
}

const changeFeedbackCategory = (event: any) => {
  const index = Number(event?.detail?.value || 0)
  feedbackCategoryIndex.value = index
  feedbackForm.category = feedbackCategories[index] || 'idea'
}

const submitFeedbackForm = async () => {
  const content = feedbackForm.content.trim()
  if (content.length < 5) {
    uni.showToast({ title: '至少输入5个字', icon: 'none' })
    return
  }
  submittingFeedback.value = true
  try {
    const result = await submitFeedback({
      user_key: ensureUserKey(),
      category: feedbackForm.category,
      content,
      contact: feedbackForm.contact.trim(),
      page: currentPagePath()
    })
    if (result.code !== 200) throw new Error(result.msg || '提交失败')
    feedbackForm.content = ''
    await loadEngagementData()
    uni.showToast({ title: '反馈已提交', icon: 'success' })
  } catch (err) {
    console.warn('submit feedback failed', err)
    uni.showToast({ title: '提交失败，请稍后再试', icon: 'none' })
  } finally {
    submittingFeedback.value = false
  }
}

const getReminderTime = (type: string) => {
  return reminderMap.value[type]?.reminder_time || reminderOptions.find(item => item.type === type)?.defaultTime || '08:00'
}

const isReminderEnabled = (type: string) => Boolean(reminderMap.value[type]?.enabled)


const requestWechatSubscribe = async (option: typeof reminderOptions[number]) => {
  const templateId = wechatSubscribeConfig.value.templates?.[option.type] || ''
  if (!templateId) return { accepted: false, templateId: '' }

  // #ifdef MP-WEIXIN
  try {
    const subscribeResult = await new Promise<Record<string, string>>((resolve, reject) => {
      uni.requestSubscribeMessage({
        tmplIds: [templateId],
        success: (res) => resolve(res as unknown as Record<string, string>),
        fail: (err) => reject(err)
      })
    })
    if (subscribeResult[templateId] !== 'accept') {
      uni.showToast({ title: '未授权微信提醒，仅保存偏好', icon: 'none' })
      return { accepted: false, templateId }
    }
    const loginResult = await new Promise<{ code?: string }>((resolve, reject) => {
      uni.login({
        provider: 'weixin',
        success: (res) => resolve(res),
        fail: (err) => reject(err)
      })
    })
    if (loginResult.code) {
      await bindWechatLogin({ user_key: ensureUserKey(), code: loginResult.code })
    }
    return { accepted: true, templateId }
  } catch (err) {
    console.warn('wechat subscribe failed', err)
    uni.showToast({ title: '微信授权失败，仅保存偏好', icon: 'none' })
    return { accepted: false, templateId }
  }
  // #endif

  // #ifndef MP-WEIXIN
  return { accepted: false, templateId }
  // #endif
}

const saveReminder = async (option: typeof reminderOptions[number], enabled: boolean, time = getReminderTime(option.type), wxSubscribe = { accepted: false, templateId: '' }) => {
  const result = await saveReminderSubscription({
    user_key: ensureUserKey(),
    reminder_type: option.type,
    title: option.title,
    reminder_time: time,
    enabled,
    wx_template_id: wxSubscribe.templateId,
    wx_subscribe_enabled: wxSubscribe.accepted
  })
  if (result.code !== 200 || !result.data) throw new Error(result.msg || '保存失败')
  const next = reminderSubscriptions.value.filter(item => item.reminder_type !== option.type)
  reminderSubscriptions.value = [result.data, ...next]
}

const toggleReminder = async (option: typeof reminderOptions[number], event: any) => {
  const enabled = Boolean(event?.detail?.value)
  try {
    if (enabled) {
      const wxSubscribe = await requestWechatSubscribe(option)
      await saveReminder(option, true, getReminderTime(option.type), wxSubscribe)
      uni.showToast({ title: wxSubscribe.accepted ? '已开启微信提醒' : '已开启提醒', icon: 'success' })
    } else {
      const result = await disableReminderSubscription(ensureUserKey(), option.type)
      if (result.code === 200 && result.data) {
        const next = reminderSubscriptions.value.filter(item => item.reminder_type !== option.type)
        reminderSubscriptions.value = [result.data, ...next]
      }
      uni.showToast({ title: '已关闭提醒', icon: 'success' })
    }
  } catch (err) {
    console.warn('toggle reminder failed', err)
    uni.showToast({ title: '操作失败，请稍后再试', icon: 'none' })
    await loadEngagementData()
  }
}

const changeReminderTime = async (option: typeof reminderOptions[number], event: any) => {
  const time = String(event?.detail?.value || getReminderTime(option.type))
  try {
    await saveReminder(option, true, time, { accepted: isReminderEnabled(option.type) && Boolean(reminderMap.value[option.type]?.wx_subscribe_enabled), templateId: reminderMap.value[option.type]?.has_wechat_template ? (wechatSubscribeConfig.value.templates?.[option.type] || '') : '' })
    uni.showToast({ title: '提醒时间已保存', icon: 'success' })
  } catch (err) {
    console.warn('change reminder time failed', err)
    uni.showToast({ title: '保存失败，请稍后再试', icon: 'none' })
  }
}

const openFeedbackPanel = () => {
  activePanel.value = 'feedback'
}

const openReminderPanel = () => {
  activePanel.value = 'reminders'
}

const openCustomerServicePanel = () => {
  activePanel.value = 'customerService'
}

const closeActivePanel = () => {
  activePanel.value = ''
}

const clearRecentTools = () => {
  uni.showModal({
    title: '清空最近使用',
    content: '确定清空首页的最近使用记录吗？',
    success: (res) => {
      if (!res.confirm) return
      try {
        uni.removeStorageSync('toolbox_recent_tools')
      } catch {}
      uni.showToast({ title: '已清空', icon: 'success' })
    }
  })
}

const showAbout = () => {
  uni.showModal({
    title: '小巧的工具箱',
    content: '一个聚合生活查询、实用工具、热榜资讯的小工具合集。',
    showCancel: false,
    confirmText: '好的'
  })
}

const navigateToBeian = () => {
  // #ifdef H5
  const opened = window.open('https://beian.miit.gov.cn/', '_blank', 'noopener,noreferrer')
  if (opened) opened.opener = null
  // #endif
}

const previewCustomerQr = () => {
  // #ifdef H5
  uni.previewImage({ urls: ['/static/customer-service-wechat.jpg'] })
  // #endif
}

onMounted(() => {
  void loadEngagementData()
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 24rpx;
  background: var(--theme-bg, #f5f7fb);
}

.settings-shell {
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.profile-card,
.settings-card {
  border-radius: 32rpx;
  border: 2rpx solid var(--theme-border, #eef2f7);
  background: var(--theme-surface, #ffffff);
  box-shadow: var(--theme-shadow-card, 0 18rpx 60rpx rgba(20, 35, 90, 0.08));
}

.profile-card {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 30rpx;
  background: linear-gradient(135deg, var(--theme-surface, #ffffff), var(--theme-primary-soft, #eef5ff));
}

.profile-avatar {
  width: 92rpx;
  height: 92rpx;
  border-radius: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--theme-primary, #1677ff);
  color: #fff;
  font-size: 46rpx;
  box-shadow: inset 0 0 0 2rpx rgba(255,255,255,0.36), 0 10rpx 24rpx rgba(22,119,255,0.18);
}

.profile-info,
.card-header > view,
.reminder-text {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  min-width: 0;
}

.profile-title {
  color: var(--theme-text, #17233d);
  font-size: 34rpx;
  font-weight: 900;
}

.profile-desc,
.card-desc,
.reminder-desc {
  color: var(--theme-text-muted, #7a869a);
  font-size: 24rpx;
  line-height: 1.5;
}

.settings-card {
  overflow: hidden;
}

.menu-list {
  padding: 12rpx 0;
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 92rpx;
  padding: 0 24rpx;
  color: var(--theme-text, #243044);
}

.menu-item:active {
  background: var(--theme-bg-hover, #f5f7fb);
}

.menu-left,
.menu-right,
.reminder-main,
.reminder-actions,
.history-top {
  display: flex;
  align-items: center;
}

.menu-left {
  gap: 18rpx;
}

.menu-right,
.reminder-actions {
  gap: 12rpx;
}

.menu-icon {
  font-size: 36rpx;
  line-height: 1;
}

.menu-name {
  font-size: 30rpx;
  font-weight: 500;
}

.current-theme,
.menu-hint {
  font-size: 26rpx;
  color: var(--theme-text-muted, #9aa6b8);
}

.menu-arrow {
  font-size: 28rpx;
  color: var(--theme-text-muted, #9aa6b8);
}

.panel-mask {
  position: fixed;
  inset: 0;
  z-index: 99;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 24rpx 24rpx calc(148rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
  background: rgba(15, 23, 42, 0.42);
}

.panel-sheet {
  width: 100%;
  max-height: calc(100vh - 188rpx - env(safe-area-inset-bottom));
  overflow-y: auto;
  border-radius: 34rpx 34rpx 24rpx 24rpx;
  background: var(--theme-surface, #ffffff);
  box-shadow: 0 -20rpx 70rpx rgba(15, 23, 42, 0.18);
}

/* #ifdef MP-WEIXIN */
.panel-mask {
  padding-bottom: calc(128rpx + env(safe-area-inset-bottom));
}
/* #endif */

/* #ifdef H5 */
.panel-mask {
  padding-bottom: calc(168rpx + env(safe-area-inset-bottom));
}
/* #endif */

.sheet-handle {
  width: 78rpx;
  height: 8rpx;
  margin: 18rpx auto 0;
  border-radius: 999rpx;
  background: var(--theme-border, #d7deea);
}

.engagement-card {
  padding: 28rpx;
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.card-header {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
}

.card-title {
  color: var(--theme-text, #17233d);
  font-size: 32rpx;
  font-weight: 900;
}

.card-icon {
  font-size: 42rpx;
}

.form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.form-row-block {
  align-items: stretch;
  flex-direction: column;
  gap: 12rpx;
}

.form-label,
.section-title {
  color: var(--theme-text, #243044);
  font-size: 27rpx;
  font-weight: 700;
}

.picker-value,
.time-pill {
  padding: 12rpx 18rpx;
  border-radius: 999rpx;
  background: var(--theme-primary-soft, #eef5ff);
  color: var(--theme-primary, #2563eb);
  font-size: 25rpx;
}

.feedback-textarea,
.text-input {
  width: 100%;
  box-sizing: border-box;
  border-radius: 22rpx;
  border: 2rpx solid var(--theme-border, #e5eaf3);
  background: var(--theme-bg, #f8fafc);
  color: var(--theme-text, #1f2937);
  font-size: 26rpx;
}

.feedback-textarea {
  min-height: 180rpx;
  padding: 18rpx;
}

.text-input {
  height: 76rpx;
  padding: 0 18rpx;
}

.primary-button {
  width: 100%;
  border-radius: 999rpx;
  background: var(--theme-primary, #2563eb);
  color: #fff;
  font-size: 28rpx;
  font-weight: 800;
}

.primary-button[disabled] {
  opacity: 0.65;
}

.feedback-history {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  padding-top: 8rpx;
}

.history-item {
  padding: 18rpx;
  border-radius: 22rpx;
  background: var(--theme-bg, #f8fafc);
}

.history-top {
  justify-content: space-between;
  margin-bottom: 10rpx;
}

.history-tag,
.history-status {
  font-size: 23rpx;
  color: var(--theme-primary, #2563eb);
}

.history-content {
  color: var(--theme-text, #243044);
  font-size: 25rpx;
  line-height: 1.55;
}

.wechat-subscribe-tip {
  padding: 18rpx 20rpx;
  border-radius: 18rpx;
  background: rgba(37, 99, 235, 0.08);
  color: #2563eb;
  font-size: 24rpx;
  line-height: 1.6;
}

.reminder-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  padding: 20rpx 0;
  border-top: 1rpx solid var(--theme-border, #eef2f7);
}

.reminder-item:first-of-type {
  border-top: 0;
}

.reminder-main {
  gap: 16rpx;
  min-width: 0;
  flex: 1;
}

.reminder-icon {
  font-size: 36rpx;
}

.reminder-title {
  color: var(--theme-text, #17233d);
  font-size: 28rpx;
  font-weight: 800;
}

.customer-service-card {
  align-items: stretch;
}

.customer-contact-button {
  margin-top: 8rpx;
}

.wechat-qr-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
  padding: 12rpx 0 4rpx;
}

.wechat-qr {
  width: 420rpx;
  max-width: 76%;
  border-radius: 26rpx;
  border: 2rpx solid var(--theme-border, #e5eaf3);
  background: #fff;
  box-shadow: 0 16rpx 44rpx rgba(15, 23, 42, 0.12);
}

.customer-tip {
  color: var(--theme-text-muted, #7a869a);
  font-size: 24rpx;
  line-height: 1.6;
  text-align: center;
}

.beian-card {
  text-align: center;
  color: var(--theme-text-muted, #8b97a8);
  font-size: 23rpx;
  padding: 10rpx 0 34rpx;
}

@media (min-width: 768px) {
  .container {
    padding: 32px 24px;
  }

  .settings-shell {
    max-width: 760px;
    margin: 0 auto;
  }
}
</style>
