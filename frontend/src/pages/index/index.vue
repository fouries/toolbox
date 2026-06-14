<template>
  <view :class="['container', themeClass]">
    <view class="page-shell home-shell">
      <view class="hero-section">
        <view class="tool-search-wrap">
          <view class="search-box tool-search">
            <uni-icons type="search" size="18" color="#8a96a8"></uni-icons>
            <input
              class="search-input"
              placeholder="搜索"
              confirm-type="search"
              v-model="searchText"
              @confirm="submitSearch"
            />
            <text class="clear-search" v-if="searchText" @click="clearSearch">清空</text>
            <button class="search-submit" @click="submitSearch">搜索</button>
          </view>
        </view>

        <view class="quick-panel">
          <view class="quick-panel-title">
            <text class="quick-panel-title-text">热门工具</text>
            <text class="quick-panel-title-icon">🔥</text>
          </view>

          <scroll-view class="quick-tool-scroll" scroll-x="true" show-scrollbar="false">
            <view class="quick-tool-list">
              <view
                class="quick-tool-card"
                @click="goToTool(tool)"
                v-for="tool in popularTools"
                :key="tool.id"
              >
                <view class="quick-tool-icon" :style="{ background: tool.color }">
                  <text class="quick-icon-text">{{ tool.icon }}</text>
                </view>
                <view class="quick-tool-info">
                  <text class="quick-tool-name">{{ tool.name }}</text>
                </view>
              </view>
            </view>
          </scroll-view>
        </view>

        <view class="main-panel">
          <scroll-view class="category-scroll" scroll-x="true" show-scrollbar="false">
            <view class="category-list">
              <view
                class="category-item"
                :class="{ active: activeCategory === 'all' }"
                @click="activeCategory = 'all'"
              >全部</view>
              <view
                class="category-item"
                :class="{ active: activeCategory === cat.id }"
                @click="activeCategory = cat.id"
                v-for="cat in categories"
                :key="cat.id"
              >{{ cat.name }}</view>
            </view>
          </scroll-view>

          <view class="tool-grid" v-if="filteredTools.length">
            <view
              class="tool-item"
              :class="{ 'tool-not-implemented': !tool.implemented }"
              @click="goToTool(tool)"
              v-for="tool in filteredTools"
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

          <view class="empty-state" v-else>
            <text class="empty-icon">🔎</text>
            <text class="empty-title">没有找到相关工具</text>
            <text class="empty-desc">试试搜索：天气、油价、二维码、黄历</text>
            <button class="empty-btn" @click="clearSearch">清空搜索</button>
          </view>
        </view>
      </view>

      <view class="footer">
        <text class="footer-text">小巧的工具箱 v1.0</text>
        <!-- #ifdef H5 -->
        <view class="icp-beian" @click="navigateToBeian">
          <text>粤ICP备2026056747号</text>
        </view>
        <!-- #endif -->
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useTheme } from '@/utils/theme'
import { getPopularTools, recordToolClick, type ToolPopularityItem } from '@/api'
import { ref, computed, onMounted } from 'vue'

const { themeClass } = useTheme()

interface CategoryItem {
  id: string
  name: string
}

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

const searchText = ref('')
const activeCategory = ref('all')
const toolClickCounts = ref<Record<string, number>>({})

const categories = ref<CategoryItem[]>([
  { id: 'life', name: '生活服务' },
  { id: 'market', name: '资讯行情' },
  { id: 'code', name: '编码转换' },
  { id: 'other', name: '其他工具' }
])

