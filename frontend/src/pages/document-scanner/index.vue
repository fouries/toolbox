<template>
  <view :class="['container', themeClass]">
    <view class="page-shell scanner-shell">
      <view class="page-header hero-card">
        <text class="title">📷 拍照扫描</text>
        <text class="subtitle">调用摄像头拍照或从相册选择图片，多张图片生成 PDF / Word / PPT，文件直接下载，不长期保存</text>
      </view>

      <view class="card scan-card">
        <view class="section-title-row">
          <text class="section-title">扫描图片</text>
          <text class="section-badge">{{ scanFiles.length }} / 10 张</text>
        </view>
        <button class="select-btn" @click="takeScanPhoto" :disabled="loading || scanFiles.length >= 10">调用摄像头拍照</button>
        <button class="secondary-btn" @click="chooseScanImages" :disabled="loading || scanFiles.length >= 10">从相册选择图片</button>
        <button v-if="scanFiles.length" class="secondary-btn" @click="clearScanFiles" :disabled="loading">清空扫描图片</button>

        <view class="scan-preview-grid" v-if="scanFiles.length">
          <view class="scan-preview" v-for="(file, index) in scanFiles" :key="`${file.name}-${index}`">
            <text class="scan-index">{{ index + 1 }}</text>
            <view class="scan-info">
              <text class="scan-name">{{ file.name }}</text>
              <text class="scan-size">{{ formatSize(file.size) }}</text>
            </view>
          </view>
        </view>

        <view class="tips-box">
          <text class="tips-title">扫描说明</text>
          <text class="tips-text">支持 JPG、PNG、WEBP 图片；一次最多 10 张，按添加顺序生成文档。</text>
          <text class="tips-text">当前是图片扫描生成文档，不做 OCR 文字识别。</text>
        </view>
      </view>

      <view class="card format-card">
        <view class="section-title-row">
          <text class="section-title">扫描模式</text>
          <text class="section-badge">{{ selectedScanMode.label }}</text>
        </view>
        <view class="format-grid scan-mode-grid">
          <view v-for="item in scanModeOptions" :key="item.value" class="format-item" :class="{ active: scanMode === item.value }" @click="selectScanMode(item.value)">
            <text class="format-icon">{{ item.icon }}</text>
            <text class="format-name">{{ item.label }}</text>
            <text class="format-desc">{{ item.desc }}</text>
          </view>
        </view>
      </view>

      <view class="card format-card">
        <view class="section-title-row">
          <text class="section-title">生成类型</text>
          <text class="section-badge">{{ scanTargetFormat.toUpperCase() }}</text>
        </view>
        <input class="text-input" v-model="scanTitle" maxlength="40" placeholder="文档标题，如：扫描文档" />
        <view class="format-grid scan-target-grid">
          <view
            v-for="item in scanTargetFormats"
            :key="item.value"
            class="format-item"
            :class="{ active: scanTargetFormat === item.value }"
            @click="selectScanTargetFormat(item.value)"
          >
            <text class="format-icon">{{ item.icon }}</text>
            <text class="format-name">{{ item.label }}</text>
            <text class="format-desc">{{ item.desc }}</text>
          </view>
        </view>
      </view>

      <button class="convert-btn" @click="generateScanDocument" :disabled="!canScanDocument || loading">
        {{ loading ? '生成中...' : '生成扫描文档' }}
      </button>

      <view class="card result-card" v-if="convertedFile">
        <view class="result-header">
          <text class="result-icon">✅</text>
          <view class="result-info">
            <text class="result-title">生成完成</text>
            <text class="result-desc">{{ convertedFile.filename }}</text>
          </view>
        </view>
        <button class="download-btn" @click="downloadConvertedFile">下载/打开文件</button>
      </view>

      <view class="card scene-card">
        <text class="scene-title">常用场景</text>
        <view class="scene-list">
          <view class="scene-item">拍照 → PDF：把纸质资料、票据、合同整理成 PDF</view>
          <view class="scene-item">自动增强/灰度/黑白扫描：适合 A4 资料归档和打印</view>
          <view class="scene-item">多图 → Word：把扫描图片插入 Word，方便继续补充文字</view>
          <view class="scene-item">多图 → PPT：每张图片生成一页演示文稿</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { scanDocumentBase64, type DocumentConvertResult } from '@/api'
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
const imageExts = ['jpg', 'jpeg', 'png', 'webp']
const scanFiles = ref<PickedFile[]>([])
const scanTargetFormat = ref<'pdf' | 'docx' | 'pptx'>('pdf')
const scanTitle = ref('扫描文档')
const scanMode = ref<'color' | 'enhance' | 'gray' | 'bw'>('enhance')
const loading = ref(false)
const convertedFile = ref<DocumentConvertResult | null>(null)

