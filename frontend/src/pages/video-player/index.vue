<template>
  <view class="player-page">
    <!-- #ifdef MP-WEIXIN -->
    <view class="player-stage" :style="playerSizeStyle">
      <video
        id="toolbox-video-player"
        class="player-video"
        :src="videoUrl"
        :poster="poster"
        :title="title"
        controls
        autoplay
        :show-play-btn="false"
        :show-progress="true"
        :show-fullscreen-btn="false"
        :show-center-play-btn="false"
        :enable-play-gesture="false"
        :enable-progress-gesture="true"
        :vslide-gesture-in-fullscreen="true"
        object-fit="contain"
        @tap="togglePlayback"
        @play="isPlaying = true"
        @pause="isPlaying = false"
        @ended="isPlaying = false"
        @error="onVideoError"
      ></video>
      <cover-view class="player-pause-overlay" v-if="!isPlaying" @tap="togglePlayback">
        <cover-view class="player-pause-triangle"></cover-view>
      </cover-view>
    </view>
    <!-- #endif -->
    <!-- #ifndef MP-WEIXIN -->
    <view class="player-stage player-stage-h5">
      <video
        id="toolbox-video-player"
        class="player-video h5-click-video"
        :src="videoUrl"
        :poster="poster"
        :title="title"
        controls
        autoplay
        :show-play-btn="false"
        :show-fullscreen-btn="false"
        :show-center-play-btn="false"
        :enable-play-gesture="false"
        :enable-progress-gesture="true"
        :vslide-gesture-in-fullscreen="true"
        object-fit="contain"
        @click.prevent="togglePlayback"
        @play="isPlaying = true"
        @pause="isPlaying = false"
        @ended="isPlaying = false"
        @error="onVideoError"
      ></video>
      <view class="player-pause-overlay player-pause-overlay-h5" v-if="!isPlaying" @click.stop="togglePlayback">
        <view class="player-pause-triangle"></view>
      </view>
    </view>
    <!-- #endif -->
    <!-- #ifdef MP-WEIXIN -->
    <cover-view class="player-title-overlay">
      <cover-view class="player-title player-title-mini">{{ title || '视频播放' }}</cover-view>
    </cover-view>
    <!-- #endif -->
    <!-- #ifndef MP-WEIXIN -->
    <view class="player-top">
      <button class="player-close" @tap="goBack">退出播放</button>
      <text class="player-title">{{ title || '视频播放' }}</text>
    </view>
    <view class="player-bottom">
      <text class="player-hint">点击退出播放返回详情，上下滑在详情文字区使用</text>
      <button class="player-link" v-if="sourceUrl" @tap="copySource">复制原链接</button>
    </view>
    <!-- #endif -->
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad, onResize } from '@dcloudio/uni-app'

declare function getCurrentPages(): any[];

const videoUrl = ref('')
const poster = ref('')
const title = ref('')
const sourceUrl = ref('')
const isPlaying = ref(true)
const screenWidth = ref(0)
const screenHeight = ref(0)
const videoTopOffset = ref(0)

const playerSizeStyle = computed(() => {
  if (!screenWidth.value || !screenHeight.value) return ''
  const top = videoTopOffset.value
  const height = Math.max(screenHeight.value - top, 1)
  return `width: ${screenWidth.value}px; height: ${height}px; min-height: ${height}px; top: ${top}px;`
})

const updatePlayerSize = () => {
  try {
    const uniAny = uni as any
    const info = typeof uniAny.getWindowInfo === 'function'
      ? uniAny.getWindowInfo()
      : uni.getSystemInfoSync()
    const width = Number(info?.windowWidth || info?.screenWidth)
    const height = Number(info?.windowHeight || info?.screenHeight)
    const menuButton = typeof uniAny.getMenuButtonBoundingClientRect === 'function'
      ? uniAny.getMenuButtonBoundingClientRect()
      : null
    const menuTop = Number(menuButton?.top)
    if (width > 0) screenWidth.value = width
    if (height > 0) screenHeight.value = height
    videoTopOffset.value = menuTop > 0 ? menuTop : Math.max(Number(info?.statusBarHeight) || 0, 0)
  } catch {}
}

const isProxyMediaValue = (value: string) => /\/api\/(?:image|video)-proxy\?url=/.test(value)