const tools = ref<ToolItem[]>([
  { id: 'oil-price', name: '油价查询', desc: '全国各省今日汽柴油和原油价格', icon: '⛽', color: '#ff6b6b', category: 'life', path: '/pages/oil-price/index', implemented: true },
  { id: 'weather', name: '天气预报', desc: '查询城市实时天气和7天预报', icon: '🌤️', color: '#4ecdc4', category: 'life', path: '/pages/weather/index', implemented: true },
  { id: 'calendar', name: '黄历日历', desc: '农历节气与宜忌查询', icon: '📅', color: '#f97316', category: 'life', path: '/pages/calendar/index', implemented: true },
  { id: 'internet-news', name: '互联网资讯', desc: '互联网、AI 和科技行业动态', icon: '🌐', color: '#2563eb', category: 'market', path: '/pages/info-news/index?category=internet', implemented: true },
  { id: 'esports-news', name: '电竞资讯', desc: '电竞赛事与游戏产业消息', icon: '🎮', color: '#7c3aed', category: 'market', path: '/pages/info-news/index?category=esports', implemented: true },
  { id: 'auto-news', name: '汽车新闻', desc: '新车上市、行业政策和用车资讯', icon: '🚗', color: '#0f766e', category: 'market', path: '/pages/info-news/index?category=auto', implemented: true },
  { id: 'gold-price', name: '黄金行情', desc: '黄金价格与贵金属行情参考', icon: '🥇', color: '#f59e0b', category: 'market', path: '/pages/gold-price/index', implemented: true },
  { id: 'daily-brief', name: '每日简报', desc: '每天快速了解重要新闻和热点摘要', icon: '🗞️', color: '#4f46e5', category: 'market', path: '/pages/daily-brief/index', implemented: true },
  { id: 'weibo-hot', name: '微博热搜榜', desc: '查看微博实时热门话题排行', icon: '🔥', color: '#ef4444', category: 'market', path: '/pages/hot-search/index?platform=weibo', implemented: true },
  { id: 'baidu-hot', name: '百度热搜榜', desc: '查看百度搜索热点排行', icon: '🔎', color: '#2563eb', category: 'market', path: '/pages/hot-search/index?platform=baidu', implemented: true },
  { id: 'qrcode', name: '二维码生成', desc: '文本/网址一键生成二维码', icon: '📱', color: '#a29bfe', category: 'other', path: '/pages/qrcode/index', implemented: true }
])

const popularTools = computed(() => {
  const rankedTools = tools.value
    .filter(tool => tool.implemented)
    .slice()
    .sort((a, b) => {
      const diff = (toolClickCounts.value[b.id] || 0) - (toolClickCounts.value[a.id] || 0)
      if (diff !== 0) return diff
      return tools.value.findIndex(tool => tool.id === a.id) - tools.value.findIndex(tool => tool.id === b.id)
    })

  return rankedTools.slice(0, 10)
})

const filteredTools = computed(() => {
  let list = tools.value

  if (activeCategory.value !== 'all') {
    list = list.filter(t => t.category === activeCategory.value)
  }

  const keyword = searchText.value.trim().toLowerCase()
  if (keyword) {
    list = list.filter(t =>
      t.name.toLowerCase().includes(keyword) ||
      t.desc.toLowerCase().includes(keyword) ||
      t.id.toLowerCase().includes(keyword)
    )
  }

  return list
})

const clearSearch = () => {
  searchText.value = ''
  activeCategory.value = 'all'
}

const submitSearch = () => {
  searchText.value = searchText.value.trim()
}

const applyPopularity = (rankings: ToolPopularityItem[]) => {
  const counts: Record<string, number> = {}
  rankings.forEach(item => {
    counts[item.id] = item.clicks
  })
  toolClickCounts.value = counts
}

const loadPopularTools = async () => {
  try {
    const result = await getPopularTools(10)
    const rankings = (result.data || result.newslist || []) as ToolPopularityItem[]
    applyPopularity(rankings)
  } catch (error) {
    console.warn('加载热门工具失败', error)
  }
}

const refreshClickedTool = (toolId: string, clicks: number) => {
  toolClickCounts.value = {
    ...toolClickCounts.value,
    [toolId]: clicks
  }
}

const trackToolClick = async (toolId: string) => {
  try {
    const result = await recordToolClick(toolId)
    const clicked = (result.data || result.newslist) as ToolPopularityItem | undefined
    if (clicked?.id && typeof clicked.clicks === 'number') {
      refreshClickedTool(clicked.id, clicked.clicks)
    }
  } catch (error) {
    console.warn('记录工具点击失败', error)
  }
}

const goToTool = (tool: ToolItem) => {
  if (!tool.implemented) {
    uni.showToast({ title: `${tool.name}${tool.status || '开发中'}`, icon: 'none' })
    return
  }

  uni.navigateTo({ url: tool.path })
  void trackToolClick(tool.id)
}

const navigateToBeian = () => {
  // #ifdef H5
  const opened = window.open('https://beian.miit.gov.cn/', '_blank', 'noopener,noreferrer')
  if (opened) opened.opener = null
  // #endif
}

