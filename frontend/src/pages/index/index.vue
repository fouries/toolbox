<template>
  <view class="container">
    <!-- 顶部搜索 -->
    <view class="search-box">
      <uni-icons type="search" size="18" color="#999"></uni-icons>
      <input 
        class="search-input" 
        placeholder="搜索工具..." 
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
        @click="goToTool(tool)"
        v-for="tool in filteredTools"
        :key="tool.id"
      >
        <view class="tool-icon" :style="{ background: tool.color }">
          <text class="icon-text">{{ tool.icon }}</text>
        </view>
        <text class="tool-name">{{ tool.name }}</text>
        <text class="tool-desc">{{ tool.desc }}</text>
      </view>
    </view>

    <!-- 底部信息 -->
    <view class="footer">
      <text class="footer-text">万能工具箱 v1.0</text>
      <!-- #ifdef H5 -->
      <view 
        class="icp-beian" 
        @click="navigateToBeian"
      >
        <text>粤ICP备2026056747号</text>
      </view>
      <!-- #endif -->
      <!-- #ifdef MP-WEIXIN -->
      <text class="icp-beian">粤ICP备2026056747号</text>
      <!-- #endif -->
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const searchText = ref('')
const activeCategory = ref('all')

const categories = ref([
  { id: 'life', name: '生活服务' },
  { id: 'query', name: '查询工具' },
  { id: 'code', name: '编码转换' },
  { id: 'other', name: '其他工具' }
])

const tools = ref([
  { id: 'oil-price', name: '油价查询', desc: '今日油价', icon: '⛽', color: '#ff6b6b', category: 'life', path: '/pages/oil-price/index' },
  { id: 'weather', name: '天气预报', desc: '实时天气', icon: '🌤️', color: '#4ecdc4', category: 'life', path: '/pages/weather/index' },
  { id: 'express', name: '快递查询', desc: '物流跟踪', icon: '📦', color: '#45b7d1', category: 'query', path: '/pages/express/index' },
  { id: 'phone', name: '手机号查询', desc: '归属地查询', icon: '📱', color: '#96ceb4', category: 'query', path: '/pages/phone/index' },
  { id: 'idcard', name: '身份证查询', desc: '信息验证', icon: '🪪', color: '#ffeaa7', category: 'query', path: '/pages/idcard/index' },
  { id: 'calendar', name: '黄历日历', desc: '今日宜忌', icon: '📅', color: '#dfe6e9', category: 'life', path: '/pages/calendar/index' },
  { id: 'qrcode', name: '二维码生成', desc: '一键生成', icon: '📱', color: '#a29bfe', category: 'other', path: '/pages/qrcode/index' },
  { id: 'ip', name: 'IP查询', desc: '地址查询', icon: '🌐', color: '#81ecec', category: 'query', path: '/pages/ip/index' },
  { id: 'password', name: '密码生成', desc: '随机密码', icon: '🔐', color: '#fdcb6e', category: 'other', path: '/pages/password/index' },
  { id: 'base64', name: 'Base64', desc: '编解码', icon: '🔤', color: '#74b9ff', category: 'code', path: '/pages/base64/index' },
  { id: 'url', name: 'URL编码', desc: '编解码', icon: '🔗', color: '#00b894', category: 'code', path: '/pages/url/index' },
  { id: 'json', name: 'JSON格式化', desc: '格式化', icon: '📋', color: '#e17055', category: 'code', path: '/pages/json/index' }
])

const filteredTools = computed(() => {
  let list = tools.value
  
  // 分类过滤
  if (activeCategory.value !== 'all') {
    list = list.filter(t => t.category === activeCategory.value)
  }
  
  // 搜索过滤
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
  // 搜索逻辑已在computed中处理
}

const goToTool = (tool: any) => {
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
  background: #f5f5f5;
  padding: 20rpx;
}

.search-box {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 50rpx;
  padding: 20rpx 30rpx;
  margin-bottom: 20rpx;
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
  background: #fff;
  border-radius: 30rpx;
  font-size: 26rpx;
  color: #666;
  white-space: nowrap;
}

.category-item.active {
  background: #007aff;
  color: #fff;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20rpx;
}

.tool-item {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx 20rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
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
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
  margin-bottom: 8rpx;
}

.tool-desc {
  font-size: 22rpx;
  color: #999;
}

.footer {
  margin-top: 60rpx;
  text-align: center;
  padding-bottom: 40rpx;
}

.footer-text {
  font-size: 24rpx;
  color: #ccc;
}

.icp-beian {
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #999;
  cursor: pointer;
}

.icp-beian:active {
  opacity: 0.7;
}
</style>
