<template>
  <view :class="['container', themeClass]">
    <view class="page-shell home-shell">
      <view class="hero-section">
        <view class="hero-content">
          <text class="hero-kicker">小巧的工具箱</text>
          <text class="hero-title">常用工具、热榜资讯，一页直达</text>
          <text class="hero-subtitle">搜索工具名称或关键词，也可以从最近使用和今日速览快速进入。</text>
        </view>

        <view class="tool-search-wrap">
          <view class="search-box tool-search">
            <uni-icons type="search" size="18" color="#8a96a8"></uni-icons>
            <input
              class="search-input"
              placeholder="搜索工具、热搜、资讯..."
              confirm-type="search"
              v-model="searchText"
              @confirm="submitSearch"
            />
            <text class="clear-search" v-if="searchText" @click="clearSearch">清空</text>
            <button class="search-submit" @click="submitSearch">搜索</button>
          </view>
        </view>

        <view class="overview-panel">
          <view
            class="overview-card"
            v-for="item in todayOverview"
            :key="item.id"
            @click="goToOverview(item)"
          >
            <view class="overview-icon" :style="{ background: item.color }">
              <text>{{ item.icon }}</text>
            </view>
            <view class="overview-info">
              <text class="overview-label">{{ item.label }}</text>
              <text class="overview-value">{{ item.value }}</text>
              <text class="overview-desc">{{ item.desc }}</text>
            </view>
          </view>
        </view>

        <view class="quick-panel" v-if="favoriteTools.length">
          <view class="quick-panel-title">
            <text class="quick-panel-title-text">我的收藏</text>
            <text class="quick-panel-title-icon">⭐</text>
          </view>
          <scroll-view class="quick-tool-scroll" scroll-x="true" show-scrollbar="false">
            <view class="quick-tool-list">
              <view
                class="quick-tool-card"
                @click="goToTool(tool)"
                v-for="tool in favoriteTools"
                :key="tool.id"
              >
                <button
                  class="favorite-toggle active"
                  @click.stop="toggleFavorite(tool)"
                >★</button>
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

        <view class="quick-panel" v-if="recentTools.length">
          <view class="quick-panel-title">
            <text class="quick-panel-title-text">最近使用</text>
            <text class="quick-panel-title-icon">🕘</text>
          </view>
          <scroll-view class="quick-tool-scroll" scroll-x="true" show-scrollbar="false">
            <view class="quick-tool-list">
              <view
                class="quick-tool-card"
                @click="goToTool(tool)"
                v-for="tool in recentTools"
                :key="tool.id"
              >
                <button
                  class="favorite-toggle"
                  :class="{ active: isFavorite(tool.id) }"
                  @click.stop="toggleFavorite(tool)"
                >{{ isFavorite(tool.id) ? '★' : '☆' }}</button>
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
                <button
                  class="favorite-toggle"
                  :class="{ active: isFavorite(tool.id) }"
                  @click.stop="toggleFavorite(tool)"
                >{{ isFavorite(tool.id) ? '★' : '☆' }}</button>
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
          <view class="panel-header">
            <view>
              <text class="section-kicker">TOOLS</text>
              <text class="section-title">全部工具</text>
            </view>
            <text class="section-count">{{ filteredTools.length }} 个</text>
          </view>

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
              <button
                class="favorite-toggle tool-favorite-toggle"
                :class="{ active: isFavorite(tool.id) }"
                v-if="tool.implemented"
                @click.stop="toggleFavorite(tool)"
              >{{ isFavorite(tool.id) ? '★' : '☆' }}</button>
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
            <text class="empty-desc">试试搜索：天气、油价、二维码、热搜</text>
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
import {
  addUserFavorite,
  ensureAnonymousUser,
  getPopularTools,
  getUserFavorites,
  recordToolClick,
  removeUserFavorite,
  type ToolPopularityItem
} from '@/api'
import { ref, computed, onMounted } from 'vue'

const { themeClass } = useTheme()
const RECENT_TOOLS_KEY = 'toolbox_recent_tools'
const TOOLBOX_USER_KEY = 'toolbox_user_key'
const FAVORITE_TOOLS_KEY = 'toolbox_favorite_tools'

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
  keywords?: string[]
}

interface OverviewItem {
  id: string
  label: string
  value: string
  desc: string
  icon: string
  color: string
  path: string
  tab?: boolean
}

const searchText = ref('')
const activeCategory = ref('all')
const toolClickCounts = ref<Record<string, number>>({})
const recentToolIds = ref<string[]>([])
const favoriteToolIds = ref<string[]>([])
const userKey = ref('')