onMounted(() => {
  loadPopularTools()
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  background: linear-gradient(180deg, #eef5ff 0%, #f7f9fc 42%, #ffffff 100%);
  padding: 24rpx;
}

.home-shell {
  max-width: 1120px;
}

.hero-section {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
  padding: 30rpx;
  margin-bottom: 24rpx;
  border-radius: 34rpx;
  background: var(--theme-surface, rgba(255, 255, 255, 0.88)) !important;
  border: 2rpx solid var(--theme-border, rgba(255, 255, 255, 0.74));
  box-shadow: 0 18rpx 50rpx rgba(20, 35, 90, 0.08);
}

.hero-content,
.quick-panel,
.main-panel {
  position: relative;
  z-index: 1;
}

.hero-content {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.hero-copy {
  display: flex;
  flex-direction: column;
}

.hero-heading {
  display: flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: wrap;
  gap: 14rpx;
}

.hero-kicker {
  display: inline-flex;
  flex-shrink: 0;
  width: fit-content;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: var(--theme-primary-soft, #eef5ff);
  font-size: 24rpx;
  color: var(--theme-primary, #1677ff);
  font-weight: 700;
}

.hero-subtitle {
  margin-top: 18rpx;
  max-width: 720px;
  font-size: 28rpx;
  color: var(--theme-text-secondary, #667085);
  line-height: 1.7;
}

.search-box {
  display: flex;
  align-items: center;
  background: var(--theme-primary-soft, rgba(246, 248, 251, 0.92));
  border-radius: 999rpx;
  padding: 20rpx 28rpx;
  border: 2rpx solid var(--theme-border, rgba(226, 232, 240, 0.9));
}

.tool-search-wrap {
  display: none;
  margin: 0;
}

.tool-search {
  gap: 12rpx;
  background: linear-gradient(135deg, var(--theme-primary-soft, #eef5ff) 0%, var(--theme-surface, #ffffff) 100%);
  border-color: var(--theme-border, rgba(226, 232, 240, 0.9));
  box-shadow: inset 0 0 0 2rpx rgba(255, 255, 255, 0.58), 0 10rpx 24rpx rgba(20, 35, 90, 0.05);
}

.search-submit {
  flex-shrink: 0;
  height: 56rpx;
  line-height: 56rpx;
  margin: 0;
  padding: 0 24rpx;
  border-radius: 999rpx;
  background: var(--theme-primary, #1677ff);
  color: #fff;
  font-size: 24rpx;
  font-weight: 800;
}

.search-submit::after {
  border: 0;
}

.theme-night .tool-search {
  background: rgba(15, 23, 42, 0.62);
  border-color: rgba(148, 163, 184, 0.26);
  box-shadow: inset 0 0 0 2rpx rgba(255, 255, 255, 0.04), 0 10rpx 24rpx rgba(0, 0, 0, 0.16);
}

.search-input {
  flex: 1;
  margin-left: 15rpx;
  font-size: 28rpx;
  color: var(--theme-text, #243044);
}

.clear-search {
  margin-left: 16rpx;
  font-size: 24rpx;
  color: var(--theme-primary, #1677ff);
  font-weight: 700;
}

.hero-meta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10rpx;
}

.hero-meta-card {
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
  min-width: 0;
  padding: 8rpx 12rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.58);
  border: 2rpx solid var(--theme-border, rgba(226, 232, 240, 0.6));
  box-shadow: 0 6rpx 16rpx rgba(20, 35, 90, 0.04);
}

.meta-icon {
  width: 34rpx;
  height: 34rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: inset 0 0 0 1rpx rgba(255, 255, 255, 0.58), 0 4rpx 10rpx rgba(20, 35, 90, 0.06);
}

.meta-icon-free {
  background: linear-gradient(135deg, #ff9f43 0%, #ff6b6b 100%);
}

.meta-icon-tools {
  background: linear-gradient(135deg, #4ecdc4 0%, #00b894 100%);
}

.meta-icon-cross {
  background: linear-gradient(135deg, #74b9ff 0%, #a29bfe 100%);
}

.meta-icon-text {
  font-size: 20rpx;
  line-height: 1;
}

.meta-label {
  display: block;
  font-size: 21rpx;
  color: var(--theme-text-secondary, #667085);
  line-height: 1.2;
  white-space: nowrap;
}

.theme-light .hero-meta-card,
.theme-warm .hero-meta-card,
.theme-fresh .hero-meta-card,
.theme-minimal .hero-meta-card,
.theme-light .quick-tool-card,
.theme-warm .quick-tool-card,
.theme-fresh .quick-tool-card,
.theme-minimal .quick-tool-card,
.theme-light .tool-search,
.theme-warm .tool-search,
.theme-fresh .tool-search,
.theme-minimal .tool-search {
  background: linear-gradient(135deg, var(--theme-primary-soft, #eef5ff) 0%, var(--theme-surface, #ffffff) 100%) !important;
  border-color: var(--theme-border, rgba(226, 232, 240, 0.9)) !important;
}

.theme-light .hero-meta-card,
.theme-warm .hero-meta-card,
.theme-fresh .hero-meta-card,
.theme-minimal .hero-meta-card,
.theme-light .quick-tool-card,
.theme-warm .quick-tool-card,
.theme-fresh .quick-tool-card,
.theme-minimal .quick-tool-card {
  box-shadow: 0 10rpx 24rpx rgba(20, 35, 90, 0.04) !important;
}

.theme-night .quick-tool-card,
.theme-night .hero-meta-card {
  background: rgba(30, 41, 59, 0.86);
  border-color: rgba(148, 163, 184, 0.3);
  box-shadow: 0 10rpx 28rpx rgba(0, 0, 0, 0.2);
}

.theme-night .hero-meta-card {
  background: rgba(15, 23, 42, 0.62);
  box-shadow: 0 6rpx 16rpx rgba(0, 0, 0, 0.16);
}

.theme-night .meta-label {
  color: #d5deec;
}

.quick-panel {
  background: rgba(255, 255, 255, 0.92);
  border-radius: 30rpx;
  padding: 24rpx;
  border: 2rpx solid rgba(238, 242, 247, 0.9);
  box-shadow: 0 12rpx 34rpx rgba(20, 35, 90, 0.06);
}

.main-panel {
  padding-top: 6rpx;
}

.quick-panel-header,
.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
  margin-bottom: 22rpx;
}

.section-kicker,
.section-title,
.section-count {
  display: block;
}

.section-kicker {
  margin-bottom: 6rpx;
  font-size: 22rpx;
  color: var(--theme-primary, #1677ff);
  font-weight: 700;
}

.section-title {
  font-size: 34rpx;
  color: var(--theme-text, #243044);
  font-weight: 800;
  line-height: 1.2;
}

.section-count {
  flex-shrink: 0;
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: var(--theme-primary-soft, #eef5ff);
  color: var(--theme-primary, #1677ff);
  font-size: 22rpx;
  font-weight: 700;
}

.quick-panel-title {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-bottom: 18rpx;
}

.quick-panel-title-text {
  font-size: 32rpx;
  line-height: 1.2;
  color: var(--theme-text, #243044);
  font-weight: 800;
}

.quick-panel-title-icon {
  font-size: 32rpx;
  line-height: 1;
}

.quick-tool-scroll {
  width: 100%;
  white-space: nowrap;
}

.quick-tool-list {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  gap: 8rpx;
}

.quick-tool-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 0 0 112rpx;
  min-width: 0;
  min-height: 88rpx;
  gap: 6rpx;
  padding: 10rpx 6rpx;
  border-radius: 16rpx;
  background: linear-gradient(135deg, var(--theme-surface, rgba(255, 255, 255, 0.94)) 0%, var(--theme-primary-soft, rgba(238, 245, 255, 0.86)) 100%);
  border: 2rpx solid var(--theme-border, rgba(238, 242, 247, 0.9));
  box-shadow: 0 6rpx 18rpx rgba(20, 35, 90, 0.04);
}

.quick-tool-icon {
  width: 40rpx;
  height: 40rpx;
  border-radius: 14rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--theme-hero, linear-gradient(135deg, #1677ff 0%, #31c48d 100%));
  box-shadow: inset 0 0 0 2rpx rgba(255, 255, 255, 0.42), 0 6rpx 14rpx rgba(20, 35, 90, 0.07);
}

.quick-icon-text {
  font-size: 22rpx;
}

.quick-tool-info {
  width: 100%;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.quick-tool-name {
  font-size: 20rpx;
  line-height: 1.2;
  color: var(--theme-text, #243044);
  font-weight: 800;
  text-align: center;
  white-space: nowrap;
}

.main-panel {
  padding-top: 6rpx;
}

.category-scroll {
  white-space: nowrap;
  margin-bottom: 24rpx;
}

.category-list {
  display: flex;
  padding: 6rpx 0 10rpx;
}

.category-item {
  padding: 15rpx 30rpx;
  margin-right: 18rpx;
  background: rgba(246, 248, 251, 0.88);
  border: 2rpx solid rgba(238, 242, 247, 0.95);
  border-radius: 999rpx;
  font-size: 26rpx;
  color: var(--theme-text-secondary, #667085);
  white-space: nowrap;
}

.category-item.active {
  background: var(--theme-primary, #1677ff);
  border-color: var(--theme-primary, #1677ff);
  color: #fff;
  box-shadow: 0 10rpx 24rpx rgba(22, 119, 255, 0.18);
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.tool-item {
  position: relative;
  min-height: 156rpx;
  background: rgba(255, 255, 255, 0.94);
  border-radius: 22rpx;
  padding: 22rpx 18rpx 20rpx;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-start;
  text-align: left;
  border: 2rpx solid rgba(238, 242, 247, 0.95);
  box-shadow: 0 8rpx 22rpx rgba(20, 35, 90, 0.045);
}

.tool-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 14rpx;
  box-shadow: inset 0 0 0 2rpx rgba(255, 255, 255, 0.38), 0 8rpx 18rpx rgba(20, 35, 90, 0.08);
}

.icon-text { font-size: 36rpx; }

.tool-name {
  font-size: 28rpx;
  font-weight: 800;
  color: var(--theme-text, #243044);
  margin-bottom: 6rpx;
  line-height: 1.2;
}

.tool-desc {
  font-size: 22rpx;
  color: var(--theme-text-secondary, #7a869a);
  line-height: 1.38;
}

.tool-not-implemented { opacity: 0.58; }

.coming-soon-badge {
  position: absolute;
  top: 15rpx;
  right: 15rpx;
  font-size: 18rpx;
  padding: 4rpx 12rpx;
  background: #ff9800;
  color: #fff;
  border-radius: 20rpx;
}

.empty-state {
  padding: 70rpx 20rpx;
  text-align: center;
  background: rgba(248, 251, 255, 0.86);
  border-radius: 24rpx;
  border: 2rpx dashed #dce8f8;
}

.empty-icon,
.empty-title,
.empty-desc {
  display: block;
}

.empty-icon { font-size: 76rpx; margin-bottom: 16rpx; }
.empty-title { font-size: 30rpx; color: var(--theme-text, #243044); font-weight: 800; }
.empty-desc { margin: 12rpx 0 24rpx; font-size: 24rpx; color: var(--theme-text-secondary, #7a869a); }

.empty-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 220rpx;
  height: 70rpx;
  line-height: 70rpx;
  border-radius: 999rpx;
  background: var(--theme-primary, #1677ff);
  color: #fff;
  font-size: 26rpx;
}

.footer {
  margin-top: 40rpx;
  text-align: center;
  padding-bottom: 40rpx;
}

.footer-text {
  font-size: 24rpx;
  color: var(--theme-text-muted, #9aa6b8);
}

.icp-beian {
  margin-top: 10rpx;
  font-size: 22rpx;
  color: var(--theme-text-muted, #8b97a8);
  cursor: pointer;
}

.icp-beian:active,
.quick-tool-card:active,
.tool-item:active { opacity: 0.72; }

@media (min-width: 768px) {
  .container { padding: 32px 24px; }

  .hero-section {
    display: grid;
    grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.85fr);
    align-items: stretch;
    gap: 24px;
    padding: 36px;
    border-radius: 28px;
  }

  .hero-subtitle { font-size: 18px; }
  .hero-heading {
    flex-direction: row;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
  }
  .hero-meta-row { gap: 8px; }
  .hero-meta-card {
    gap: 6px;
    padding: 5px 9px;
    border-radius: 999px;
  }
  .meta-icon { width: 20px; height: 20px; }
  .meta-icon-text { font-size: 13px; }
  .meta-label { font-size: 13px; }
  .search-box { padding: 14px 20px; }
  .tool-search-wrap { margin: 0; }
  .tool-search { max-width: none; }
  .search-input { font-size: 16px; }
  .search-submit {
    height: 34px;
    line-height: 34px;
    padding: 0 18px;
    font-size: 14px;
  }
  .quick-panel {
    grid-column: 1 / -1;
    padding: 28px;
    border-radius: 24px;
  }

  .main-panel {
    grid-column: 1 / -1;
    padding-top: 4px;
  }

  .quick-tool-list {
    gap: 8px;
  }

  .quick-tool-card {
    flex-basis: 92px;
    min-height: 60px;
    padding: 8px 6px;
    border-radius: 12px;
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
    cursor: pointer;
  }

  .quick-tool-icon {
    width: 26px;
    height: 26px;
    border-radius: 9px;
  }

  .quick-icon-text { font-size: 14px; }
  .quick-tool-name { font-size: 12px; }

  .quick-tool-card:hover {
    transform: translateY(-2px);
    border-color: rgba(22, 119, 255, 0.24);
    box-shadow: 0 12px 28px rgba(20, 35, 90, 0.08);
  }

  .tool-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
  }

  .tool-item {
    min-height: 136px;
    padding: 20px 18px 18px;
    border-radius: 18px;
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
    cursor: pointer;
  }

  .tool-icon {
    width: 44px;
    height: 44px;
    border-radius: 14px;
    margin-bottom: 12px;
  }

  .icon-text { font-size: 22px; }

  .tool-name { font-size: 16px; }
  .tool-desc { font-size: 13px; }

  .tool-item:hover {
    transform: translateY(-2px);
    border-color: rgba(22, 119, 255, 0.24);
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
  }
}
</style>
