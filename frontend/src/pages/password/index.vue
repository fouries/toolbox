<template>
  <view :class="['container', themeClass]">
    <ThemeSwitcher />
    <view class="page-shell">
      <view class="page-header">
        <text class="title">🔐 密码生成器</text>
        <text class="subtitle">安全随机密码，可选择长度和字符类型</text>
      </view>

      <view class="password-box card" @tap="copyPassword">
        <text class="password-text">{{ password || '点击下方按钮生成' }}</text>
        <view class="copy-hint">点击密码复制</view>
      </view>

      <view class="setting-card card">
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

      <view class="setting-card card">
        <view class="setting-title">字符类型</view>

        <view class="option-row">
          <view class="option-left">
            <text class="option-label">大写字母</text>
            <text class="option-desc">A-Z</text>
          </view>
          <switch :checked="options.upper" color="#007aff" @change="toggleOption('upper', $event)" />
        </view>

        <view class="option-row">
          <view class="option-left">
            <text class="option-label">小写字母</text>
            <text class="option-desc">a-z</text>
          </view>
          <switch :checked="options.lower" color="#007aff" @change="toggleOption('lower', $event)" />
        </view>

        <view class="option-row">
          <view class="option-left">
            <text class="option-label">数字</text>
            <text class="option-desc">0-9</text>
          </view>
          <switch :checked="options.number" color="#007aff" @change="toggleOption('number', $event)" />
        </view>

        <view class="option-row">
          <view class="option-left">
            <text class="option-label">特殊符号</text>
            <text class="option-desc">!@#$%^&*()</text>
          </view>
          <switch :checked="options.symbol" color="#007aff" @change="toggleOption('symbol', $event)" />
        </view>

        <view class="option-row" style="border-bottom: none;">
          <view class="option-left">
            <text class="option-label">排除易混淆字符</text>
            <text class="option-desc">如 1/l/I/0/O</text>
          </view>
          <switch :checked="options.excludeAmbiguous" color="#007aff" @change="toggleOption('excludeAmbiguous', $event)" />
        </view>
      </view>

      <view class="strength-card card" v-if="password">
        <view class="strength-title">密码强度</view>
        <view class="strength-bar">
          <view class="strength-fill" :class="strengthLevel"></view>
        </view>
        <text class="strength-text">{{ strengthText }}</text>
      </view>

      <view class="action-buttons">
        <button class="generate-btn" @tap="generatePassword" :disabled="loading">
          {{ loading ? '生成中...' : '生成密码' }}
        </button>
        <button class="copy-btn" v-if="password" @tap="copyPassword">
          <uni-icons type="download" size="16" color="#007aff"></uni-icons>
          复制密码
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'
import { useTheme } from '@/utils/theme'
import { ref, computed } from 'vue'
import { generatePassword as apiGeneratePassword } from '@/api'

declare const wx: any

const { themeClass } = useTheme()

interface PasswordOptions {
  upper: boolean
  lower: boolean
  number: boolean
  symbol: boolean
  excludeAmbiguous: boolean
}

const password = ref('')
const loading = ref(false)
const passwordLength = ref(16)

const options = ref<PasswordOptions>({
  upper: true,
  lower: true,
  number: true,
  symbol: true,
  excludeAmbiguous: false
})

const UPPER = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
const LOWER = 'abcdefghijklmnopqrstuvwxyz'
const NUMBER = '0123456789'
const SYMBOL = '!@#$%^&*()_+-=[]{}|;:,.<>?'
const AMBIGUOUS = '0O1lI'

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
  const idx = strengthLevel.value === 'weak' ? 1
    : strengthLevel.value === 'medium' ? 2
    : strengthLevel.value === 'strong' ? 3 : 4
  return levels[idx]
})

const onLengthChange = (e: any) => {
  passwordLength.value = e.detail.value
}

const toggleOption = (key: string, e?: any) => {
  // Use event value if provided (from switch @change)
  const value = e?.detail?.value !== undefined ? e.detail.value : !(options.value as any)[key]
  ;(options.value as PasswordOptions)[key as keyof PasswordOptions] = value
}

