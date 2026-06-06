<template>
  <view class="container">
    <view class="page-shell">
      <!-- 顶部介绍：同一网址兼容 PC 和移动端 -->
      <view class="hero-section">
        <view class="hero-content">
          <text class="hero-title">小巧的工具箱</text>
          <text class="hero-subtitle">天气查询、今日油价、二维码生成、随机密码生成等常用工具，一个页面快速使用。</text>
        </view>
        <view class="hero-card">
          <text class="hero-card-title">已上线工具</text>
          <text class="hero-card-number">4+</text>
          <text class="hero-card-desc">持续扩展生活服务、编码转换和效率工具</text>
        </view>
      </view>

      <view class="main-panel">
        <!-- 顶部搜索 -->
        <view class="search-box">
          <uni-icons type="search" size="18" color="#999"></uni-icons>
          <input
            class="search-input"
            placeholder="搜索天气、油价、二维码、密码..."
            v-model="searchText"
            @input="onSearch"
          />
        </view>

        <!-- 分类标签 -->
        <scroll-view class="category-scroll" scroll-x="true" show-scrollbar="false">
          <view class="category-list">
            <view
              class="category-item"
              :class="{ active: activeCategory === 'all' }"
              @click="activeCategory = 'all'"
            >
              全部
            </view>
            <view
              class="category-item"
              :class="{ active: activeCategory === cat.id }"
              @click="activeCategory = cat.id"
              v-for="cat in categories"
              :key="cat.id"
            >
              {{ cat.name }}
            </view>
          </view>
        </scroll-view>

        <!-- 工具列表 -->
        <view class="tool-grid">
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
            <text class="coming-soon-badge" v-if="!tool.implemented">开发中</text>
          </view>
        </view>
      </view>


      <!-- 底部信息 -->
      <view class="footer">
        <text class="footer-text">小巧的工具箱 v1.0</text>
        <!-- #ifdef H5 -->
        <view
          class="icp-beian"
          @click="navigateToBeian"
        >
          <text>粤ICP备2026056747号</text>
        </view>
        <!-- #endif -->
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const searchText = ref('')
const activeCategory = ref('all')

const categories = ref([
  { id: 'life', name: '生活服务' },
  { id: 'code', name: '编码转换' },
  { id: 'other', name: '其他工具' }
])

const tools = ref([
  { id: 'oil-price', name: '油价查询', desc: '今日油价', icon: '⛽', color: '#ff6b6b', category: 'life', path: '/pages/oil-price/index', implemented: true },
  { id: 'weather', name: '天气预报', desc: '实时天气', icon: '🌤️', color: '#4ecdc4', category: 'life', path: '/pages/weather/index', implemented: true },
  { id: 'calendar', name: '黄历日历', desc: '敬请期待', icon: '📅', color: '#dfe6e9', category: 'life', path: '/pages/calendar/index', implemented: false },
  { id: 'qrcode', name: '二维码生成', desc: '一键生成', icon: '📱', color: '#a29bfe', category: 'other', path: '/pages/qrcode/index', implemented: true },
  { id: 'password', name: '密码生成', desc: '随机密码', icon: '🔐', color: '#fdcb6e', category: 'other', path: '/pages/password/index', implemented: true },
  { id: 'base64', name: 'Base64', desc: '敬请期待', icon: '🔤', color: '#74b9ff', category: 'code', path: '/pages/base64/index', implemented: false },
  { id: 'url', name: 'URL编码', desc: '敬请期待', icon: '🔗', color: '#00b894', category: 'code', path: '/pages/url/index', implemented: false },
  { id: 'json', name: 'JSON格式化', desc: '敬请期待', icon: '📋', color: '#e17055', category: 'code', path: '/pages/json/index', implemented: false }
])

const filteredTools = computed(() => {
  let list = tools.value

  if (activeCategory.value !== 'all') {
    list = list.filter(t => t.category === activeCategory.value)
  }

  if (searchText.value) {
    const keyword = searchText.value.toLowerCase()
    list = list.filter(t =>
      t.name.toLowerCase().includes(keyword) ||
      t.desc.toLowerCase().includes(keyword)
    )
  }

  return list
})

const onSearch = () => {
  // 搜索逻辑已在 computed 中处理
}

const goToTool = (tool: any) => {
  if (!tool.implemented) {
    uni.showToast({ title: '功能开发中，敬请期待', icon: 'none' })
    return
  }
  uni.navigateTo({
    url: tool.path
  })
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

.page-shell {
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
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

.icon-text {
  font-size: 48rpx;
}

.tool-name {
  font-size: 29rpx;
  font-weight: 700;
  color: #243044;
  margin-bottom: 8rpx;
}

.tool-desc {
  font-size: 23rpx;
  color: #7a869a;
}

.tool-not-implemented {
  opacity: 0.58;
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
.tool-item:active {
  opacity: 0.72;
}

@media (min-width: 768px) {
  .container {
    padding: 32px 24px;
  }

  .hero-section {
    flex-direction: row;
    align-items: stretch;
    justify-content: space-between;
    padding: 48px;
    border-radius: 28px;
  }

  .hero-content {
    flex: 1;
  }

  .hero-title {
    font-size: 48px;
  }

  .hero-subtitle {
    font-size: 18px;
  }

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
  }

  .tool-item:hover {
    transform: translateY(-4px);
    box-shadow: 0 14px 32px rgba(20, 35, 90, 0.12);
  }

}
</style>
