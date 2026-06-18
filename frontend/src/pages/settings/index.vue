<template>
  <view :class="['container', themeClass]">
    <view class="page-shell settings-shell">
      <view class="settings-card">
        <view class="settings-header">
          <text class="settings-title">我的</text>
          <text class="settings-desc">设置与关于</text>
        </view>

        <view class="menu-list">
          <view class="menu-item" @click="showThemePicker">
            <view class="menu-left">
              <text class="menu-icon">🎨</text>
              <text class="menu-name">主题设置</text>
            </view>
            <text class="menu-arrow">></text>
          </view>

          <view class="theme-section">
            <text class="section-title">当前主题</text>
            <view
              class="theme-item"
              :class="{ active: currentTheme.id === theme.id }"
              v-for="theme in themes"
              :key="theme.id"
              @click="setTheme(theme.id)"
            >
              <view class="theme-left">
                <text class="theme-icon">{{ theme.icon }}</text>
                <text class="theme-name">{{ theme.name }}</text>
              </view>
              <text class="theme-check" v-if="currentTheme.id === theme.id">✓</text>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useTheme } from '@/utils/theme'

const { themes, currentTheme, themeClass, setTheme, showThemePicker } = useTheme()
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
}

.settings-card {
  overflow: hidden;
  border-radius: 32rpx;
  border: 2rpx solid var(--theme-border, #eef2f7);
  background: var(--theme-surface, #ffffff);
  box-shadow: var(--theme-shadow-card, 0 18rpx 60rpx rgba(20, 35, 90, 0.08));
}

.settings-header {
  padding: 34rpx 32rpx 22rpx;
  border-bottom: 1rpx solid var(--theme-border, #eef2f7);
}

.settings-title {
  display: block;
  font-size: 38rpx;
  font-weight: 700;
  color: var(--theme-text, #243044);
}

.settings-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  color: var(--theme-text-muted, #9aa6b8);
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

.menu-arrow {
  font-size: 28rpx;
  color: var(--theme-text-muted, #9aa6b8);
}

.theme-section {
  padding: 12rpx 20rpx 20rpx;
  border-top: 1rpx solid var(--theme-border, #eef2f7);
}

.section-title {
  display: block;
  font-size: 26rpx;
  font-weight: 600;
  color: var(--theme-text-muted, #9aa6b8);
  padding: 16rpx 12rpx 20rpx;
}

.theme-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 92rpx;
  padding: 0 20rpx;
  margin-top: 10rpx;
  border-radius: 24rpx;
  color: var(--theme-text, #243044);
}

.theme-item.active {
  background: var(--theme-primary-soft, #eef5ff);
  color: var(--theme-primary, #2563eb);
}

.theme-left {
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.theme-icon {
  font-size: 34rpx;
  line-height: 1;
}

.theme-name {
  font-size: 28rpx;
  font-weight: 600;
}

.theme-check {
  font-size: 34rpx;
  font-weight: 700;
}
</style>
