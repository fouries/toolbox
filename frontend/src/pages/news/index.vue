<template>
  <view :class="['container', themeClass]">
    <view class="page-shell news-shell">
      <view class="hot-hero">
        <view>
          <text class="hero-kicker">HOT LIST</text>
          <text class="hero-title">热榜</text>
          <text class="hero-desc">百度热搜、抖音热搜、每日简报和行业资讯集中查看。</text>
        </view>
      </view>

      <view class="section-card primary-card">
        <view class="section-header">
          <view>
            <text class="section-kicker">实时热点</text>
            <text class="section-title">热搜榜单</text>
          </view>
          <text class="section-badge">实时更新</text>
        </view>
        <view class="featured-grid">
          <view
            class="featured-item"
            v-for="tool in hotTools"
            :key="tool.id"
            @click="goToTool(tool)"
          >
            <view class="featured-icon" :style="{ background: tool.color }">
              <text>{{ tool.icon }}</text>
            </view>
            <view class="featured-info">
              <text class="featured-name">{{ tool.name }}</text>
              <text class="featured-desc">{{ tool.desc }}</text>
            </view>
            <text class="featured-arrow">›</text>
          </view>
        </view>
      </view>

      <view class="section-card brief-card" @click="goToTool(dailyBriefTool)">
        <view class="brief-left">
          <view class="brief-icon">📰</view>
          <view class="brief-info">
            <text class="brief-title">每日简报</text>
            <text class="brief-desc">每天一页看完重点新闻和热门事件</text>
          </view>
        </view>
        <text class="brief-action">查看</text>
      </view>

      <view class="section-card">
        <view class="section-header">
          <view>
            <text class="section-kicker">NEWS</text>
            <text class="section-title">资讯频道</text>
          </view>
        </view>
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
  </view>
</template>

<script setup lang="ts">
import { useTheme } from '@/utils/theme'

interface ToolItem {
  id: string
  name: string
  desc: string
  icon: string
  color: string
  category: string
  path: string
  implemented: boolean
  status?: string
}

const { themeClass } = useTheme()

const hotTools: ToolItem[] = [
  { id: 'baidu-hot', name: '百度热搜榜', desc: '查看百度搜索热点排行和详情', icon: '🔎', color: '#2563eb', category: 'hot', path: '/pages/hot-search/index?platform=baidu', implemented: true },
  { id: 'douyin-hot', name: '抖音热搜榜', desc: '抖音热门搜索排行和相关视频', icon: '🎵', color: '#111827', category: 'hot', path: '/pages/hot-search/index?platform=douyin', implemented: true }
]

const dailyBriefTool: ToolItem = {
  id: 'daily-brief',
  name: '每日简报',
  desc: '每日热点简明速览',
  icon: '📰',
  color: '#4f46e5',
  category: 'brief',
  path: '/pages/daily-brief/index',
  implemented: true
}

const newsTools: ToolItem[] = [
  { id: 'internet-news', name: '互联网资讯', desc: '互联网、AI 和科技行业动态', icon: '🌐', color: '#2563eb', category: 'news', path: '/pages/info-news/index?category=internet', implemented: true },
  { id: 'esports-news', name: '电竞资讯', desc: '电竞赛事与游戏产业消息', icon: '🎮', color: '#7c3aed', category: 'news', path: '/pages/info-news/index?category=esports', implemented: true },
  { id: 'auto-news', name: '汽车新闻', desc: '新车上市、行业政策和用车资讯', icon: '🚗', color: '#0f766e', category: 'news', path: '/pages/info-news/index?category=auto', implemented: true }
]

const goToTool = (tool: ToolItem) => {
  if (!tool.implemented) {
    uni.showToast({ title: `${tool.name}${tool.status || '开发中'}`, icon: 'none' })
    return
  }
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
  background: linear-gradient(180deg, #fff7ed 0%, #f8fafc 48%, #ffffff 100%);
}

.news-shell {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
  box-sizing: border-box;
}

.hot-hero,
.section-card {
  border: 2rpx solid var(--theme-border, rgba(238, 242, 247, 0.92));
  background: var(--theme-surface, rgba(255, 255, 255, 0.94));
  box-shadow: 0 14rpx 40rpx rgba(194, 65, 12, 0.07);
}

.hot-hero {
  padding: 34rpx 30rpx;
  border-radius: 34rpx;
  background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(255,247,237,0.94));
}

.hero-kicker,
.hero-title,
.hero-desc,
.section-kicker,
.section-title {
  display: block;
}

.hero-kicker,
.section-kicker {
  color: #f97316;
  font-size: 22rpx;
  font-weight: 900;
  letter-spacing: 1rpx;
}