async function getSecureRandomValues(length: number): Promise<Uint32Array> {
  // #ifdef H5
  return crypto.getRandomValues(new Uint32Array(length))
  // #endif

  // #ifdef MP-WEIXIN
  return new Promise((resolve) => {
    wx.getRandomValues({
      length: length * 4,
      success: (res: any) => {
        const buffer = res.randomValues || res
        const bytes = new Uint8Array(buffer)
        const arr = new Uint32Array(length)
        for (let i = 0; i < length; i++) {
          arr[i] =
            ((bytes[i * 4] || 0) << 24) |
            ((bytes[i * 4 + 1] || 0) << 16) |
            ((bytes[i * 4 + 2] || 0) << 8) |
            (bytes[i * 4 + 3] || 0)
        }
        resolve(arr)
      },
      fail: () => {
        resolve(new Uint32Array())
      }
    })
  })
  // #endif

  throw new Error('当前环境不支持安全随机数生成')
}

function buildCharPool(): string {
  let chars = ''
  if (options.value.upper) chars += UPPER
  if (options.value.lower) chars += LOWER
  if (options.value.number) chars += NUMBER
  if (options.value.symbol) chars += SYMBOL
  if (options.value.excludeAmbiguous) {
    for (const ch of AMBIGUOUS) {
      chars = chars.replace(ch, '')
    }
  }
  return chars
}

function pickFromPool(pool: string, random: number): string {
  return pool[random % pool.length]
}

function secureShuffle(arr: string[], randoms: Uint32Array, offset: number): string[] {
  const a = arr.slice()
  for (let i = a.length - 1; i > 0; i--) {
    const j = randoms[offset++] % (i + 1)
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

async function generateLocally(): Promise<string> {
  const chars = buildCharPool()
  if (!chars) return ''

  const requiredPools: string[] = []
  if (options.value.upper) requiredPools.push(options.value.excludeAmbiguous ? UPPER.replace(/[0O]/g, '') : UPPER)
  if (options.value.lower) requiredPools.push(options.value.excludeAmbiguous ? LOWER.replace(/[1lI]/g, '') : LOWER)
  if (options.value.number) requiredPools.push(options.value.excludeAmbiguous ? NUMBER.replace(/[0]/g, '') : NUMBER)
  if (options.value.symbol) requiredPools.push(SYMBOL)

  const length = passwordLength.value
  const remaining = Math.max(length - requiredPools.length, 0)
  const randoms = await getSecureRandomValues(requiredPools.length + remaining + length)
  if (randoms.length < requiredPools.length + remaining + length) {
    throw new Error('当前环境不支持安全随机数生成')
  }

  let cursor = 0
  const result: string[] = []
  for (const pool of requiredPools) {
    result.push(pickFromPool(pool, randoms[cursor++]))
  }

  for (let i = 0; i < remaining; i++) {
    result.push(pickFromPool(chars, randoms[cursor++]))
  }

  return secureShuffle(result, randoms, cursor).join('')
}

const generatePassword = async () => {
  if (!options.value.upper && !options.value.lower && !options.value.number && !options.value.symbol) {
    uni.showToast({ title: '请至少选择一种字符类型', icon: 'none' })
    return
  }

  loading.value = true

  try {
    if (options.value.excludeAmbiguous) {
      password.value = await generateLocally()
      uni.showToast({ title: '生成成功', icon: 'success' })
      return
    }

    const res: any = await apiGeneratePassword({
      length: passwordLength.value,
      upper: options.value.upper,
      lower: options.value.lower,
      number: options.value.number,
      symbol: options.value.symbol,
      excludeAmbiguous: options.value.excludeAmbiguous
    })

    if (res.code === 200) {
      password.value = res.data.password
      uni.showToast({ title: '生成成功', icon: 'success' })
    } else {
      throw new Error(res.msg)
    }
  } catch {
    // API 失败时本地生成（兜底方案）
    try {
      password.value = await generateLocally()
      uni.showToast({ title: '生成本地密码', icon: 'success' })
    } catch {
      uni.showToast({ title: '当前环境不支持安全随机数', icon: 'none' })
    }
  } finally {
    loading.value = false
  }
}

const copyPassword = () => {
  if (!password.value) return

  uni.setClipboardData({
    data: password.value,
    success: () => {
      uni.showToast({ title: '已复制到剪贴板', icon: 'success' })
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

.password-box {
  text-align: center;
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

.strength-fill.weak { width: 25%; background: #ff5252; }
.strength-fill.medium { width: 50%; background: #ffb74d; }
.strength-fill.strong { width: 75%; background: #66bb6a; }
.strength-fill.very-strong { width: 100%; background: #4caf50; }

.strength-text {
  font-size: 24rpx;
  color: #666;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  margin-top: 20rpx;
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

.copy-btn {
  width: 100%;
  background: #fff;
  color: #007aff;
  border-radius: 50rpx;
  padding: 20rpx;
  font-size: 28rpx;
  border: 2rpx solid #007aff;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
}
</style>