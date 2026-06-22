<template>
  <view :class="['container', themeClass]">
    <view class="page-shell document-shell">
      <view class="page-header hero-card">
        <text class="title">📄 文档转换/处理</text>
        <text class="subtitle">支持 TXT、HTML、Word、PDF 常见文档互转，也支持图片转 PDF / Word，转换后直接下载，不长期保存</text>
      </view>

      <view class="card mode-card">
        <view class="section-title-row">
          <text class="section-title">功能类型</text>
          <text class="section-badge">{{ modeBadge }}</text>
        </view>
        <view class="mode-grid">
          <view class="mode-item" :class="{ active: toolMode === 'convert' }" @click="switchToolMode('convert')">
            <text class="format-icon">🔄</text>
            <text class="format-name">文档互转</text>
            <text class="format-desc">文档/图片转格式</text>
          </view>
          <view class="mode-item" :class="{ active: toolMode === 'pdf' }" @click="switchToolMode('pdf')">
            <text class="format-icon">🧩</text>
            <text class="format-name">PDF 处理</text>
            <text class="format-desc">合并/拆分/压缩</text>
          </view>
        </view>
      </view>

      <view class="card upload-card" v-if="toolMode === 'convert'">
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
          <text class="tips-text">源文件：TXT、HTML、DOCX、PDF、JPG、PNG、WEBP、Excel、PPT</text>
          <text class="tips-text">目标格式：TXT、HTML、DOCX、PDF、Excel、PPT；图片支持转 PDF / Word</text>
          <text class="tips-text">说明：PDF/Excel/PPT 转换会提取可选中文本，扫描件图片 PDF 暂不做 OCR。</text>
        </view>
      </view>

      <view class="card pdf-card" v-if="toolMode === 'pdf'">
        <view class="section-title-row">
          <text class="section-title">PDF 文件</text>
          <text class="section-badge">{{ selectedPdfFiles.length }} 个</text>
        </view>
        <button class="select-btn" @click="choosePdfFiles" :disabled="loading">
          {{ pdfSelectButtonText }}
        </button>
        <button v-if="selectedPdfFiles.length" class="secondary-btn" @click="clearSelectedPdfFiles" :disabled="loading">清空已选 PDF</button>
        <view class="file-preview" v-for="(file, index) in selectedPdfFiles" :key="`${file.name}-${index}`">
          <text class="file-icon">📕</text>
          <view class="file-info">
            <text class="file-name">{{ file.name }}</text>
            <text class="file-meta">PDF · {{ formatSize(file.size) }}</text>
          </view>
        </view>
        <view class="tips-box">
          <text class="tips-title">PDF 能力</text>
          <text class="tips-text">合并请选择多个 PDF；拆分/压缩/编辑/去水印选择一个 PDF。</text>
          <text v-if="pdfOperation === 'merge'" class="tips-text">如果当前环境一次只能选一个，请点“继续添加 PDF”逐个添加，至少添加 2 个后即可合并。</text>
          <text class="tips-text">页码示例：1,3-5；去水印仅尝试移除指定文本/批注类水印，扫描图水印不保证。</text>
        </view>
      </view>

      <view class="card pdf-operation-card" v-if="toolMode === 'pdf'">
        <view class="section-title-row">
          <text class="section-title">PDF 操作</text>
          <text class="section-badge">{{ selectedPdfOperation.label }}</text>
        </view>
        <view class="format-grid">
          <view
            v-for="item in pdfOperations"
            :key="item.value"
            class="format-item"
            :class="{ active: pdfOperation === item.value }"
            @click="selectPdfOperation(item.value)"
          >
            <text class="format-icon">{{ item.icon }}</text>
            <text class="format-name">{{ item.label }}</text>
            <text class="format-desc">{{ item.desc }}</text>
          </view>
        </view>
        <view v-if="pdfOperation === 'compress'" class="compression-panel">
          <text class="option-title">压缩比</text>
          <view class="compression-grid">
            <view
              v-for="item in compressionOptions"
              :key="item.value"
              class="compression-item"
              :class="{ active: pdfCompressionLevel === item.value }"
              @click="selectCompressionLevel(item.value)"
            >
              <text class="compression-name">{{ item.label }}</text>
              <text class="compression-desc">{{ item.desc }}</text>
            </view>
          </view>
        </view>
        <input v-if="pdfOperation === 'extract'" class="text-input" v-model="pdfPages" placeholder="输入页码，如 1,3-5" />
        <view v-if="pdfOperation === 'edit'" class="edit-panel">
          <text class="option-title">编辑内容</text>
          <textarea class="text-area" v-model="pdfText" maxlength="160" placeholder="输入要添加到每页顶部的文字，例如：内部资料 / 已审核" />
          <text class="tips-text">当前编辑功能支持在每页顶部添加文字，复杂内容编辑后续再扩展。</text>
        </view>
        <input v-if="pdfOperation === 'remove_watermark'" class="text-input" v-model="pdfText" placeholder="输入要尝试移除的水印文字，可留空仅移除批注" />
      </view>

      <view class="card format-card" v-if="toolMode === 'convert'">
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

      <button class="convert-btn" @click="runPrimaryAction" :disabled="!canRunAction || loading">
        {{ loading ? '处理中...' : primaryActionText }}
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
          <view class="scene-item">PDF 合并/拆分：多份 PDF 合成一份，或按页码提取</view>
          <view class="scene-item">PDF 压缩/编辑/去水印：适合基础页面处理</view>
          <view class="scene-item">Excel/PPT → PDF/Word/TXT：提取内容后轻量转换</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { convertDocumentBase64, operatePdfBase64, type DocumentConvertResult } from '@/api'
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
const selectedPdfFiles = ref<PickedFile[]>([])
const targetFormat = ref('pdf')
const toolMode = ref<'convert' | 'pdf'>('convert')
const pdfOperation = ref('merge')
const pdfPages = ref('')
const pdfText = ref('')
const pdfCompressionLevel = ref<'low' | 'medium' | 'high'>('medium')
const loading = ref(false)
const convertedFile = ref<DocumentConvertResult | null>(null)

