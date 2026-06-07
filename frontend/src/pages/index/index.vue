<template>
  <view :class="['container', themeClass]">
    <ThemeSwitcher />
    <view class="page-shell home-shell">
      <view class="hero-section">
        <view class="hero-bg-dot dot-one"></view>
        <view class="hero-bg-dot dot-two"></view>

        <view class="hero-content">
          <view class="hero-copy">
            <text class="hero-kicker">在线实用工具集合</text>
            <text class="hero-title">小巧的工具箱</text>
            <text class="hero-subtitle">精选日常高频工具，轻量、快速、即开即用。天气、油价、二维码、密码等常用能力，一个入口快速找到。</text>
          </view>

          <view class="search-box hero-search">
            <uni-icons type="search" size="18" color="#8a96a8"></uni-icons>
            <input
              class="search-input"
              placeholder="搜索天气、油价、二维码、密码..."
              confirm-type="search"
              v-model="searchText"
            />
            <text class="clear-search" v-if="searchText" @click="clearSearch">清空</text>
          </view>

          <view class="hero-meta-row">
            <view class="hero-meta-card">
              <view class="meta-icon meta-icon-free">
                <text class="meta-icon-text">🎁</text>
              </view>
              <view class="meta-copy">
                <text class="meta-number">免费使用</text>
                <text class="meta-label">无需安装 · 即开即用</text>
              </view>
            </view>
            <view class="hero-meta-card">
              <view class="meta-icon meta-icon-tools">
                <text class="meta-icon-text">🧰</text>
              </view>
              <view class="meta-copy">
                <text class="meta-number">常用工具</text>
                <text class="meta-label">简洁无广告</text>
              </view>
            </view>
            <view class="hero-meta-card">
              <view class="meta-icon meta-icon-cross">
                <text class="meta-icon-text">📱</text>
              </view>
              <view class="meta-copy">
                <text class="meta-number">跨端</text>
                <text class="meta-label">手机电脑都可用</text>
              </view>
            </view>
          </view>
        </view>

        <view class="quick-panel">
          <view class="quick-panel-header">
            <view>
              <text class="section-kicker">快捷入口</text>
              <text class="section-title">热门工具</text>
            </view>
            <text class="section-count">{{ popularTools.length }} 个常用</text>
          </view>

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
                <text class="quick-tool-desc">{{ tool.desc }}</text>
              </view>
              <text class="quick-arrow">›</text>
            </view>
          </view>
        </view>
      </view>

      <view class="main-panel">
        <view class="panel-header">
          <view>
            <text class="section-kicker">全部工具</text>
            <text class="section-title">按分类浏览</text>
          </view>
          <text class="section-count">{{ filteredTools.length }} 个结果</text>
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
            <text class="badge hot" v-if="tool.badge">{{ tool.badge }}</text>
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
          <text class="empty-desc">试试搜索：天气、油价、二维码、密码</text>
          <button class="empty-btn" @click="clearSearch">清空搜索</button>
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
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'
import { useTheme } from '@/utils/theme'
import { ref, computed } from 'vue'

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
  badge?: string
  status?: string
}

const searchText = ref('')
const activeCategory = ref('all')

const categories = ref<CategoryItem[]>([
  { id: 'life', name: '生活服务' },
  { id: 'code', name: '编码转换' },
  { id: 'other', name: '其他工具' }
])