const categories = ref<CategoryItem[]>([
  { id: 'life', name: '生活查询' },
  { id: 'market', name: '市场行情' },
  { id: 'utility', name: '实用工具' },
  { id: 'calendar', name: '日历文化' },
  { id: 'news', name: '热榜资讯' }
])

const HIDDEN_TOOL_IDS = new Set(['password'])

const visibleTools = () => tools.value.filter(tool => !HIDDEN_TOOL_IDS.has(tool.id))

const tools = ref<ToolItem[]>([
  { id: 'weather', name: '天气预报', desc: '城市实时天气和7天预报', icon: '🌤️', color: '#4ecdc4', category: 'life', path: '/pages/weather/index', implemented: true, keywords: ['天气', '预报', '城市'] },
  { id: 'oil-price', name: '油价查询', desc: '全国各省汽柴油价格', icon: '⛽', color: '#ff6b6b', category: 'life', path: '/pages/oil-price/index', implemented: true, keywords: ['油价', '汽油', '柴油'] },
  { id: 'gold-price', name: '黄金行情', desc: '黄金与贵金属行情参考', icon: '🥇', color: '#f59e0b', category: 'market', path: '/pages/gold-price/index', implemented: true, keywords: ['黄金', '金价', '行情'] },
  { id: 'qrcode', name: '二维码生成', desc: '文本/网址一键生成二维码', icon: '📱', color: '#a29bfe', category: 'utility', path: '/pages/qrcode/index', implemented: true, keywords: ['二维码', '网址', '文本'] },
  { id: 'password', name: '密码生成器', desc: '生成安全随机密码', icon: '🔐', color: '#6366f1', category: 'utility', path: '/pages/password/index', implemented: true, keywords: ['密码', '随机', '安全'] },
  { id: 'calendar', name: '黄历日历', desc: '农历节气与宜忌查询', icon: '📅', color: '#f97316', category: 'calendar', path: '/pages/calendar/index', implemented: true, keywords: ['黄历', '农历', '日历'] },
  { id: 'history-today', name: '历史上的今天', desc: '查看今日历史事件', icon: '📜', color: '#b45309', category: 'calendar', path: '/pages/history-today/index', implemented: true, keywords: ['历史', '今天'] },
  { id: 'solar-terms', name: '二十四节气', desc: '节气日期与传统知识', icon: '🌿', color: '#16a34a', category: 'calendar', path: '/pages/solar-terms/index', implemented: true, keywords: ['节气', '二十四节气'] },
  { id: 'baidu-hot', name: '百度热搜榜', desc: '查看百度搜索热点排行', icon: '🔎', color: '#2563eb', category: 'news', path: '/pages/hot-search/index?platform=baidu', implemented: true, keywords: ['百度', '热搜', '热榜'] },
  { id: 'douyin-hot', name: '抖音热搜榜', desc: '查看抖音热门搜索排行', icon: '🎵', color: '#111827', category: 'news', path: '/pages/hot-search/index?platform=douyin', implemented: true, keywords: ['抖音', '热搜', '视频'] },
  { id: 'daily-brief', name: '每日简报', desc: '每日热点简明速览', icon: '📰', color: '#4f46e5', category: 'news', path: '/pages/daily-brief/index', implemented: true, keywords: ['简报', '新闻', '热点'] },
  { id: 'info-news', name: '资讯查询', desc: '互联网、AI、汽车与电竞资讯', icon: '🌐', color: '#0ea5e9', category: 'news', path: '/pages/info-news/index?category=internet', implemented: true, keywords: ['资讯', '新闻', '互联网', 'AI'] }
])

const todayOverview = computed<OverviewItem[]>(() => {
  const date = new Date()
  const month = date.getMonth() + 1
  const day = date.getDate()
  return [
    { id: 'today', label: '今日', value: `${month}月${day}日`, desc: '黄历、节气、历史事件', icon: '📅', color: '#f97316', path: '/pages/calendar/index' },
    { id: 'hot', label: '热榜', value: '百度 / 抖音', desc: '热点内容集中查看', icon: '🔥', color: '#ef4444', path: '/pages/news/index', tab: true },
    { id: 'tools', label: '工具', value: `${visibleTools().filter(tool => tool.implemented).length} 个可用`, desc: '生活查询和实用工具', icon: '🧰', color: '#2563eb', path: '' }
  ]
})

