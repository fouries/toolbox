<template>
  <view class="container">
    <view class="page-shell home-shell">
      <view class="hero-section">
        <view class="hero-content">
          <text class="hero-kicker">在线实用工具集合</text>
          <text class="hero-title">小巧的工具箱</text>
          <text class="hero-subtitle">天气查询、今日油价、二维码生成、随机密码生成等常用工具，一个页面快速使用，电脑和手机都能舒适访问。</text>
        </view>
        <view class="hero-card">
          <text class="hero-card-title">已上线工具</text>
          <text class="hero-card-number">4+</text>
          <text class="hero-card-desc">持续扩展生活服务、编码转换和效率工具</text>
        </view>
      </view>

      <view class="main-panel">
        <view class="search-box">
          <uni-icons type="search" size="18" color="#999"></uni-icons>
          <input
            class="search-input"
            placeholder="搜索天气、油价、二维码、密码..."
            confirm-type="search"
            v-model="searchText"
          />
          <text class="clear-search" v-if="searchText" @click="clearSearch">清空</text>
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
import { ref, computed } from 'vue'

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
  display: flex;
  flex-direction: column;
  gap: 24rpx;
  padding: 42rpx 32rpx;
  margin-bottom: 24rpx;
  border-radius: 32rpx;
  color: #fff;
  background: linear-gradient(135deg, #1677ff 0%, #31c48d 100%);
  box-shadow: 0 24rpx 60rpx rgba(22, 119, 255, 0.2);
}

.hero-content {
  display: flex;
  flex-direction: column;
}

.hero-kicker {
  display: inline-flex;
  width: fit-content;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.9);
}

.hero-title {
  margin-top: 18rpx;
  font-size: 52rpx;
  font-weight: 800;
  line-height: 1.15;
}

.hero-subtitle {
  margin-top: 16rpx;
  max-width: 760px;
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.7;
}

.hero-card {
  padding: 28rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.16);
  border: 2rpx solid rgba(255, 255, 255, 0.22);
}

.hero-card-title,
.hero-card-desc {
  display: block;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.84);
}

.hero-card-number {
  display: block;
  margin: 8rpx 0;
  font-size: 64rpx;
  font-weight: 800;
}

.main-panel {
  background: rgba(255, 255, 255, 0.92);
  border-radius: 30rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 16rpx 44rpx rgba(20, 35, 90, 0.08);
}

.search-box {
  display: flex;
  align-items: center;
  background: #f6f8fb;
  border-radius: 999rpx;
  padding: 20rpx 30rpx;
  margin-bottom: 20rpx;
  border: 2rpx solid #edf1f7;
}

.search-input {
  flex: 1;
  margin-left: 15rpx;
  font-size: 28rpx;
}

.clear-search {
  margin-left: 16rpx;
  font-size: 24rpx;
  color: #1677ff;
}

.category-scroll {
  white-space: nowrap;
  margin-bottom: 30rpx;
}

.category-list {
  display: flex;
  padding: 10rpx 0;
}

.category-item {
  padding: 15rpx 30rpx;
  margin-right: 20rpx;
  background: #f6f8fb;
  border-radius: 999rpx;
  font-size: 26rpx;
  color: #556;
  white-space: nowrap;
}

.category-item.active {
  background: #007aff;
  color: #fff;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20rpx;
}

.tool-item {
  position: relative;
  min-height: 220rpx;
  background: #fff;
  border-radius: 24rpx;
  padding: 30rpx 20rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  border: 2rpx solid #eef2f7;
  box-shadow: 0 10rpx 26rpx rgba(20, 35, 90, 0.06);
}

.tool-icon {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 15rpx;
}

.icon-text { font-size: 48rpx; }

.tool-name {
  font-size: 29rpx;
  font-weight: 700;
  color: #243044;
  margin-bottom: 8rpx;
}

.tool-desc {
  font-size: 23rpx;
  color: #7a869a;
  line-height: 1.45;
}

.tool-not-implemented { opacity: 0.58; }

.badge.hot {
  position: absolute;
  top: 15rpx;
  left: 15rpx;
  font-size: 18rpx;
  padding: 4rpx 12rpx;
  background: #e8f3ff;
  color: #1677ff;
  border-radius: 20rpx;
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
  background: #f8fbff;
  border-radius: 24rpx;
  border: 2rpx dashed #dce8f8;
}

.empty-icon,
.empty-title,
.empty-desc {
  display: block;
}

.empty-icon { font-size: 76rpx; margin-bottom: 16rpx; }
.empty-title { font-size: 30rpx; color: #243044; font-weight: 700; }
.empty-desc { margin: 12rpx 0 24rpx; font-size: 24rpx; color: #7a869a; }

.empty-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 220rpx;
  height: 70rpx;
  line-height: 70rpx;
  border-radius: 999rpx;
  background: #1677ff;
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
  color: #9aa6b8;
}

.icp-beian {
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #8b97a8;
  cursor: pointer;
}

.icp-beian:active,
.tool-item:active { opacity: 0.72; }

@media (min-width: 768px) {
  .container { padding: 32px 24px; }

  .hero-section {
    flex-direction: row;
    align-items: stretch;
    justify-content: space-between;
    padding: 48px;
    border-radius: 28px;
  }

  .hero-content { flex: 1; }
  .hero-title { font-size: 48px; }
  .hero-subtitle { font-size: 18px; }

  .hero-card {
    width: 260px;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .main-panel {
    padding: 28px;
    border-radius: 24px;
  }

  .tool-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 18px;
  }

  .tool-item {
    min-height: 168px;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
    cursor: pointer;
  }

  .tool-item:hover {
    transform: translateY(-4px);
    box-shadow: 0 14px 32px rgba(20, 35, 90, 0.12);
  }
}
</style>
