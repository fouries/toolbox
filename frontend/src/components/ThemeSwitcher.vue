<template>
  <button class="theme-switcher" size="mini" @click="showThemePicker">
    <text class="theme-switcher-icon">{{ currentTheme.icon }}</text>
    <text class="theme-switcher-text">主题</text>
  </button>
</template>

<script setup lang="ts">
import { useTheme } from '@/utils/theme'

const { currentTheme, showThemePicker } = useTheme()
</script>

<style scoped>
.theme-switcher {
  position: fixed;
  top: 24rpx;
  right: 24rpx;
  z-index: 99;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  min-width: 132rpx;
  height: 56rpx;
  line-height: 56rpx;
  padding: 0 20rpx;
  border-radius: 999rpx;
  border: 2rpx solid var(--theme-switch-border, rgba(255, 255, 255, 0.72));
  background: var(--theme-switch-bg, rgba(255, 255, 255, 0.82));
  color: var(--theme-switch-text, #243044);
  box-shadow: var(--theme-switch-shadow, 0 10rpx 30rpx rgba(20, 35, 90, 0.12));
  backdrop-filter: blur(16px);
  font-size: 24rpx;
}

.theme-switcher-icon,
.theme-switcher-text {
  line-height: 1;
}

.theme-switcher[disabled] {
  opacity: 1;
}
</style>