const popularTools = computed(() => {
  const rankedTools = visibleTools()
    .filter(tool => tool.implemented)
    .slice()
    .sort((a, b) => {
      const diff = (toolClickCounts.value[b.id] || 0) - (toolClickCounts.value[a.id] || 0)
      if (diff !== 0) return diff
      return tools.value.findIndex(tool => tool.id === a.id) - tools.value.findIndex(tool => tool.id === b.id)
    })

  return rankedTools.slice(0, 10)
})

const recentTools = computed(() => {
  const available = visibleTools().filter(tool => tool.implemented)
  return recentToolIds.value
    .map(id => available.find(tool => tool.id === id))
    .filter((tool): tool is ToolItem => Boolean(tool))
    .slice(0, 10)
})

const favoriteTools = computed(() => {
  const available = visibleTools().filter(tool => tool.implemented)
  return favoriteToolIds.value
    .map(id => available.find(tool => tool.id === id))
    .filter((tool): tool is ToolItem => Boolean(tool))
    .slice(0, 10)
})

const filteredTools = computed(() => {
  let list = visibleTools()

  if (activeCategory.value !== 'all') {
    list = list.filter(t => t.category === activeCategory.value)
  }

  const keyword = searchText.value.trim().toLowerCase()
  if (keyword) {
    list = list.filter(t => {
      const keywordText = [t.id, t.name, t.desc, t.category, ...(t.keywords || [])].join(' ').toLowerCase()
      return keywordText.includes(keyword)
    })
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

const loadRecentTools = () => {
  try {
    const stored = uni.getStorageSync(RECENT_TOOLS_KEY)
    recentToolIds.value = Array.isArray(stored) ? stored.filter(item => typeof item === 'string') : []
  } catch (error) {
    console.warn('加载最近使用失败', error)
  }
}

const generateUserKey = () => `anon_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 12)}`

const ensureUserKey = () => {
  if (userKey.value) return userKey.value
  try {
    const stored = uni.getStorageSync(TOOLBOX_USER_KEY)
    const key = typeof stored === 'string' && stored.length >= 8 ? stored : generateUserKey()
    userKey.value = key
    if (key !== stored) uni.setStorageSync(TOOLBOX_USER_KEY, key)
    return key
  } catch (error) {
    console.warn('初始化用户标识失败', error)
    const key = generateUserKey()
    userKey.value = key
    return key
  }
}

const saveFavoriteTools = () => {
  try {
    uni.setStorageSync(FAVORITE_TOOLS_KEY, favoriteToolIds.value)
  } catch (error) {
    console.warn('保存收藏失败', error)
  }
}

const loadCachedFavorites = () => {
  try {
    const stored = uni.getStorageSync(FAVORITE_TOOLS_KEY)
    favoriteToolIds.value = Array.isArray(stored) ? stored.filter(item => typeof item === 'string') : []
  } catch (error) {
    console.warn('加载本地收藏失败', error)
  }
}

const syncUserAndFavorites = async () => {
  const key = ensureUserKey()
  loadCachedFavorites()
  try {
    await ensureAnonymousUser(userKey.value)
    const result = await getUserFavorites(userKey.value)
    const remoteFavorites = (result.data || result.newslist || []) as string[]
    if (Array.isArray(remoteFavorites)) {
      favoriteToolIds.value = remoteFavorites.filter(item => typeof item === 'string')
      saveFavoriteTools()
    }
  } catch (error) {
    console.warn('同步收藏失败，使用本地收藏', key, error)
  }
}

const isFavorite = (toolId: string) => favoriteToolIds.value.includes(toolId)

const toggleFavorite = async (tool: ToolItem) => {
  if (!tool.implemented) return
  const key = ensureUserKey()
  const nextFavorited = !isFavorite(tool.id)
  favoriteToolIds.value = nextFavorited
    ? [tool.id, ...favoriteToolIds.value.filter(id => id !== tool.id)].slice(0, 10)
    : favoriteToolIds.value.filter(id => id !== tool.id)
  saveFavoriteTools()
  try {
    if (nextFavorited) {
      await addUserFavorite(userKey.value, tool.id)
    } else {
      await removeUserFavorite(userKey.value, tool.id)
    }
  } catch (error) {
    console.warn('同步收藏操作失败', key, error)
  }
}

const saveRecentTool = (toolId: string) => {
  const next = [toolId, ...recentToolIds.value.filter(id => id !== toolId)].slice(0, 10)
  recentToolIds.value = next
  try {
    uni.setStorageSync(RECENT_TOOLS_KEY, next)
  } catch (error) {
    console.warn('保存最近使用失败', error)
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

const openPath = (path: string, tab = false) => {
  if (!path) return
  if (tab) {
    uni.switchTab({ url: path })
    return
  }
  uni.navigateTo({ url: path })
}

const goToOverview = (item: OverviewItem) => {
  if (item.id === 'tools') {
    activeCategory.value = 'all'
    return
  }
  openPath(item.path, item.tab)
}

const goToTool = (tool: ToolItem) => {
  if (!tool.implemented) {
    uni.showToast({ title: `${tool.name}${tool.status || '开发中'}`, icon: 'none' })
    return
  }

  saveRecentTool(tool.id)
  openPath(tool.path)
  void trackToolClick(tool.id)
}

const navigateToBeian = () => {
  // #ifdef H5
  const opened = window.open('https://beian.miit.gov.cn/', '_blank', 'noopener,noreferrer')
  if (opened) opened.opener = null
  // #endif
}

onMounted(() => {
  loadRecentTools()
  void syncUserAndFavorites()
  loadPopularTools()
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  background: linear-gradient(180deg, #eef5ff 0%, #f7f9fc 42%, #ffffff 100%);
  padding: 24rpx;
  box-sizing: border-box;
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
  background: var(--theme-surface, rgba(255, 255, 255, 0.9)) !important;
  border: 2rpx solid var(--theme-border, rgba(255, 255, 255, 0.74));
  box-shadow: 0 18rpx 50rpx rgba(20, 35, 90, 0.08);
}

.hero-content,
.tool-search-wrap,
.overview-panel,
.quick-panel,
.main-panel {
  position: relative;
  z-index: 1;
}

.tool-search-wrap {
  display: none;
}

.hero-content {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.hero-kicker {
  width: fit-content;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: var(--theme-primary-soft, #eef5ff);
  color: var(--theme-primary, #1677ff);
  font-size: 24rpx;
  font-weight: 800;
}

.hero-title {
  font-size: 44rpx;
  line-height: 1.22;
  color: var(--theme-text, #17233d);
  font-weight: 900;
}

.hero-subtitle {
  max-width: 760px;
  font-size: 26rpx;
  color: var(--theme-text-secondary, #667085);
  line-height: 1.65;
}

.search-box {
  display: flex;
  align-items: center;
  background: var(--theme-primary-soft, rgba(246, 248, 251, 0.92));
  border-radius: 999rpx;
  padding: 18rpx 24rpx;
  border: 2rpx solid var(--theme-border, rgba(226, 232, 240, 0.9));
}

.tool-search {
  gap: 12rpx;
  background: linear-gradient(135deg, var(--theme-primary-soft, #eef5ff) 0%, var(--theme-surface, #ffffff) 100%);
  border-color: var(--theme-border, rgba(226, 232, 240, 0.9));
  box-shadow: inset 0 0 0 2rpx rgba(255, 255, 255, 0.58), 0 10rpx 24rpx rgba(20, 35, 90, 0.05);
}

.search-input {
  flex: 1;
  min-width: 0;
  font-size: 28rpx;
  color: var(--theme-text, #243044);
}

.clear-search {
  font-size: 24rpx;
  color: var(--theme-primary, #1677ff);
  font-weight: 700;
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

.search-submit::after,
.empty-btn::after {
  border: 0;
}

.overview-panel {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
}

.overview-card {
  display: flex;
  align-items: center;
  gap: 12rpx;
  min-width: 0;
  padding: 18rpx 16rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, rgba(255,255,255,0.96), rgba(248,251,255,0.9));
  border: 2rpx solid var(--theme-border, rgba(226, 232, 240, 0.86));
  box-shadow: 0 8rpx 22rpx rgba(20, 35, 90, 0.045);
}

.overview-icon {
  width: 62rpx;
  height: 62rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
  font-size: 32rpx;
}

.overview-info {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.overview-label {
  color: var(--theme-text-secondary, #667085);
  font-size: 20rpx;
  font-weight: 700;
}

.overview-value {
  color: var(--theme-text, #17233d);
  font-size: 24rpx;
  font-weight: 900;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.overview-desc {
  color: var(--theme-text-muted, #8a96a8);
  font-size: 20rpx;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.quick-panel {
  background: rgba(255, 255, 255, 0.92);
  border-radius: 30rpx;
  padding: 24rpx;
  border: 2rpx solid rgba(238, 242, 247, 0.9);
  box-shadow: 0 12rpx 34rpx rgba(20, 35, 90, 0.06);
}

.quick-panel-title,
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  margin-bottom: 18rpx;
}

.quick-panel-title {
  justify-content: flex-start;
  gap: 8rpx;
}

.quick-panel-title-text,
.section-title {
  font-size: 32rpx;
  line-height: 1.2;
  color: var(--theme-text, #243044);
  font-weight: 900;
}

.quick-panel-title-icon {
  font-size: 32rpx;
  line-height: 1;
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
  font-weight: 800;
}

.section-count {
  flex-shrink: 0;
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: var(--theme-primary-soft, #eef5ff);
  color: var(--theme-primary, #1677ff);
  font-size: 22rpx;
  font-weight: 800;
}

.quick-tool-scroll {
  width: 100%;
  white-space: nowrap;
}

.quick-tool-list {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  gap: 10rpx;
}

.quick-tool-card {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 0 0 112rpx;
  min-width: 0;
  min-height: 88rpx;
  gap: 7rpx;
  padding: 10rpx 6rpx;
  border-radius: 18rpx;
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
  box-shadow: inset 0 0 0 2rpx rgba(255, 255, 255, 0.42), 0 6rpx 14rpx rgba(20, 35, 90, 0.07);
}

.quick-icon-text {
  font-size: 22rpx;
}

.quick-tool-info {
  width: 100%;
  min-width: 0;
}

.quick-tool-name {
  display: block;
  font-size: 20rpx;
  line-height: 1.2;
  color: var(--theme-text, #243044);
  font-weight: 800;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.favorite-toggle {
  position: absolute;
  top: 6rpx;
  right: 6rpx;
  z-index: 2;
  width: 34rpx;
  height: 34rpx;
  line-height: 32rpx;
  margin: 0;
  padding: 0;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.86);
  color: #cbd5e1;
  font-size: 22rpx;
  font-weight: 900;
  box-shadow: 0 4rpx 12rpx rgba(15, 23, 42, 0.08);
}

.favorite-toggle::after {
  border: 0;
}

.favorite-toggle.active {
  color: #f59e0b;
}

.tool-favorite-toggle {
  top: 16rpx;
  right: 16rpx;
  width: 46rpx;
  height: 46rpx;
  line-height: 44rpx;
  font-size: 30rpx;
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
  font-weight: 900;
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
.empty-title { font-size: 30rpx; color: var(--theme-text, #243044); font-weight: 900; }
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
.overview-card:active,
.quick-tool-card:active,
.tool-item:active,
.category-item:active { opacity: 0.72; }

.theme-night .tool-search,
.theme-night .quick-panel,
.theme-night .overview-card,
.theme-night .tool-item {
  background: rgba(30, 41, 59, 0.86);
  border-color: rgba(148, 163, 184, 0.3);
  box-shadow: 0 10rpx 28rpx rgba(0, 0, 0, 0.2);
}

.theme-night .overview-label,
.theme-night .overview-desc,
.theme-night .tool-desc,
.theme-night .hero-subtitle {
  color: #d5deec;
}

@media (min-width: 768px) {
  .container { padding: 32px 24px; }

  .hero-section {
    gap: 24px;
    padding: 36px;
    border-radius: 28px;
  }

  .hero-title { font-size: 34px; }
  .hero-subtitle { font-size: 16px; }
  .search-box { padding: 14px 20px; }
  .search-input { font-size: 16px; }
  .search-submit {
    height: 34px;
    line-height: 34px;
    padding: 0 18px;
    font-size: 14px;
  }

  .overview-panel { gap: 16px; }
  .overview-card {
    padding: 18px;
    border-radius: 18px;
    cursor: pointer;
  }
  .overview-icon { width: 44px; height: 44px; border-radius: 14px; font-size: 22px; }
  .overview-label, .overview-desc { font-size: 13px; }
  .overview-value { font-size: 17px; }

  .quick-panel {
    padding: 28px;
    border-radius: 24px;
  }

  .quick-tool-list { gap: 8px; }
  .quick-tool-card {
    flex-basis: 92px;
    min-height: 60px;
    padding: 8px 6px;
    border-radius: 12px;
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
    cursor: pointer;
  }
  .quick-tool-icon { width: 26px; height: 26px; border-radius: 9px; }
  .quick-icon-text { font-size: 14px; }
  .quick-tool-name { font-size: 12px; }

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

  .tool-icon { width: 44px; height: 44px; border-radius: 14px; margin-bottom: 12px; }
  .icon-text { font-size: 22px; }
  .tool-name { font-size: 16px; }
  .tool-desc { font-size: 13px; }

  .overview-card:hover,
  .quick-tool-card:hover,
  .tool-item:hover {
    transform: translateY(-2px);
    border-color: rgba(22, 119, 255, 0.24);
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
  }
}

@media (max-width: 420px) {
  .overview-panel {
    grid-template-columns: 1fr;
  }
}
</style>
