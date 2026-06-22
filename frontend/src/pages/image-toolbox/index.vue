<template>
  <view :class="['container', themeClass]">
    <view class="page-shell">
      <view class="hero-card">
        <text class="title">🖼️ 图片工具箱</text>
        <text class="subtitle">图片压缩、格式转换、尺寸调整、加水印和图片 Base64，一页完成常见图片处理</text>
      </view>

      <view class="card">
        <view class="section-title-row">
          <text class="section-title">选择功能</text>
          <text class="section-badge">本地处理</text>
        </view>
        <view class="operation-grid">
          <view class="operation-item" :class="{ active: operation === item.value }" v-for="item in operations" :key="item.value" @click="selectOperation(item.value)">
            <text class="operation-icon">{{ item.icon }}</text>
            <text class="operation-label">{{ item.label }}</text>
            <text class="operation-desc">{{ item.desc }}</text>
          </view>
        </view>
      </view>

      <view class="card">
        <view class="section-title-row">
          <text class="section-title">上传图片</text>
          <text class="section-badge">JPG/PNG/WEBP</text>
        </view>
        <button class="select-btn" @click="chooseImageFile" :disabled="loading">选择图片</button>
        <view class="file-preview" v-if="selectedFile">
          <text class="file-name">{{ selectedFile.name }}</text>
          <text class="file-size">{{ formatSize(selectedFile.size) }}</text>
        </view>
      </view>

      <view class="card" v-if="operation === 'convert'">
        <view class="section-title-row"><text class="section-title">目标格式</text><text class="section-badge">{{ targetFormat.toUpperCase() }}</text></view>
        <view class="format-grid">
          <view class="format-item" :class="{ active: targetFormat === item.value }" v-for="item in formats" :key="item.value" @click="targetFormat = item.value">
            <text class="format-label">{{ item.label }}</text>
            <text class="format-desc">{{ item.desc }}</text>
          </view>
        </view>
      </view>

      <view class="card" v-if="operation === 'compress' || operation === 'convert'">
        <view class="section-title-row"><text class="section-title">图片质量</text><text class="section-badge">{{ quality }}%</text></view>
        <slider :value="quality" min="35" max="95" show-value @change="onQualityChange" />
      </view>

      <view class="card" v-if="operation === 'resize'">
        <view class="section-title-row"><text class="section-title">尺寸调整</text><text class="section-badge">等比可留空</text></view>
        <view class="form-grid">
          <view class="form-item"><text class="form-label">宽度 px</text><input class="text-input" type="number" v-model="resizeWidth" placeholder="如 1080" /></view>
          <view class="form-item"><text class="form-label">高度 px</text><input class="text-input" type="number" v-model="resizeHeight" placeholder="可留空" /></view>
        </view>
      </view>

      <view class="card" v-if="operation === 'watermark'">
        <view class="section-title-row"><text class="section-title">水印文字</text><text class="section-badge">右下角</text></view>
        <input class="text-input" v-model="watermarkText" maxlength="40" placeholder="请输入水印文字" />
      </view>

      <button class="primary-btn" @click="submitImageTask" :disabled="!selectedFile || loading">{{ loading ? '处理中...' : '开始处理图片' }}</button>

      <view class="card result-card" v-if="resultFile || base64Text">
        <view class="section-title-row"><text class="section-title">处理结果</text><text class="section-badge success">完成</text></view>
        <view v-if="base64Text" class="text-box">
          <textarea class="result-text" :value="base64Text" disabled />
          <button class="ghost-btn" @click="copyBase64">复制 Base64</button>
        </view>
        <view v-if="resultFile" class="result-file">
          <text class="file-name">{{ resultFile.filename }}</text>
          <text class="file-size">{{ resultFile.media_type }}</text>
          <button class="download-btn" @click="downloadResult">下载图片</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { processImageBase64, type ImageToolboxResult } from '@/api'
import { useTheme } from '@/utils/theme'

declare const wx: any
const { themeClass } = useTheme()
type Operation = 'compress' | 'convert' | 'resize' | 'watermark' | 'base64'
interface PickedFile { name: string; size: number; path?: string; content?: ArrayBuffer | Blob | string }

