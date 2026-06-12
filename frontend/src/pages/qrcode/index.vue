<template>
  <view :class="['container', themeClass]">
    <view class="page-shell">
      <view class="page-header">
        <text class="title">📱 二维码生成</text>
        <text class="subtitle">输入文字或网址，一键生成二维码</text>
      </view>

      <view class="input-box card">
        <textarea
          class="input"
          placeholder="请输入要生成二维码的文字或网址..."
          v-model="inputText"
          maxlength="500"
          auto-height
        ></textarea>
        <view class="input-footer">
          <text class="char-count">{{ inputText.length }}/500</text>
          <button class="clear-btn" size="mini" @click="inputText = ''" v-if="inputText">清空</button>
        </view>
      </view>

      <view class="size-box card">
        <text class="size-label">二维码尺寸</text>
        <slider
          class="size-slider"
          :min="128"
          :max="512"
          :step="64"
          :value="qrSize"
          @change="onSizeChange"
          activeColor="#007aff"
        />
        <text class="size-value">{{ qrSize }}px</text>
      </view>

      <button class="generate-btn" @click="generateQrcode" :disabled="!inputText.trim() || loading">
        {{ loading ? '生成中...' : '生成二维码' }}
      </button>

      <view class="result-box card" v-if="qrCode">
        <view class="qrcode-wrapper">
          <image class="qrcode-img" :src="qrCode" mode="widthFix" :style="{ width: previewSize + 'rpx', height: previewSize + 'rpx' }"></image>
        </view>
        <view class="action-buttons">
          <button class="action-btn" size="mini" @click="saveImage">
            <uni-icons type="download" size="16" color="#fff"></uni-icons>
            保存图片
          </button>
          <button class="action-btn secondary" size="mini" @click="copyText">
            <uni-icons type="redo" size="16" color="#007aff"></uni-icons>
            复制内容
          </button>
        </view>
      </view>

      <view class="quick-tags card">
        <text class="tags-title">⚡ 快捷输入</text>
        <view class="tags-list">
          <view class="tag" @click="inputText = 'https://'">网址</view>
          <view class="tag" @click="inputText = '13800138000'">手机号</view>
          <view class="tag" @click="inputText = 'example@mail.com'">邮箱</view>
          <view class="tag" @click="inputText = '你好世界'">问候语</view>
          <view class="tag" @click="inputText = 'WiFi:T:WPA;S:MyWiFi;P:password;;'">WiFi模板</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useTheme } from '@/utils/theme'
import { ref, computed } from 'vue'
import { generateQrcode as apiGenerateQrcode } from '@/api'

const { themeClass } = useTheme()

declare const wx: any

const inputText = ref('')
const qrSize = ref(256)
const loading = ref(false)
const qrCode = ref('')

const previewSize = computed(() => {
  return Math.min(400, Math.max(250, qrSize.value * 0.8))
})

const onSizeChange = (e: any) => {
  qrSize.value = e.detail.value
}

const generateQrcode = async () => {
  if (!inputText.value.trim()) {
    uni.showToast({ title: '请输入内容', icon: 'none' })
    return
  }

  loading.value = true

  try {
    const res: any = await apiGenerateQrcode(inputText.value, qrSize.value)
    if (res.code === 200) {
      qrCode.value = res.data.base64
      uni.showToast({ title: '生成成功', icon: 'success' })
    } else {
      uni.showToast({ title: res.msg || '生成失败', icon: 'none' })
    }
  } catch (e) {
    uni.showToast({ title: '生成失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const saveImage = () => {
  if (!qrCode.value) return

  // #ifdef MP-WEIXIN
  const base64Data = qrCode.value.replace(/^data:image\/\w+;base64,/, '')
  const fs = uni.getFileSystemManager()
  const filePath = `${wx.env.USER_DATA_PATH}/qrcode_${Date.now()}.png`

  fs.writeFile({
    filePath,
    data: base64Data,
    encoding: 'base64',
    success: () => {
      uni.saveImageToPhotosAlbum({
        filePath,
        success: () => {
          uni.showToast({ title: '保存成功', icon: 'success' })
        },
        fail: (err: any) => {
          uni.showToast({ title: err.errMsg || '保存失败', icon: 'none' })
        }
      })
    },
    fail: (err: any) => {
      uni.showToast({ title: '写入文件失败', icon: 'none' })
    }
  })
  // #endif

  // #ifdef H5
  const link = document.createElement('a')
  link.href = qrCode.value
  link.download = `qrcode_${Date.now()}.png`
  link.click()
  uni.showToast({ title: '已开始下载', icon: 'success' })
  // #endif
}

const copyText = () => {
  uni.setClipboardData({
    data: inputText.value || qrCode.value,
    success: () => {
      uni.showToast({ title: '已复制', icon: 'success' })
    }
  })
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background: linear-gradient(180deg, #e8f5e9 0%, #f5f5f5 100%);
  padding: 30rpx;
}

.input {
  width: 100%;
  min-height: 150rpx;
  font-size: 28rpx;
  color: #333;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15rpx;
  padding-top: 15rpx;
  border-top: 1rpx solid #eee;
}

.char-count {
  font-size: 24rpx;
  color: #999;
}

.clear-btn {
  font-size: 24rpx;
  color: #999;
  background: #f5f5f5;
  border: none;
}

.size-box {
  display: flex;
  align-items: center;
}

.size-label {
  font-size: 28rpx;
  color: #333;
  min-width: 140rpx;
}

.size-slider {
  flex: 1;
  margin: 0 20rpx;
}

.size-value {
  font-size: 26rpx;
  color: #007aff;
  font-weight: 500;
  min-width: 80rpx;
  text-align: right;
}

.generate-btn {
  width: 100%;
  background: #007aff;
  color: #fff;
  border-radius: 50rpx;
  font-size: 32rpx;
  padding: 25rpx;
  margin-bottom: 40rpx;
}

.generate-btn[disabled] {
  background: #ccc;
}

.result-box {
  text-align: center;
}

.qrcode-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 30rpx;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 30rpx;
}

.action-btn {
  background: #007aff;
  color: #fff;
  border: none;
  border-radius: 40rpx;
  padding: 15rpx 40rpx;
  font-size: 26rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.action-btn.secondary {
  background: #fff;
  color: #007aff;
  border: 2rpx solid #007aff;
}

.tags-title {
  display: block;
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
  margin-bottom: 20rpx;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 15rpx;
}

.tag {
  padding: 15rpx 25rpx;
  background: #f0f7ff;
  color: #007aff;
  border-radius: 30rpx;
  font-size: 24rpx;
}
</style>