const scanTargetFormats = [
  { value: 'pdf', label: 'PDF', icon: '📕', desc: '适合归档打印' },
  { value: 'docx', label: 'Word', icon: '📝', desc: '图片页可编辑' },
  { value: 'pptx', label: 'PPT', icon: '📽️', desc: '一图一页演示' }
] as const

const scanModeOptions = [
  { value: 'color', label: '彩色原图', icon: '🌈', desc: '保留原始色彩' },
  { value: 'enhance', label: '自动增强', icon: '✨', desc: '增强对比和清晰度' },
  { value: 'gray', label: '灰度扫描', icon: '⚪', desc: '适合资料归档' },
  { value: 'bw', label: '黑白扫描', icon: '⚫', desc: '接近复印件效果' }
] as const

const selectedScanMode = computed(() => scanModeOptions.find(item => item.value === scanMode.value) || scanModeOptions[1])

const canScanDocument = computed(() => scanFiles.value.length > 0)

const formatSize = (size: number) => {
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(2)} MB`
  return `${Math.max(1, Math.round(size / 1024))} KB`
}

const normalizeExt = (name: string) => {
  const ext = (name.split('.').pop() || '').toLowerCase()
  return ext === 'htm' ? 'html' : ext
}

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

const selectScanTargetFormat = (format: 'pdf' | 'docx' | 'pptx') => {
  scanTargetFormat.value = format
  convertedFile.value = null
}

const selectScanMode = (mode: 'color' | 'enhance' | 'gray' | 'bw') => {
  scanMode.value = mode
  convertedFile.value = null
}

const normalizeScanPickedFiles = (res: any, prefix = 'scan') => {
  const tempFiles = res.tempFiles || []
  const paths = res.tempFilePaths || []
  if (tempFiles.length) {
    return tempFiles.map((file: any, index: number) => {
      const path = file.path || file.tempFilePath || paths[index]
      const name = file.name || path?.split('/').pop() || `${prefix}-${Date.now()}-${index + 1}.jpg`
      const content = file.file || file.raw || path
      return { name, size: file.size || 0, path, content }
    })
  }
  return paths.map((path: string, index: number) => ({ name: path?.split('/').pop() || `${prefix}-${Date.now()}-${index + 1}.jpg`, size: 0, path, content: path }))
}

const setPickedScanFiles = (files: PickedFile[]) => {
  const remain = 10 - scanFiles.value.length
  if (remain <= 0) {
    uni.showToast({ title: '一次最多 10 张', icon: 'none' })
    return
  }
  const candidates = files.slice(0, remain)
  const validFiles = candidates.filter(file => imageExts.includes(normalizeExt(file.name)))
  if (!validFiles.length) {
    uni.showToast({ title: '请选择 JPG、PNG、WEBP 图片', icon: 'none' })
    return
  }
  if (validFiles.some(file => file.size > MAX_FILE_SIZE)) {
    uni.showToast({ title: '单张图片不能超过 5MB', icon: 'none' })
    return
  }
  scanFiles.value = [...scanFiles.value, ...validFiles]
  convertedFile.value = null
}

const takeScanPhoto = () => {
  uni.chooseImage({
    count: 1,
    sourceType: ['camera'],
    sizeType: ['compressed'],
    success: (res: any) => setPickedScanFiles(normalizeScanPickedFiles(res, 'camera')),
    fail: () => uni.showToast({ title: '未拍照', icon: 'none' })
  })
}

const chooseScanImages = () => {
  uni.chooseImage({
    count: Math.max(1, Math.min(9, 10 - scanFiles.value.length)),
    sourceType: ['album'],
    sizeType: ['compressed'],
    success: (res: any) => setPickedScanFiles(normalizeScanPickedFiles(res, 'album')),
    fail: () => uni.showToast({ title: '未选择图片', icon: 'none' })
  })
}

const clearScanFiles = () => {
  scanFiles.value = []
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

const generateScanDocument = async () => {
  if (!canScanDocument.value) {
    uni.showToast({ title: '请先拍照或选择图片', icon: 'none' })
    return
  }

  loading.value = true
  convertedFile.value = null
  try {
    const files = []
    for (const file of scanFiles.value) {
      files.push({ filename: file.name, content_base64: await readSelectedFileAsBase64(file) })
    }
    const res = await scanDocumentBase64({
      files,
      target_format: scanTargetFormat.value,
      title: scanTitle.value.trim() || '扫描文档',
      mode: scanMode.value
    })
    if (res.code === 200 && res.data) {
      convertedFile.value = res.data
      uni.showToast({ title: '生成成功', icon: 'success' })
    } else {
      uni.showToast({ title: res.msg || '生成失败', icon: 'none' })
    }
  } catch (error: any) {
    uni.showToast({ title: error?.message || '生成失败', icon: 'none' })
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
  document.body.appendChild(link)
  link.click()
  setTimeout(() => {
    URL.revokeObjectURL(url)
    document.body.removeChild(link)
  }, 1000)
  uni.showToast({ title: '已开始下载', icon: 'success' })
  // #endif

  // #ifdef MP-WEIXIN
  const fs = uni.getFileSystemManager()
  const safeFilename = String(file.filename || 'scan-file').replace(/[\\/:*?"<>|]/g, '_')
  const filePath = `${wx.env.USER_DATA_PATH}/${Date.now()}_${safeFilename}`
  fs.writeFile({
    filePath,
    data: file.base64,
    encoding: 'base64',
    success: () => {
      if (/\.(pdf|docx|pptx)$/i.test(filePath)) {
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
  background: var(--theme-bg, linear-gradient(180deg, #fff7ed 0%, #f7f9fc 45%, #ffffff 100%));
}

.scanner-shell {
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

.scan-card,
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
  background: rgba(249, 115, 22, 0.12);
  color: #f97316;
  font-size: 22rpx;
  font-weight: 700;
}

.select-btn,
.secondary-btn,
.convert-btn,
.download-btn {
  width: 100%;
  border: none;
  border-radius: 999rpx;
  background: #f97316;
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 800;
}

.select-btn,
.secondary-btn,
.download-btn {
  height: 84rpx;
  line-height: 84rpx;
}

.secondary-btn {
  margin-top: 18rpx;
  background: var(--theme-surface-muted, #f6f8fb);
  color: #f97316;
}

.convert-btn {
  height: 92rpx;
  line-height: 92rpx;
  box-shadow: 0 16rpx 36rpx rgba(249, 115, 22, 0.22);
}

.convert-btn[disabled],
.select-btn[disabled],
.secondary-btn[disabled] {
  opacity: 0.55;
}

.scan-preview-grid,
.format-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.scan-preview-grid {
  margin-top: 22rpx;
}

.scan-preview,
.format-item {
  border: 2rpx solid var(--theme-border, #eef2f7);
  border-radius: 24rpx;
  background: var(--theme-surface-muted, #f6f8fb);
}

.scan-preview {
  display: flex;
  align-items: center;
  gap: 14rpx;
  min-height: 96rpx;
  padding: 16rpx;
}

.scan-index {
  width: 44rpx;
  height: 44rpx;
  flex: 0 0 44rpx;
  border-radius: 50%;
  background: #f97316;
  color: #fff;
  font-size: 24rpx;
  font-weight: 800;
  line-height: 44rpx;
  text-align: center;
}

.scan-info {
  min-width: 0;
}

.scan-name,
.scan-size {
  display: block;
}

.scan-name {
  overflow: hidden;
  color: var(--theme-text, #17233d);
  font-size: 24rpx;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scan-size {
  margin-top: 6rpx;
  color: var(--theme-text-secondary, #667085);
  font-size: 22rpx;
}

.tips-box {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  margin-top: 24rpx;
  padding: 20rpx;
  border-radius: 22rpx;
  background: rgba(249, 115, 22, 0.1);
}

.tips-title {
  color: #f97316;
  font-size: 26rpx;
  font-weight: 800;
}

.tips-text {
  color: var(--theme-text-secondary, #667085);
  font-size: 24rpx;
  line-height: 1.5;
}

.text-input {
  box-sizing: border-box;
  width: 100%;
  height: 84rpx;
  margin-bottom: 22rpx;
  padding: 0 22rpx;
  border: 2rpx solid var(--theme-border, #e6e8ef);
  border-radius: 20rpx;
  background: var(--theme-surface-muted, #f6f8fb);
  color: var(--theme-text, #17233d);
  font-size: 26rpx;
}

.format-item {
  display: flex;
  min-height: 150rpx;
  flex-direction: column;
  justify-content: center;
  gap: 8rpx;
  padding: 22rpx;
}

.format-item.active {
  border-color: #f97316;
  background: rgba(249, 115, 22, 0.12);
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
  .scanner-shell {
    max-width: 760px;
    margin: 0 auto;
  }

  .format-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}
</style>
