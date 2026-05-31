<template>
  <view class="container">
    <view class="header">
      <text class="title">🔐 密码生成器</text>
      <text class="subtitle">安全随机密码，一键生成</text>
    </view>

    <!-- 密码显示区域 -->
    <view class="password-box">
      <text class="password-text" @tap="copyPassword">{{ password || '点击下方按钮生成' }}</text>
      <view class="copy-hint">点击密码复制</view>
    </view>

    <!-- 长度设置 -->
    <view class="setting-card">
      <view class="setting-row">
        <text class="setting-label">密码长度</text>
        <text class="setting-value">{{ passwordLength }} 位</text>
      </view>
      <slider 
        :value="passwordLength" 
        :min="4" 
        :max="64" 
        :step="1"
        @change="onLengthChange"
        activeColor="#007aff"
        backgroundColor="#e0e0e0"
      />
    </view>

    <!-- 字符选项 -->
    <view class="setting-card">
      <view class="setting-title">字符类型</view>
      
      <view class="option-row" @tap="toggleOption('upper')">
        <view class="option-left">
          <text class="option-label">大写字母</text>
          <text class="option-desc">A-Z</text>
        </view>
        <switch :checked="options.upper" color="#007aff" />
      </view>

      <view class="option-row" @tap="toggleOption('lower')">
        <view class="option-left">
          <text class="option-label">小写字母</text>
          <text class="option-desc">a-z</text>
        </view>
        <switch :checked="options.lower" color="#007aff" />
      </view>

      <view class="option-row" @tap="toggleOption('number')">
        <view class="option-left">
          <text class="option-label">数字</text>
          <text class="option-desc">0-9</text>
        </view>
        <switch :checked="options.number" color="#007aff" />
      </view>

      <view class="option-row" @tap="toggleOption('symbol')">
        <view class="option-left">
          <text class="option-label">特殊符号</text>
          <text class="option-desc">!@#$%^&*()</text>
        </view>
        <switch :checked="options.symbol" color="#007aff" />
      </view>
    </view>

    <!-- 密码强度 -->
    <view class="strength-card" v-if="password">
      <view class="strength-title">密码强度</view>
      <view class="strength-bar">
        <view class="strength-fill" :class="strengthLevel"></view>
      </view>
      <text class="strength-text">{{ strengthText }}</text>
    </view>

    <!-- 生成按钮 -->
    <button class="generate-btn" @tap="generatePassword" :loading="loading">
      {{ loading ? '生成中...' : '生成密码' }}
    </button>
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { generatePassword as apiGeneratePassword } from '@/api'

const password = ref('')
const loading = ref(false)
const passwordLength = ref(16)

const options = ref({
  upper: true,
  lower: true,
  number: true,
  symbol: true
})

const strengthLevel = computed(() => {
  let score = 0
  if (password.value.length >= 8) score++
  if (password.value.length >= 12) score++
  if (password.value.length >= 16) score++
  if (/[A-Z]/.test(password.value)) score++
  if (/[a-z]/.test(password.value)) score++
  if (/[0-9]/.test(password.value)) score++
  if (/[^A-Za-z0-9]/.test(password.value)) score++
  
  if (score <= 2) return 'weak'
  if (score <= 4) return 'medium'
  if (score <= 5) return 'strong'
  return 'very-strong'
})

const strengthText = computed(() => {
  const levels = ['非常弱', '弱', '中等', '强', '非常强']
  const idx = strengthLevel.value === 'weak' ? 1 : 
              strengthLevel.value === 'medium' ? 2 :
              strengthLevel.value === 'strong' ? 3 : 4
  return levels[idx]
})

const onLengthChange = (e: any) => {
  passwordLength.value = e.detail.value
}

const toggleOption = (key: string) => {
  (options.value as any)[key] = !(options.value as any)[key]
}