const tools = ref<ToolItem[]>([
  { id: 'oil-price', name: '油价查询', desc: '全国各省今日汽柴油价格', icon: '⛽', color: '#ff6b6b', category: 'life', path: '/pages/oil-price/index', implemented: true, badge: '常用' },
  { id: 'weather', name: '天气预报', desc: '查询城市实时天气和7天预报', icon: '🌤️', color: '#4ecdc4', category: 'life', path: '/pages/weather/index', implemented: true, badge: '热门' },
  { id: 'calendar', name: '黄历日历', desc: '农历节气与宜忌查询', icon: '📅', color: '#dfe6e9', category: 'life', path: '/pages/calendar/index', implemented: false, status: '即将上线' },
  { id: 'qrcode', name: '二维码生成', desc: '文本/网址一键生成二维码', icon: '📱', color: '#a29bfe', category: 'other', path: '/pages/qrcode/index', implemented: true, badge: '常用' },
  { id: 'password', name: '密码生成', desc: '自定义长度和字符类型', icon: '🔐', color: '#fdcb6e', category: 'other', path: '/pages/password/index', implemented: true, badge: '安全' },
  { id: 'base64', name: 'Base64', desc: '文本编码解码工具', icon: '🔤', color: '#74b9ff', category: 'code', path: '/pages/base64/index', implemented: false, status: '规划中' },
  { id: 'url', name: 'URL编码', desc: '网址参数编码解码', icon: '🔗', color: '#00b894', category: 'code', path: '/pages/url/index', implemented: false, status: '规划中' },
  { id: 'json', name: 'JSON格式化', desc: '格式化与压缩 JSON', icon: '📋', color: '#e17055', category: 'code', path: '/pages/json/index', implemented: false, status: '规划中' }
])

const popularTools = computed(() => tools.value.filter(t => t.implemented && t.badge).slice(0, 4))

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

const goToTool = (tool: ToolItem) => {
  if (!tool.implemented) {
    uni.showToast({ title: `${tool.name}${tool.status || '开发中'}`, icon: 'none' })
    return
  }
  uni.navigateTo({ url: tool.path })
}

const navigateToBeian = () => {
  // #ifdef H5
  window.open('https://beian.miit.gov.cn/', '_blank')
  // #endif
}
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

.hero-bg-dot {
  position: absolute;
  border-radius: 999rpx;
  opacity: 0.18;
  pointer-events: none;
}

