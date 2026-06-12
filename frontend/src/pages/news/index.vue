<template>
  <view :class="['container', themeClass]">
    <view class="page-shell news-shell">
      <view class="news-card">
        <view class="news-header">
          <text class="news-title">资讯</text>
          <text class="news-desc">工具资讯和更新动态</text>
        </view>

        <view class="empty-news">
          <text class="empty-icon">📰</text>
          <text class="empty-title">暂无资讯</text>
          <text class="empty-desc">后续会在这里展示工具更新和实用内容</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useTheme } from '@/utils/theme'

const { themeClass } = useTheme()
</script>

<style scoped>
.container {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 24rpx;
  background: var(--theme-bg, #f5f7fb);
}

.news-shell {
  box-sizing: border-box;
}

.news-card {
  overflow: hidden;
  border-radius: 32rpx;
  border: 2rpx solid var(--theme-border, #eef2f7);
  background: var(--theme-surface, #ffffff);
  box-shadow: var(--theme-shadow-card, 0 18rpx 60rpx rgba(20, 35, 90, 0.08));
}

.news-header {
  padding: 34rpx 32rpx 22rpx;
  border-bottom: 1rpx solid var(--theme-border, #eef2f7);
}

.news-title {
  display: block;
  font-size: 38rpx;
  font-weight: 700;
  color: var(--theme-text, #243044);
}

.news-desc {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  color: var(--theme-text-muted, #9aa6b8);
}

.empty-news {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 90rpx 40rpx;
  text-align: center;
}

.empty-icon {
  font-size: 72rpx;
  line-height: 1;
}

.empty-title {
  margin-top: 24rpx;
  font-size: 32rpx;
  font-weight: 700;
  color: var(--theme-text, #243044);
}

.empty-desc {
  margin-top: 12rpx;
  font-size: 24rpx;
  color: var(--theme-text-muted, #9aa6b8);
}
</style>