const operations: Array<{ value: Operation; label: string; icon: string; desc: string }> = [
  { value: 'compress', label: '图片压缩', icon: '📦', desc: '减小 JPG/WEBP 体积' },
  { value: 'convert', label: '格式转换', icon: '🔁', desc: 'PNG/JPG/WEBP 互转' },
  { value: 'resize', label: '尺寸调整', icon: '📐', desc: '按宽高缩放图片' },
  { value: 'watermark', label: '图片加水印', icon: '💧', desc: '右下角文字水印' },
  { value: 'base64', label: '图片转 Base64', icon: '🔤', desc: '生成 data URL 文本' }
]
const formats = [
  { value: 'jpg', label: 'JPG', desc: '照片通用' },
  { value: 'png', label: 'PNG', desc: '透明/无损' },
  { value: 'webp', label: 'WEBP', desc: '体积更小' }
]

const operation = ref<Operation>('compress')
const selectedFile = ref<PickedFile | null>(null)
const quality = ref(75)
const targetFormat = ref('jpg')
const resizeWidth = ref('1080')
const resizeHeight = ref('')
const watermarkText = ref('小巧的工具箱')
const loading = ref(false)
const resultFile = ref<ImageToolboxResult | null>(null)
const base64Text = ref('')
const canSubmit = computed(() => Boolean(selectedFile.value))

const selectOperation = (value: Operation) => { operation.value = value; resultFile.value = null; base64Text.value = '' }
const onQualityChange = (event: any) => { quality.value = Number(event.detail?.value || quality.value) }
const formatSize = (size: number) => size >= 1024 * 1024 ? `${(size / 1024 / 1024).toFixed(2)} MB` : `${Math.max(1, Math.round(size / 1024))} KB`
const arrayBufferToBase64 = (buffer: ArrayBuffer) => { let binary = ''; const bytes = new Uint8Array(buffer); for (let i = 0; i < bytes.length; i += 0x8000) binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000)); return btoa(binary) }
const base64ToArrayBuffer = (base64: string) => { const binary = atob(base64); const bytes = new Uint8Array(binary.length); for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i); return bytes.buffer }

const setPickedFile = (file: PickedFile) => {
  const ext = (file.name.split('.').pop() || '').toLowerCase()
  if (!['jpg', 'jpeg', 'png', 'webp'].includes(ext)) return uni.showToast({ title: '请选择 JPG、PNG、WEBP 图片', icon: 'none' })
  if (file.size > 10 * 1024 * 1024) return uni.showToast({ title: '图片不能超过 10MB', icon: 'none' })
  selectedFile.value = file
  resultFile.value = null
  base64Text.value = ''
}

const chooseImageFile = () => {
  // #ifdef MP-WEIXIN
  uni.chooseImage({ count: 1, sourceType: ['album', 'camera'], sizeType: ['original', 'compressed'], success: (res: any) => {
    const file = res.tempFiles?.[0]; const path = file?.path || res.tempFilePaths?.[0]; if (path) setPickedFile({ name: path.split('/').pop() || 'image.jpg', size: file?.size || 0, path, content: path })
  }})
  // #endif
  // #ifdef H5
  uni.chooseFile({ count: 1, type: 'image', extension: ['.jpg', '.jpeg', '.png', '.webp'], success: (res: any) => {
    const file = res.tempFiles?.[0]; if (!file) return; setPickedFile({ name: file.name || 'image.jpg', size: file.size || 0, path: file.path || file.tempFilePath, content: file.file || file.raw || file.path || file.tempFilePath })
  }})
  // #endif
}

const readFileBase64 = async (file: PickedFile) => {
  // #ifdef MP-WEIXIN
  return new Promise<string>((resolve, reject) => uni.getFileSystemManager().readFile({ filePath: file.path || '', encoding: 'base64', success: (res: any) => resolve(res.data), fail: reject }))
  // #endif
  // #ifdef H5
  const raw = file.content as any
  if (raw instanceof ArrayBuffer) return arrayBufferToBase64(raw)
  if (raw && typeof raw.arrayBuffer === 'function') return arrayBufferToBase64(await raw.arrayBuffer())
  if (typeof raw === 'string') { const response = await fetch(raw); return arrayBufferToBase64(await response.arrayBuffer()) }
  throw new Error('读取图片失败')
  // #endif
}

const submitImageTask = async () => {
  if (!canSubmit.value || !selectedFile.value) return
  loading.value = true; resultFile.value = null; base64Text.value = ''
  try {
    const res = await processImageBase64({
      filename: selectedFile.value.name,
      content_base64: await readFileBase64(selectedFile.value),
      operation: operation.value,
      options: { quality: quality.value, target_format: targetFormat.value, width: resizeWidth.value, height: resizeHeight.value, watermark: watermarkText.value }
    })
    if (res.code === 200 && res.data) {
      if (operation.value === 'base64') base64Text.value = String(res.data.text || '')
      else resultFile.value = res.data
      uni.showToast({ title: '处理完成', icon: 'success' })
    } else uni.showToast({ title: res.msg || '处理失败', icon: 'none' })
  } catch (error: any) { uni.showToast({ title: error?.message || '处理失败', icon: 'none' }) }
  finally { loading.value = false }
}