.dot-one {
  width: 260rpx;
  height: 260rpx;
  top: -96rpx;
  right: -66rpx;
  background: var(--theme-primary, #1677ff);
}

.dot-two {
  width: 180rpx;
  height: 180rpx;
  left: -70rpx;
  bottom: 80rpx;
  background: var(--theme-accent, #31c48d);
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

.hero-kicker {
  display: inline-flex;
  width: fit-content;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: var(--theme-primary-soft, #eef5ff);
  font-size: 24rpx;
  color: var(--theme-primary, #1677ff);
  font-weight: 700;
}

.hero-title {
  margin-top: 18rpx;
  font-size: 52rpx;
  font-weight: 800;
  line-height: 1.12;
  color: var(--theme-text, #243044);
}

.hero-subtitle {
  margin-top: 16rpx;
  max-width: 720px;
  font-size: 28rpx;
  color: var(--theme-text-secondary, #667085);
  line-height: 1.7;
}

.search-box {
  display: flex;
  align-items: center;
  background: rgba(246, 248, 251, 0.92);
  border-radius: 999rpx;
  padding: 20rpx 28rpx;
  border: 2rpx solid rgba(226, 232, 240, 0.9);
}

.hero-search {
  box-shadow: inset 0 0 0 2rpx rgba(255, 255, 255, 0.55);
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
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
}

.hero-meta-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  min-width: 0;
  padding: 18rpx 16rpx;
  text-align: center;
  border-radius: 22rpx;
  background: rgba(248, 250, 252, 0.78);
  border: 2rpx solid rgba(226, 232, 240, 0.68);
}

.meta-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: inset 0 0 0 2rpx rgba(255, 255, 255, 0.58), 0 10rpx 22rpx rgba(20, 35, 90, 0.08);
}

.meta-icon-free {
  background: linear-gradient(135deg, #fff1b8 0%, #ffd666 100%);
}

.meta-icon-tools {
  background: linear-gradient(135deg, #dbeafe 0%, #93c5fd 100%);
}

.meta-icon-cross {
  background: linear-gradient(135deg, #dcfce7 0%, #86efac 100%);
}

.meta-icon-text {
  font-size: 32rpx;
  line-height: 1;
}

.meta-copy {
  flex: 1;
  min-width: 0;
}

.meta-number,
.meta-label {
  display: block;
}

.meta-number {
  font-size: 30rpx;
  font-weight: 800;
  color: var(--theme-text, #243044);
}

.meta-label {
  margin-top: 4rpx;
  font-size: 21rpx;
  color: var(--theme-text-muted, #9aa6b8);
}

.quick-panel,
.main-panel {
  background: rgba(255, 255, 255, 0.92);
  border-radius: 30rpx;
  padding: 24rpx;
  border: 2rpx solid rgba(238, 242, 247, 0.9);
  box-shadow: 0 12rpx 34rpx rgba(20, 35, 90, 0.06);
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

.quick-tool-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.quick-tool-card {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 18rpx;
  border-radius: 22rpx;
  background: rgba(248, 250, 252, 0.78);
  border: 2rpx solid rgba(238, 242, 247, 0.9);
}

.quick-tool-icon {
  width: 76rpx;
  height: 76rpx;
  border-radius: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.quick-icon-text {
  font-size: 36rpx;
}

.quick-tool-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.quick-tool-name {
  font-size: 28rpx;
  color: var(--theme-text, #243044);
  font-weight: 800;
}

.quick-tool-desc {
  margin-top: 4rpx;
  font-size: 22rpx;
  color: var(--theme-text-secondary, #667085);
  line-height: 1.35;
}

.quick-arrow {
  color: var(--theme-text-muted, #9aa6b8);
  font-size: 42rpx;
  line-height: 1;
}

.main-panel {
  margin-bottom: 24rpx;
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
  gap: 20rpx;
}

.tool-item {
  position: relative;
  min-height: 220rpx;
  background: rgba(255, 255, 255, 0.94);
  border-radius: 24rpx;
  padding: 30rpx 20rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  border: 2rpx solid rgba(238, 242, 247, 0.95);
  box-shadow: 0 10rpx 26rpx rgba(20, 35, 90, 0.05);
}

.tool-icon {
  width: 100rpx;
  height: 100rpx;
  border-radius: 30rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 15rpx;
}

.icon-text { font-size: 48rpx; }

.tool-name {
  font-size: 29rpx;
  font-weight: 800;
  color: var(--theme-text, #243044);
  margin-bottom: 8rpx;
}

.tool-desc {
  font-size: 23rpx;
  color: var(--theme-text-secondary, #7a869a);
  line-height: 1.45;
}

.tool-not-implemented { opacity: 0.58; }

.badge.hot {
  position: absolute;
  top: 15rpx;
  left: 15rpx;
  font-size: 18rpx;
  padding: 4rpx 12rpx;
  background: var(--theme-primary-soft, #e8f3ff);
  color: var(--theme-primary, #1677ff);
  border-radius: 20rpx;
  font-weight: 700;
}

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

  .hero-title { font-size: 48px; }
  .hero-subtitle { font-size: 18px; }
  .search-box { padding: 14px 20px; }
  .search-input { font-size: 16px; }
  .hero-meta-row { gap: 12px; }
  .hero-meta-card {
    flex-direction: row;
    align-items: center;
    gap: 12px;
    padding: 16px;
    text-align: left;
    border-radius: 18px;
  }
  .meta-icon { width: 46px; height: 46px; border-radius: 15px; }
  .meta-icon-text { font-size: 24px; }
  .meta-number { font-size: 22px; }
  .meta-label { font-size: 13px; }

  .quick-panel,
  .main-panel {
    padding: 28px;
    border-radius: 24px;
  }

  .quick-tool-card {
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
    cursor: pointer;
  }

  .quick-tool-card:hover {
    transform: translateY(-2px);
    border-color: rgba(22, 119, 255, 0.24);
    box-shadow: 0 12px 28px rgba(20, 35, 90, 0.08);
  }

  .tool-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 18px;
  }

  .tool-item {
    min-height: 168px;
    transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
    cursor: pointer;
  }

  .tool-item:hover {
    transform: translateY(-2px);
    border-color: rgba(22, 119, 255, 0.24);
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
  }
}
</style>
