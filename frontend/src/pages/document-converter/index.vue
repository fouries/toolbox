<template>
  <view :class="['container', themeClass]">
    <view class="page-shell document-shell">
      <view class="page-header hero-card">
        <text class="title">📄 文档转换</text>
        <text class="subtitle">支持 TXT、HTML、Word、PDF 常见文档互转，也支持图片转 PDF / Word，转换后直接下载，不长期保存</text>
      </view>

      <view class="card upload-card">
        <view class="section-title-row">
          <text class="section-title">选择文件</text>
          <text class="section-badge">最大 5MB</text>
        </view>
        <button class="select-btn" @click="chooseDocumentFile" :disabled="loading">
          {{ selectedFile ? '重新选择文件' : '选择文档文件' }}
        </button>
        <view class="file-preview" v-if="selectedFile">
          <text class="file-icon">{{ sourceIcon }}</text>
          <view class="file-info">
            <text class="file-name">{{ selectedFile.name }}</text>
            <text class="file-meta">{{ sourceFormatLabel }} · {{ fileSizeLabel }}</text>
          </view>
        </view>
        <view class="tips-box">
          <text class="tips-title">支持格式</text>
          <text class="tips-text">源文件：TXT、HTML、DOCX、PDF、JPG、PNG、WEBP</text>
          <text class="tips-text">目标格式：TXT、HTML、DOCX、PDF；图片支持转 PDF / Word</text>
          <text class="tips-text">说明：PDF 转换提取可选中文本，扫描件图片 PDF 暂不做 OCR。</text>
        </view>
      </view>

      <view class="card format-card">
        <view class="section-title-row">
          <text class="section-title">转换为</text>
          <text class="section-badge">{{ targetFormat.toUpperCase() }}</text>
        </view>
        <view class="format-grid">
          <view
            v-for="item in targetFormats"
            :key="item.value"
            class="format-item"
            :class="{ active: targetFormat === item.value, disabled: isTargetDisabled(item.value) }"
            @click="selectTargetFormat(item.value)"
          >
            <text class="format-icon">{{ item.icon }}</text>
            <text class="format-name">{{ item.label }}</text>
            <text class="format-desc">{{ item.desc }}</text>
          </view>
        </view>
      </view>

      <button class="convert-btn" @click="convertDocument" :disabled="!canConvert || loading">
        {{ loading ? '转换中...' : '开始转换' }}
      </button>

      <view class="card result-card" v-if="convertedFile">
        <view class="result-header">
          <text class="result-icon">✅</text>
          <view class="result-info">
            <text class="result-title">转换完成</text>
            <text class="result-desc">{{ convertedFile.filename }}</text>
          </view>
        </view>
        <button class="download-btn" @click="downloadConvertedFile">下载/打开文件</button>
      </view>

      <view class="card scene-card">
        <text class="scene-title">常用场景</text>
        <view class="scene-list">
          <view class="scene-item">TXT → PDF：把文字内容快速排版成 PDF</view>
          <view class="scene-item">DOCX → TXT：提取 Word 文档纯文本</view>
          <view class="scene-item">HTML → DOCX：网页片段转成可编辑文档</view>
          <view class="scene-item">PDF → TXT：提取可复制 PDF 中的文字</view>
          <view class="scene-item">图片 → PDF：把照片、截图整理成单页 PDF</view>
          <view class="scene-item">图片 → Word：把图片插入可继续编辑的 Word 文档</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { convertDocumentBase64, type DocumentConvertResult } from '@/api'
import { useTheme } from '@/utils/theme'

const { themeClass } = useTheme()

declare const wx: any

interface PickedFile {
  name: string
  size: number
  path?: string
  content?: ArrayBuffer | Blob | string
}

const MAX_FILE_SIZE = 5 * 1024 * 1024
const selectedFile = ref<PickedFile | null>(null)
const targetFormat = ref('pdf')
const loading = ref(false)
const convertedFile = ref<DocumentConvertResult | null>(null)