const targetFormats = [
  { value: 'pdf', label: 'PDF', icon: '📕', desc: '适合分享打印' },
  { value: 'docx', label: 'Word', icon: '📝', desc: '可继续编辑' },
  { value: 'txt', label: 'TXT', icon: '📄', desc: '纯文本提取' },
  { value: 'html', label: 'HTML', icon: '🌐', desc: '网页格式' },
  { value: 'xlsx', label: 'Excel', icon: '📊', desc: '表格数据' },
  { value: 'pptx', label: 'PPT', icon: '📽️', desc: '演示文稿' }
]

const pdfOperations = [
  { value: 'merge', label: 'PDF 合并', icon: '🧩', desc: '多份合一' },
  { value: 'extract', label: '拆分/提取', icon: '✂️', desc: '按页码导出' },
  { value: 'compress', label: 'PDF 压缩', icon: '📦', desc: '可选压缩比' },
  { value: 'edit', label: 'PDF 编辑', icon: '✏️', desc: '添加文字' },
  { value: 'remove_watermark', label: 'PDF 去水印', icon: '🧼', desc: '文本/批注' }
]

const compressionOptions = [
  { value: 'low', label: '低压缩', desc: '优先保留质量' },
  { value: 'medium', label: '中压缩', desc: '推荐平衡方案' },
  { value: 'high', label: '高压缩', desc: '尽量减小体积' }
] as const

const imageExts = ['jpg', 'jpeg', 'png', 'webp']
const documentExts = ['txt', 'html', 'docx', 'pdf', 'xlsx', 'pptx']

const sourceExt = computed(() => {
  const name = selectedFile.value?.name || ''
  const ext = name.split('.').pop()?.toLowerCase() || ''
  return ext === 'htm' ? 'html' : ext
})