const copyBase64 = () => uni.setClipboardData({ data: base64Text.value })
const downloadResult = () => {
  if (!resultFile.value?.base64 || !resultFile.value.filename) return
  // #ifdef H5
  const blob = new Blob([base64ToArrayBuffer(resultFile.value.base64)], { type: resultFile.value.media_type })
  const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = resultFile.value.filename; document.body.appendChild(link); link.click(); setTimeout(() => { URL.revokeObjectURL(url); document.body.removeChild(link) }, 1000)
  // #endif
  // #ifdef MP-WEIXIN
  const filePath = `${wx.env.USER_DATA_PATH}/${Date.now()}_${String(resultFile.value.filename).replace(/[\\/:*?"<>|]/g, '_')}`
  uni.getFileSystemManager().writeFile({ filePath, data: resultFile.value.base64, encoding: 'base64', success: () => uni.openDocument({ filePath, showMenu: true, fail: () => uni.showToast({ title: '已保存', icon: 'success' }) }), fail: () => uni.showToast({ title: '保存失败', icon: 'none' }) })
  // #endif
}
</script>

<style scoped>
.container { min-height: 100vh; background: var(--theme-bg, #f5f7fb); }
.page-shell { padding: 28rpx; }
.hero-card, .card { border-radius: 28rpx; background: var(--theme-card, #fff); box-shadow: 0 12rpx 34rpx rgba(15,23,42,.08); }
.hero-card { padding: 36rpx; background: linear-gradient(135deg, #0ea5e9, #22c55e); color: #fff; }
.title { display:block; font-size:42rpx; font-weight:900; margin-bottom:12rpx; }
.subtitle { display:block; font-size:26rpx; line-height:1.6; opacity:.92; }
.card { margin-top:24rpx; padding:28rpx; }
.section-title-row { display:flex; justify-content:space-between; align-items:center; margin-bottom:20rpx; }
.section-title { font-size:30rpx; font-weight:800; color:var(--theme-text,#111827); }
.section-badge { padding:8rpx 16rpx; border-radius:999rpx; background:#e0f2fe; color:#0284c7; font-size:22rpx; }
.section-badge.success { background:#dcfce7; color:#16a34a; }
.operation-grid,.format-grid,.form-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:18rpx; }
.operation-item,.format-item { padding:22rpx; border:2rpx solid var(--theme-border,#e5e7eb); border-radius:22rpx; background:var(--theme-muted,#f8fafc); }
.operation-item.active,.format-item.active { border-color:#0ea5e9; background:#f0f9ff; }
.operation-icon { display:block; font-size:34rpx; margin-bottom:8rpx; }
.operation-label,.format-label { display:block; font-size:27rpx; font-weight:800; color:var(--theme-text,#111827); }
.operation-desc,.format-desc,.file-size { display:block; margin-top:8rpx; color:var(--theme-text-secondary,#64748b); font-size:22rpx; line-height:1.4; }
.select-btn,.primary-btn,.download-btn { width:100%; border:none; border-radius:22rpx; background:linear-gradient(135deg,#0ea5e9,#22c55e); color:#fff; font-weight:800; }
.primary-btn { margin-top:26rpx; height:92rpx; line-height:92rpx; font-size:28rpx; }
.ghost-btn { margin-top:14rpx; border-radius:20rpx; background:#f1f5f9; color:#475569; font-size:25rpx; }
.file-preview,.result-file { padding:18rpx; border-radius:20rpx; background:var(--theme-muted,#f8fafc); }
.file-name { color:var(--theme-text,#111827); font-size:25rpx; word-break:break-all; }
.form-label { display:block; margin-bottom:10rpx; font-size:24rpx; color:var(--theme-text-secondary,#64748b); }
.text-input { box-sizing:border-box; width:100%; height:82rpx; padding:0 22rpx; border:2rpx solid var(--theme-border,#e5e7eb); border-radius:18rpx; background:var(--theme-muted,#f8fafc); color:var(--theme-text,#111827); }
.result-text { width:100%; min-height:260rpx; box-sizing:border-box; padding:18rpx; border-radius:18rpx; background:#fff; color:#111827; font-size:24rpx; }
</style>
