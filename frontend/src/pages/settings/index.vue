<template>
  <view :class="['container', themeClass]">
    <view class="page-shell settings-shell">
      <view class="profile-card">
        <view class="profile-avatar">🧰</view>
        <view class="profile-info">
          <text class="profile-title">小巧的工具箱</text>
          <text class="profile-desc">设置、反馈和关于信息</text>
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
          <view class="menu-item" @click="showFeedback">
            <view class="menu-left">
              <text class="menu-icon">💬</text>
              <text class="menu-name">反馈建议</text>
            </view>
            <view class="menu-right">
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

      <!-- #ifdef H5 -->
      <view class="beian-card" @click="navigateToBeian">
        <text>粤ICP备2026056747号</text>
      </view>
      <!-- #endif -->
    </view>
  </view>
</template>

<script setup lang="ts">
import { useTheme } from '@/utils/theme'

const { themes, currentTheme, themeClass, setTheme, showThemePicker } = useTheme()

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

const showFeedback = () => {
  uni.showModal({
    title: '反馈建议',
    content: '如果使用中遇到问题，可以通过站点备案主体联系方式或项目页面反馈。',
    showCancel: false,
    confirmText: '知道了'
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

.profile-card {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 30rpx;
  border-radius: 32rpx;
  border: 2rpx solid var(--theme-border, #eef2f7);
  background: linear-gradient(135deg, var(--theme-surface, #ffffff), var(--theme-primary-soft, #eef5ff));
  box-shadow: var(--theme-shadow-card, 0 18rpx 60rpx rgba(20, 35, 90, 0.08));
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

.profile-info {
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

.profile-desc {
  color: var(--theme-text-muted, #7a869a);
  font-size: 24rpx;
}

.settings-card {
  overflow: hidden;
  border-radius: 32rpx;
  border: 2rpx solid var(--theme-border, #eef2f7);
  background: var(--theme-surface, #ffffff);
  box-shadow: var(--theme-shadow-card, 0 18rpx 60rpx rgba(20, 35, 90, 0.08));
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

.menu-left {
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.menu-icon {
  font-size: 36rpx;
  line-height: 1;
}

.menu-name {
  font-size: 30rpx;
  font-weight: 500;
}

.menu-right {
  display: flex;
  align-items: center;
  gap: 12rpx;
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