const generatePassword = async () => {
  // 检查至少选择一种字符类型
  if (!options.value.upper && !options.value.lower && 
      !options.value.number && !options.value.symbol) {
    uni.showToast({
      title: '请至少选择一种字符类型',
      icon: 'none'
    })
    return
  }

  loading.value = true
  
  try {
    // 调用后端 API 生成密码
    const res: any = await apiGeneratePassword({
      length: passwordLength.value,
      upper: options.value.upper,
      lower: options.value.lower,
      number: options.value.number,
      symbol: options.value.symbol
    })
    
    if (res.code === 200) {
      password.value = res.data.password
      uni.showToast({
        title: '生成成功',
        icon: 'success'
      })
    } else {
      throw new Error(res.msg)
    }
  } catch (e) {
    // API 失败时，前端本地生成（兜底方案）
    let chars = ''
    if (options.value.upper) chars += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    if (options.value.lower) chars += 'abcdefghijklmnopqrstuvwxyz'
    if (options.value.number) chars += '0123456789'
    if (options.value.symbol) chars += '!@#$%^&*()_+-=[]{}|;:,.<>?'
    
    let result = ''
    const array = new Uint32Array(passwordLength.value)
    crypto.getRandomValues(array)
    for (let i = 0; i < passwordLength.value; i++) {
      result += chars[array[i] % chars.length]
    }
    password.value = result
    
    uni.showToast({
      title: '生成本地密码',
      icon: 'success'
    })
  } finally {
    loading.value = false
  }
}

const copyPassword = () => {
  if (!password.value) return
  
  uni.setClipboardData({
    data: password.value,
    success: () => {
      uni.showToast({
        title: '已复制到剪贴板',
        icon: 'success'
      })
    }
  })
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background: linear-gradient(180deg, #e3f2fd 0%, #f5f5f5 100%);
  padding: 30rpx;
}

.header {
  text-align: center;
  margin-bottom: 40rpx;
}

.title {
  display: block;
  font-size: 40rpx;
  font-weight: bold;
  color: #333;
  margin-bottom: 10rpx;
}

.subtitle {
  font-size: 24rpx;
  color: #999;
}

.password-box {
  background: #fff;
  border-radius: 20rpx;
  padding: 40rpx 30rpx;
  margin-bottom: 30rpx;
  text-align: center;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
}

.password-text {
  display: block;
  font-size: 36rpx;
  font-weight: 500;
  color: #007aff;
  word-break: break-all;
  margin-bottom: 15rpx;
  letter-spacing: 2rpx;
}

.copy-hint {
  font-size: 22rpx;
  color: #999;
}

.setting-card {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
}

.setting-title {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
  margin-bottom: 20rpx;
}

.setting-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.setting-label {
  font-size: 28rpx;
  color: #333;
}

.setting-value {
  font-size: 28rpx;
  color: #007aff;
  font-weight: 500;
}

.option-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f5f5f5;
}

.option-row:last-child {
  border-bottom: none;
}

.option-left {
  display: flex;
  flex-direction: column;
}

.option-label {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 5rpx;
}

.option-desc {
  font-size: 22rpx;
  color: #999;
}

.strength-card {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
}

.strength-title {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
  margin-bottom: 20rpx;
}

.strength-bar {
  height: 12rpx;
  background: #e0e0e0;
  border-radius: 6rpx;
  overflow: hidden;
  margin-bottom: 15rpx;
}

.strength-fill {
  height: 100%;
  transition: all 0.3s;
  border-radius: 6rpx;
}

.strength-fill.weak {
  width: 25%;
  background: #ff5252;
}

.strength-fill.medium {
  width: 50%;
  background: #ffb74d;
}

.strength-fill.strong {
  width: 75%;
  background: #66bb6a;
}

.strength-fill.very-strong {
  width: 100%;
  background: #4caf50;
}

.strength-text {
  font-size: 24rpx;
  color: #666;
}

.generate-btn {
  width: 100%;
  background: #007aff;
  color: #fff;
  border-radius: 50rpx;
  padding: 25rpx;
  font-size: 32rpx;
  font-weight: 500;
}

.generate-btn[disabled] {
  background: #ccc;
}
</style>