const targetFormats = [
  { value: 'pdf', label: 'PDF', icon: '📕', desc: '适合分享打印' },
  { value: 'docx', label: 'Word', icon: '📝', desc: '可继续编辑' },
  { value: 'txt', label: 'TXT', icon: '📄', desc: '纯文本提取' },
  { value: 'html', label: 'HTML', icon: '🌐', desc: '网页格式' }
]

const imageExts = ['jpg', 'jpeg', 'png', 'webp']
const documentExts = ['txt', 'html', 'docx', 'pdf']

const sourceExt = computed(() => {
  const name = selectedFile.value?.name || ''
  const ext = name.split('.').pop()?.toLowerCase() || ''
  return ext === 'htm' ? 'html' : ext
})

const isImageSource = computed(() => imageExts.includes(sourceExt.value))
const sourceFormatLabel = computed(() => sourceExt.value ? sourceExt.value.toUpperCase() : '未知格式')
const sourceIcon = computed(() => isImageSource.value ? '🖼️' : targetFormats.find(item => item.value === sourceExt.value)?.icon || '📎')
const fileSizeLabel = computed(() => {
  const size = selectedFile.value?.size || 0
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(2)} MB`
  return `${Math.max(1, Math.round(size / 1024))} KB`
})

const isTargetDisabled = (format: string) => {
  if (!sourceExt.value) return false
  if (isImageSource.value) return !['pdf', 'docx'].includes(format)
  return sourceExt.value === format
}

const canConvert = computed(() => Boolean(selectedFile.value && sourceExt.value && !isTargetDisabled(targetFormat.value)))

const arrayBufferToBase64 = (buffer: ArrayBuffer) => {
  let binary = ''
  const bytes = new Uint8Array(buffer)
  const chunkSize = 0x8000
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize))
  }
  return btoa(binary)
}

const base64ToArrayBuffer = (base64: string) => {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  return bytes.buffer
}

const isSupportedSource = (ext: string) => [...documentExts, ...imageExts].includes(ext)

const setPickedFile = (file: PickedFile) => {
  const ext = (file.name.split('.').pop() || '').toLowerCase().replace('htm', 'html')
  if (!isSupportedSource(ext)) {
    uni.showToast({ title: '仅支持文档或图片格式', icon: 'none' })
    return
  }
  if (file.size > MAX_FILE_SIZE) {
    uni.showToast({ title: '文件不能超过 5MB', icon: 'none' })
    return
  }
  selectedFile.value = file
  convertedFile.value = null
  if (imageExts.includes(ext)) {
    targetFormat.value = ['pdf', 'docx'].includes(targetFormat.value) ? targetFormat.value : 'pdf'
  } else if (targetFormat.value === ext) {
    targetFormat.value = targetFormats.find(item => item.value !== ext)?.value || 'pdf'
  }
}

const chooseDocumentFile = () => {
  // #ifdef MP-WEIXIN
  wx.chooseMessageFile({
    count: 1,
    type: 'file',
    extension: ['txt', 'html', 'htm', 'docx', 'pdf', 'jpg', 'jpeg', 'png', 'webp'],
    success: (res: any) => {
      const file = res.tempFiles?.[0]
      if (!file) return
      setPickedFile({ name: file.name, size: file.size, path: file.path })
    },
    fail: () => uni.showToast({ title: '未选择文件', icon: 'none' })
  })
  // #endif

  // #ifdef H5
  uni.chooseFile({
    count: 1,
    extension: ['.txt', '.html', '.htm', '.docx', '.pdf', '.jpg', '.jpeg', '.png', '.webp'],
    success: async (res: any) => {
      const file = res.tempFiles?.[0]
      if (!file) return
      const content = file.file || file.raw || file.path || file.tempFilePath
      setPickedFile({ name: file.name || file.path?.split('/').pop() || 'document', size: file.size || 0, path: file.path || file.tempFilePath, content })
    },
    fail: () => uni.showToast({ title: '未选择文件', icon: 'none' })
  })
  // #endif
}

const selectTargetFormat = (format: string) => {
  if (isTargetDisabled(format)) {
    uni.showToast({ title: isImageSource.value ? '图片仅支持转 PDF 或 Word' : '请选择不同的目标格式', icon: 'none' })
    return
  }
  targetFormat.value = format
  convertedFile.value = null
}

const readSelectedFileAsBase64 = async (file: PickedFile) => {
  // #ifdef MP-WEIXIN
  return new Promise<string>((resolve, reject) => {
    const fs = uni.getFileSystemManager()
    fs.readFile({
      filePath: file.path || '',
      encoding: 'base64',
      success: (res: any) => resolve(res.data),
      fail: reject
    })
  })
  // #endif

  // #ifdef H5
  const rawContent = file.content as any
  if (rawContent instanceof ArrayBuffer) {
    return arrayBufferToBase64(rawContent)
  }
  if (rawContent && typeof rawContent.arrayBuffer === 'function') {
    return arrayBufferToBase64(await rawContent.arrayBuffer())
  }
  if (typeof rawContent === 'string') {
    const response = await fetch(rawContent)
    if (!response.ok) throw new Error('读取文件失败')
    return arrayBufferToBase64(await response.arrayBuffer())
  }
  const filePath = file.path
  if (typeof filePath === 'string' && filePath) {
    const response = await fetch(filePath as string)
    if (!response.ok) throw new Error('读取文件失败')
    return arrayBufferToBase64(await response.arrayBuffer())
  }
  throw new Error('读取文件失败')
  // #endif
}

const convertDocument = async () => {
  if (!selectedFile.value) {
    uni.showToast({ title: '请先选择文件', icon: 'none' })
    return
  }
  if (!canConvert.value) {
    uni.showToast({ title: isImageSource.value ? '图片仅支持转 PDF 或 Word' : '请选择不同的目标格式', icon: 'none' })
    return
  }

  loading.value = true
  convertedFile.value = null
  try {
    const contentBase64 = await readSelectedFileAsBase64(selectedFile.value)
    const res = await convertDocumentBase64({
      filename: selectedFile.value.name,
      content_base64: contentBase64,
      target_format: targetFormat.value
    })
    if (res.code === 200 && res.data) {
      convertedFile.value = res.data
      uni.showToast({ title: '转换成功', icon: 'success' })
    } else {
      uni.showToast({ title: res.msg || '转换失败', icon: 'none' })
    }
  } catch (error: any) {
    uni.showToast({ title: error?.message || '转换失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const downloadConvertedFile = () => {
  const file = convertedFile.value
  if (!file) return

  // #ifdef H5
  const blob = new Blob([base64ToArrayBuffer(file.base64)], { type: file.media_type })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = file.filename
  link.click()
  URL.revokeObjectURL(url)
  uni.showToast({ title: '已开始下载', icon: 'success' })
  // #endif

  // #ifdef MP-WEIXIN
  const fs = uni.getFileSystemManager()
  const filePath = `${wx.env.USER_DATA_PATH}/${Date.now()}_${file.filename}`
  fs.writeFile({
    filePath,
    data: file.base64,
    encoding: 'base64',
    success: () => {
      if (/\.(pdf|docx)$/i.test(filePath)) {
        uni.openDocument({ filePath, showMenu: true })
      } else {
        uni.showModal({ title: '已保存', content: `文件已保存到：${filePath}`, showCancel: false })
      }
    },
    fail: () => uni.showToast({ title: '保存失败', icon: 'none' })
  })
  // #endif
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 24rpx;
  background: var(--theme-bg, linear-gradient(180deg, #eef5ff 0%, #f7f9fc 45%, #ffffff 100%));
}

.document-shell {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.card,
.hero-card {
  border-radius: 28rpx;
  border: 2rpx solid var(--theme-border, #eef2f7);
  background: var(--theme-surface, #ffffff);
  box-shadow: var(--theme-shadow-card, 0 10rpx 28rpx rgba(20, 35, 90, 0.08));
}

.hero-card {
  padding: 34rpx 30rpx;
}

.title {
  display: block;
  color: var(--theme-text, #17233d);
  font-size: 42rpx;
  font-weight: 900;
}

.subtitle {
  display: block;
  margin-top: 12rpx;
  color: var(--theme-text-secondary, #667085);
  font-size: 26rpx;
  line-height: 1.6;
}

.upload-card,
.format-card,
.result-card,
.scene-card {
  padding: 28rpx;
}

.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22rpx;
}

.section-title,
.scene-title {
  color: var(--theme-text, #17233d);
  font-size: 30rpx;
  font-weight: 800;
}

.section-badge {
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: var(--theme-primary-soft, #eef5ff);
  color: var(--theme-primary, #1677ff);
  font-size: 22rpx;
  font-weight: 700;
}

.select-btn,
.convert-btn,
.download-btn {
  width: 100%;
  border: none;
  border-radius: 999rpx;
  background: var(--theme-primary, #1677ff);
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 800;
}

.select-btn,
.download-btn {
  height: 84rpx;
  line-height: 84rpx;
}

.convert-btn {
  height: 92rpx;
  line-height: 92rpx;
  box-shadow: 0 16rpx 36rpx rgba(37, 99, 235, 0.22);
}

.convert-btn[disabled],
.select-btn[disabled] {
  opacity: 0.55;
}

.file-preview {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-top: 24rpx;
  padding: 22rpx;
  border-radius: 24rpx;
  background: var(--theme-surface-muted, #f6f8fb);
}

.file-icon {
  font-size: 50rpx;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name,
.file-meta {
  display: block;
}

.file-name {
  overflow: hidden;
  color: var(--theme-text, #17233d);
  font-size: 28rpx;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  margin-top: 8rpx;
  color: var(--theme-text-secondary, #667085);
  font-size: 24rpx;
}

.tips-box {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  margin-top: 24rpx;
  padding: 20rpx;
  border-radius: 22rpx;
  background: rgba(22, 119, 255, 0.08);
}

.tips-title {
  color: var(--theme-primary, #1677ff);
  font-size: 26rpx;
  font-weight: 800;
}

.tips-text {
  color: var(--theme-text-secondary, #667085);
  font-size: 24rpx;
  line-height: 1.5;
}

.format-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.format-item {
  display: flex;
  min-height: 150rpx;
  flex-direction: column;
  justify-content: center;
  gap: 8rpx;
  padding: 22rpx;
  border: 2rpx solid var(--theme-border, #eef2f7);
  border-radius: 24rpx;
  background: var(--theme-surface-muted, #f6f8fb);
}

.format-item.active {
  border-color: var(--theme-primary, #1677ff);
  background: var(--theme-primary-soft, #eef5ff);
}

.format-item.disabled {
  opacity: 0.45;
}

.format-icon {
  font-size: 42rpx;
}

.format-name {
  color: var(--theme-text, #17233d);
  font-size: 28rpx;
  font-weight: 900;
}

.format-desc {
  color: var(--theme-text-secondary, #667085);
  font-size: 22rpx;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 18rpx;
  margin-bottom: 24rpx;
}

.result-icon {
  font-size: 46rpx;
}

.result-title,
.result-desc {
  display: block;
}

.result-title {
  color: var(--theme-text, #17233d);
  font-size: 30rpx;
  font-weight: 900;
}

.result-desc {
  margin-top: 6rpx;
  color: var(--theme-text-secondary, #667085);
  font-size: 24rpx;
}

.scene-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  margin-top: 18rpx;
}

.scene-item {
  padding: 18rpx 20rpx;
  border-radius: 18rpx;
  background: var(--theme-surface-muted, #f6f8fb);
  color: var(--theme-text-secondary, #667085);
  font-size: 24rpx;
  line-height: 1.5;
}

@media (min-width: 768px) {
  .document-shell {
    max-width: 760px;
    margin: 0 auto;
  }

  .format-grid {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
</style>