const decodeValue = (value: unknown): string => {
  if (typeof value !== 'string') return ''
  let decoded = value
  try {
    while (decoded.includes('%')) {
      const next = decodeURIComponent(decoded)
      decoded = next
      // Keep nested proxy target URLs encoded so signed video/poster query
      // strings are not split into the proxy endpoint's own parameters.
      if (isProxyMediaValue(decoded)) break
    }
  } catch {}
  return decoded
}

const goBack = () => {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack()
    return
  }
  uni.redirectTo({ url: '/pages/hot-search/index?platform=douyin' })
}

const onVideoError = () => {
  uni.showToast({ title: '视频暂时无法播放，可复制原链接去抖音查看', icon: 'none' })
}

const copySource = () => {
  if (!sourceUrl.value) return
  uni.setClipboardData({ data: sourceUrl.value })
  uni.showToast({ title: '原链接已复制', icon: 'none' })
}

const getPlayerContext = () => uni.createVideoContext('toolbox-video-player') as any

const togglePlayback = () => {
  const context = getPlayerContext()
  if (isPlaying.value) {
    context.pause?.()
    isPlaying.value = false
    return
  }
  context.play?.()
  isPlaying.value = true
}

onResize(() => {
  updatePlayerSize()
})

onLoad((options: any) => {
  updatePlayerSize()
  videoUrl.value = decodeValue(options?.url)
  poster.value = decodeValue(options?.poster)
  title.value = decodeValue(options?.title)
  sourceUrl.value = decodeValue(options?.sourceUrl)
  if (!videoUrl.value) {
    uni.showToast({ title: '缺少视频地址', icon: 'none' })
  }
})
</script>

<style scoped>
.player-page {
  position: fixed;
  inset: 0;
  min-height: 100vh;
  background: #000;
  overflow: hidden;
}

.player-stage {
  position: fixed;
  top: 0;
  left: 0;
  background: #000;
  overflow: hidden;
}

.player-stage-h5 {
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
}

.player-video {
  width: 100%;
  height: 100%;
  background: #000;
}

.player-pause-overlay {
  position: absolute;
  left: 50%;
  top: 50%;
  z-index: 4;
  width: 156rpx;
  height: 156rpx;
  margin-left: -78rpx;
  margin-top: -78rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999rpx;
  background: rgba(0, 0, 0, 0.26);
}

.player-pause-overlay-h5 {
  pointer-events: auto;
  cursor: pointer;
}

.h5-click-video,
.h5-click-video::-webkit-media-controls-play-button {
  display: none !important;
}

.h5-click-video {
  display: block !important;
  cursor: pointer;
}

.player-pause-triangle {
  width: 0;
  height: 0;
  margin-left: 14rpx;
  border-top: 40rpx solid transparent;
  border-bottom: 40rpx solid transparent;
  border-left: 62rpx solid rgba(255, 255, 255, 0.74);
}

.player-top,
.player-bottom {
  position: fixed;
  left: 0;
  right: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 24rpx 28rpx;
  box-sizing: border-box;
  pointer-events: none;
}

.player-top {
  top: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.62), transparent);
}

.player-title-overlay {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 5;
  display: flex;
  align-items: flex-end;
  justify-content: flex-start;
  padding: 90rpx 36rpx 92rpx;
  box-sizing: border-box;
  pointer-events: none;
  background: linear-gradient(0deg, rgba(0, 0, 0, 0.58), transparent);
}

.player-bottom {
  bottom: 0;
  justify-content: space-between;
  background: linear-gradient(0deg, rgba(0, 0, 0, 0.62), transparent);
}

.player-close,
.player-link,
.player-fullscreen {
  margin: 0;
  padding: 0 22rpx;
  height: 58rpx;
  line-height: 58rpx;
  border: none;
  border-radius: 999rpx;
  color: #fff;
  background: rgba(249, 115, 22, 0.92);
  font-size: 24rpx;
  font-weight: 700;
  pointer-events: auto;
}

.player-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #fff;
  font-size: 26rpx;
  font-weight: 700;
}

.player-title-mini {
  flex: none;
  width: 86vw;
  max-height: 82rpx;
  display: -webkit-box;
  overflow: hidden;
  text-align: left;
  white-space: normal;
  word-break: break-all;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  font-size: 28rpx;
  line-height: 1.45;
  text-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.48);
}

.player-fullscreen {
  background: rgba(37, 99, 235, 0.92);
}

.player-hint {
  color: rgba(255, 255, 255, 0.84);
  font-size: 24rpx;
  font-weight: 700;
}
</style>
