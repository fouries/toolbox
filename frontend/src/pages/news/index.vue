<template>
  <view :class="['container', themeClass]">
    <view class="page-shell news-shell">
      <view class="tool-grid">
        <view
          class="tool-item news-item"
          :class="{ 'tool-not-implemented': !tool.implemented }"
          @click="goToTool(tool)"
          v-for="tool in newsTools"
          :key="tool.id"
        >
          <view class="tool-icon" :style="{ background: tool.color }">
            <text class="icon-text">{{ tool.icon }}</text>
          </view>
          <text class="tool-name">{{ tool.name }}</text>
          <text class="tool-desc">{{ tool.desc }}</text>
          <text class="coming-soon-badge" v-if="!tool.implemented">{{ tool.status || '开发中' }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useTheme } from '@/utils/theme'
import type { ToolItem } from '@/types'

const { themeClass } = useTheme()

const tools: ToolItem[] = [
  { id: 'internet-news', name: '互联网资讯', desc: '互联网、AI 和科技行业动态', icon: '🌐', color: '#2563eb', category: 'news', path: '/pages/info-news/index?category=internet', implemented: true },
  { id: 'esports-news', name: '电竞资讯', desc: '电竞赛事与游戏产业消息', icon: '🎮', color: '#7c3aed', category: 'news', path: '/pages/info-news/index?category=esports', implemented: true },
  { id: 'auto-news', name: '汽车新闻', desc: '新车上市、行业政策和用车资讯', icon: '🚗', color: '#0f766e', category: 'news', path: '/pages/info-news/index?category=auto', implemented: true },
  { id: 'baidu-hot', name: '百度热搜榜', desc: '查看百度搜索热点排行', icon: '🔎', color: '#2563eb', category: 'news', path: '/pages/hot-search/index?platform=baidu', implemented: true },
]

const newsTools = tools.filter(tool => tool.implemented)

const goToTool = (tool: ToolItem) => {
  if (!tool.implemented) return
  if (tool.path) {
    uni.navigateTo({ url: tool.path })
  }
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 24rpx;
  background: var(--theme-bg, #f5f7fb);
}

.page-shell {
  box-sizing: border-box;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20rpx;
}

.tool-item {
  position: relative;
  background: var(--theme-surface, #ffffff);
  border: 2rpx solid var(--theme-border, #eef2f7);
  border-radius: 20rpx;
  padding: 32rpx 24rpx 28rpx;
  text-align: center;
  min-height: 200rpx;
}

.tool-not-implemented {
  opacity: 0.6;
}

.tool-icon {
  width: 88rpx;
  height: 88rpx;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20rpx;
}

.icon-text {
  font-size: 44rpx;
  line-height: 1;
}

.tool-name {
  display: block;
  font-size: 30rpx;
  font-weight: 600;
  color: var(--theme-text, #243044);
  margin-bottom: 10rpx;
}

.tool-desc {
  display: block;
  font-size: 24rpx;
  color: var(--theme-text-muted, #7a869a);
  line-height: 1.5;
}

.coming-soon-badge {
  position: absolute;
  top: 16rpx;
  right: 16rpx;
  background: #f1f5f9;
  color: #64748b;
  font-size: 20rpx;
  padding: 6rpx 12rpx;
  border-radius: 12rpx;
}

.tool-item:active {
  opacity: 0.72;
}

@media (min-width: 768px) {
  .container {
    padding: 32px 24px;
  }

  .tool-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
  }

  .tool-item {
    min-height: 136px;
    padding: 20px 18px 18px;
    border-radius: 18px;
  }

  .tool-icon {
    width: 44px;
    height: 44px;
    border-radius: 14px;
    margin-bottom: 12px;
  }

  .icon-text {
    font-size: 22px;
  }

  .tool-name {
    font-size: 16px;
  }

  .tool-desc {
    font-size: 13px;
  }
}
</style>