.hero-title {
  margin-top: 10rpx;
  color: var(--theme-text, #17233d);
  font-size: 48rpx;
  line-height: 1.16;
  font-weight: 900;
}

.hero-desc {
  margin-top: 12rpx;
  max-width: 720px;
  color: var(--theme-text-secondary, #667085);
  font-size: 27rpx;
  line-height: 1.6;
}

.section-card {
  padding: 26rpx;
  border-radius: 30rpx;
}

.primary-card {
  background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(255,247,237,0.92));
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  margin-bottom: 22rpx;
}

.section-title {
  margin-top: 6rpx;
  color: var(--theme-text, #243044);
  font-size: 34rpx;
  font-weight: 900;
}

.section-badge {
  flex-shrink: 0;
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: #ffedd5;
  color: #ea580c;
  font-size: 22rpx;
  font-weight: 800;
}

.featured-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16rpx;
}

.featured-item {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 22rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.9);
  border: 2rpx solid rgba(254, 215, 170, 0.7);
}

.featured-icon,
.brief-icon {
  width: 76rpx;
  height: 76rpx;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
  font-size: 38rpx;
  box-shadow: inset 0 0 0 2rpx rgba(255,255,255,0.36), 0 8rpx 20rpx rgba(15,23,42,0.1);
}

.featured-info,
.brief-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.featured-name,
.brief-title {
  color: var(--theme-text, #17233d);
  font-size: 30rpx;
  font-weight: 900;
}

.featured-desc,
.brief-desc {
  color: var(--theme-text-secondary, #7a869a);
  font-size: 24rpx;
  line-height: 1.42;
}

.featured-arrow {
  color: #fb923c;
  font-size: 46rpx;
  font-weight: 300;
}

.brief-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  background: linear-gradient(135deg, #4f46e5, #2563eb);
  border-color: transparent;
  box-shadow: 0 16rpx 40rpx rgba(37, 99, 235, 0.22);
}

.brief-left {
  display: flex;
  align-items: center;
  gap: 18rpx;
  min-width: 0;
}

.brief-icon {
  background: rgba(255,255,255,0.18);
}

.brief-title,
.brief-desc,
.brief-action {
  color: #fff;
}

.brief-desc {
  opacity: 0.88;
}

.brief-action {
  flex-shrink: 0;
  padding: 10rpx 20rpx;
  border-radius: 999rpx;
  background: rgba(255,255,255,0.18);
  font-size: 24rpx;
  font-weight: 900;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.tool-item {
  position: relative;
  background: var(--theme-surface, #ffffff);
  border: 2rpx solid var(--theme-border, #eef2f7);
  border-radius: 22rpx;
  padding: 30rpx 22rpx 26rpx;
  text-align: left;
  min-height: 184rpx;
  box-shadow: 0 8rpx 22rpx rgba(20, 35, 90, 0.045);
}

.tool-not-implemented {
  opacity: 0.6;
}

.tool-icon {
  width: 78rpx;
  height: 78rpx;
  border-radius: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18rpx;
}

.icon-text {
  font-size: 38rpx;
  line-height: 1;
}

.tool-name {
  display: block;
  font-size: 29rpx;
  font-weight: 900;
  color: var(--theme-text, #243044);
  margin-bottom: 10rpx;
}

.tool-desc {
  display: block;
  font-size: 23rpx;
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

.featured-item:active,
.brief-card:active,
.tool-item:active {
  opacity: 0.72;
}

@media (min-width: 768px) {
  .container {
    padding: 32px 24px;
  }

  .hot-hero {
    padding: 34px 32px;
    border-radius: 28px;
  }

  .hero-title { font-size: 38px; }
  .hero-desc { font-size: 16px; }

  .section-card {
    padding: 28px;
    border-radius: 24px;
  }

  .featured-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
  }

  .featured-item,
  .tool-item,
  .brief-card {
    cursor: pointer;
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
  }

  .featured-item:hover,
  .tool-item:hover,
  .brief-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
  }

  .tool-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
  }

  .tool-item {
    min-height: 150px;
    padding: 22px 18px 18px;
    border-radius: 18px;
  }

  .tool-icon,
  .featured-icon,
  .brief-icon {
    width: 46px;
    height: 46px;
    border-radius: 14px;
  }

  .icon-text,
  .featured-icon,
  .brief-icon { font-size: 22px; }
  .tool-name,
  .featured-name,
  .brief-title { font-size: 17px; }
  .tool-desc,
  .featured-desc,
  .brief-desc { font-size: 13px; }
}
</style>