const isImageSource = computed(() => imageExts.includes(sourceExt.value))
const sourceFormatLabel = computed(() => sourceExt.value ? sourceExt.value.toUpperCase() : '未知格式')
const sourceIcon = computed(() => isImageSource.value ? '🖼️' : targetFormats.find(item => item.value === sourceExt.value)?.icon || '📎')
const formatSize = (size: number) => {
  if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(2)} MB`
  return `${Math.max(1, Math.round(size / 1024))} KB`
}
const fileSizeLabel = computed(() => formatSize(selectedFile.value?.size || 0))
const modeBadge = computed(() => toolMode.value === 'convert' ? '格式转换' : 'PDF 工具')
const selectedPdfOperation = computed(() => pdfOperations.find(item => item.value === pdfOperation.value) || pdfOperations[0])
const pdfSelectButtonText = computed(() => {
  if (pdfOperation.value === 'merge') return selectedPdfFiles.value.length ? '继续添加 PDF' : '选择多个 PDF 文件'
  return selectedPdfFiles.value.length ? '重新选择 PDF' : '选择 PDF 文件'
})

const isTargetDisabled = (format: string) => {
  if (!sourceExt.value) return false
  if (isImageSource.value) return !['pdf', 'docx'].includes(format)
  return sourceExt.value === format
}

const canConvert = computed(() => Boolean(selectedFile.value && sourceExt.value && !isTargetDisabled(targetFormat.value)))
const canOperatePdf = computed(() => {
  if (pdfOperation.value === 'merge') return selectedPdfFiles.value.length >= 2
  if (!selectedPdfFiles.value.length) return false
  if (pdfOperation.value === 'extract') return Boolean(pdfPages.value.trim())
  if (pdfOperation.value === 'edit') return Boolean(pdfText.value.trim())
  return true
})
const canRunAction = computed(() => toolMode.value === 'convert' ? canConvert.value : canOperatePdf.value)
const primaryActionText = computed(() => toolMode.value === 'convert' ? '开始转换' : '开始处理 PDF')

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
const normalizeExt = (name: string) => {
  const ext = (name.split('.').pop() || '').toLowerCase()
  return ext === 'htm' ? 'html' : ext
}

const switchToolMode = (mode: 'convert' | 'pdf') => {
  toolMode.value = mode
  convertedFile.value = null
}

const selectPdfOperation = (operation: string) => {
  pdfOperation.value = operation
  convertedFile.value = null
}

const selectCompressionLevel = (level: 'low' | 'medium' | 'high') => {
  pdfCompressionLevel.value = level
  convertedFile.value = null
}

const setPickedFile = (file: PickedFile) => {
  const ext = normalizeExt(file.name)
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
    extension: ['txt', 'html', 'htm', 'docx', 'pdf', 'xlsx', 'pptx', 'jpg', 'jpeg', 'png', 'webp'],
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
    extension: ['.txt', '.html', '.htm', '.docx', '.pdf', '.xlsx', '.pptx', '.jpg', '.jpeg', '.png', '.webp'],
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

const setPickedPdfFiles = (files: PickedFile[]) => {
  const validFiles = files.filter(file => normalizeExt(file.name) === 'pdf')
  if (!validFiles.length) {
    uni.showToast({ title: '请选择 PDF 文件', icon: 'none' })
    return
  }
  if (validFiles.some(file => file.size > MAX_FILE_SIZE)) {
    uni.showToast({ title: '单个 PDF 不能超过 5MB', icon: 'none' })
    return
  }
  selectedPdfFiles.value = pdfOperation.value === 'merge' ? [...selectedPdfFiles.value, ...validFiles] : validFiles.slice(0, 1)
  convertedFile.value = null
}

const clearSelectedPdfFiles = () => {
  selectedPdfFiles.value = []
  convertedFile.value = null
}

const choosePdfFiles = () => {
  const count = pdfOperation.value === 'merge' ? 5 : 1
  // #ifdef MP-WEIXIN
  wx.chooseMessageFile({
    count,
    type: 'file',
    extension: ['pdf'],
    success: (res: any) => {
      const files = (res.tempFiles || []).map((file: any) => ({ name: file.name, size: file.size, path: file.path }))
      setPickedPdfFiles(files)
    },
    fail: () => uni.showToast({ title: '未选择文件', icon: 'none' })
  })
  // #endif

  // #ifdef H5
  uni.chooseFile({
    count,
    extension: ['.pdf'],
    success: (res: any) => {
      const files = (res.tempFiles || []).map((file: any) => {
        const content = file.file || file.raw || file.path || file.tempFilePath
        return { name: file.name || file.path?.split('/').pop() || 'document.pdf', size: file.size || 0, path: file.path || file.tempFilePath, content }
      })
      setPickedPdfFiles(files)
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

const operatePdf = async () => {
  if (!canOperatePdf.value) {
    uni.showToast({ title: '请补全 PDF 文件或参数', icon: 'none' })
    return
  }

  loading.value = true
  convertedFile.value = null
  try {
    const files = []
    for (const file of selectedPdfFiles.value) {
      files.push({ filename: file.name, content_base64: await readSelectedFileAsBase64(file) })
    }
    const res = await operatePdfBase64({
      operation: pdfOperation.value,
      files,
      pages: pdfPages.value,
      text: pdfText.value,
      compression_level: pdfCompressionLevel.value
    })
    if (res.code === 200 && res.data) {
      convertedFile.value = res.data
      uni.showToast({ title: '处理成功', icon: 'success' })
    } else {
      uni.showToast({ title: res.msg || '处理失败', icon: 'none' })
    }
  } catch (error: any) {
    uni.showToast({ title: error?.message || '处理失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const runPrimaryAction = () => toolMode.value === 'convert' ? convertDocument() : operatePdf()

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
  const safeFilename = String(file.filename || 'converted-file').replace(/[\\/:*?"<>|]/g, '_')
  const filePath = `${wx.env.USER_DATA_PATH}/${Date.now()}_${safeFilename}`
  fs.writeFile({
    filePath,
    data: file.base64,
    encoding: 'base64',
    success: () => {
      if (/\.(pdf|docx|xlsx|pptx)$/i.test(filePath)) {
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

.mode-card,
.pdf-card,
.pdf-operation-card,
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
.secondary-btn,
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
.secondary-btn,
.download-btn {
  height: 84rpx;
  line-height: 84rpx;
}

.secondary-btn {
  margin-top: 18rpx;
  background: var(--theme-surface-muted, #f6f8fb);
  color: var(--theme-primary, #1677ff);
}

.convert-btn {
  height: 92rpx;
  line-height: 92rpx;
  box-shadow: 0 16rpx 36rpx rgba(37, 99, 235, 0.22);
}

.convert-btn[disabled],
.select-btn[disabled],
.secondary-btn[disabled] {
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

.format-grid,
.mode-grid,
.compression-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.format-item,
.mode-item,
.compression-item {
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

.format-item.active,
.mode-item.active,
.compression-item.active {
  border-color: var(--theme-primary, #1677ff);
  background: var(--theme-primary-soft, #eef5ff);
}

.compression-panel,
.edit-panel {
  margin-top: 22rpx;
}

.option-title,
.compression-name,
.compression-desc {
  display: block;
}

.option-title {
  margin-bottom: 14rpx;
  color: var(--theme-text, #17233d);
  font-size: 26rpx;
  font-weight: 800;
}

.compression-item {
  min-height: 116rpx;
}

.compression-name {
  color: var(--theme-text, #17233d);
  font-size: 26rpx;
  font-weight: 800;
}

.compression-desc {
  margin-top: 8rpx;
  color: var(--theme-text-secondary, #667085);
  font-size: 22rpx;
  line-height: 1.4;
}

.text-area {
  box-sizing: border-box;
  width: 100%;
  min-height: 150rpx;
  padding: 20rpx 22rpx;
  border: 2rpx solid var(--theme-border, #e6e8ef);
  border-radius: 20rpx;
  background: var(--theme-surface-muted, #f6f8fb);
  color: var(--theme-text, #17233d);
  font-size: 26rpx;
  line-height: 1.5;
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
