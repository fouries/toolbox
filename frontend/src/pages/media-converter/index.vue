<template>
  <view :class="['container', themeClass]">
    <view class="page-shell media-shell">
      <view class="page-header hero-card">
        <text class="title">🎧 音视频转换</text>
        <text class="subtitle">音频裁剪、拼接/合并、音量调节、视频提取音频、声音转文字和轻量人声处理</text>
      </view>

      <view class="card operation-card">
        <view class="section-title-row">
          <text class="section-title">选择功能</text>
          <text class="section-badge">FFmpeg</text>
        </view>
        <view class="operation-grid">
          <view
            class="operation-item"
            :class="{ active: operation === item.value }"
            v-for="item in operations"
            :key="item.value"
            @click="selectOperation(item.value)"
          >
            <text class="operation-icon">{{ item.icon }}</text>
            <text class="operation-label">{{ item.label }}</text>
            <text class="operation-desc">{{ item.desc }}</text>
          </view>
        </view>
      </view>

      <view class="card upload-card" v-if="operation !== 'url_extract'">
        <view class="section-title-row">
          <text class="section-title">上传文件</text>
          <text class="section-badge">{{ selectedFiles.length }} 个</text>
        </view>
        <button class="select-btn" @click="chooseMediaFiles" :disabled="loading || selectedFiles.length >= maxFileCount">
          {{ multiFileMode ? (selectedFiles.length ? '继续添加文件' : '选择多个音频文件') : '选择音频/视频文件' }}
        </button>
        <button class="ghost-btn" v-if="selectedFiles.length" @click="clearSelectedFiles" :disabled="loading">清空已选</button>
        <view class="file-list" v-if="selectedFiles.length">
          <view class="file-preview" v-for="file in selectedFiles" :key="file.name + file.size">
            <text class="file-name">{{ file.name }}</text>
            <text class="file-size">{{ formatSize(file.size) }}</text>
          </view>
        </view>
      </view>

      <view class="card option-card" v-if="operation === 'url_extract'">
        <view class="section-title-row">
          <text class="section-title">视频链接</text>
          <text class="section-badge">直链</text>
        </view>
        <input class="text-input" v-model="videoUrl" placeholder="请输入 mp4/mov/webm 等可直接下载的视频链接" />
        <view class="tips-box compact">
          <text class="tips-text">目前支持公开视频/音频直链提取音频，不绕过平台登录、加密或防盗链。</text>
        </view>
      </view>

      <view class="card option-card" v-if="showTimeOptions">
        <view class="section-title-row">
          <text class="section-title">裁剪时间</text>
          <text class="section-badge">秒</text>
        </view>
        <view class="form-grid">
          <view class="form-item">
            <text class="form-label">开始秒数</text>
            <input class="text-input" type="digit" v-model="startTime" placeholder="0" />
          </view>
          <view class="form-item">
            <text class="form-label">结束秒数</text>
            <input class="text-input" type="digit" v-model="endTime" placeholder="例如 30" />
          </view>
        </view>
      </view>

      <view class="card option-card" v-if="operation === 'volume'">
        <view class="section-title-row">
          <text class="section-title">音量倍数</text>
          <text class="section-badge">0.1x - 5x</text>
        </view>
        <input class="text-input" type="digit" v-model="volumeLevel" placeholder="例如 1.5" />
      </view>

      <view class="card option-card" v-if="operation === 'vocal_remove'">
        <view class="section-title-row">
          <text class="section-title">人声处理</text>
          <text class="section-badge">轻量版</text>
        </view>
        <view class="format-grid">
          <view class="format-item" :class="{ active: vocalMode === 'instrumental' }" @click="vocalMode = 'instrumental'">
            <text class="format-label">消除人声</text>
            <text class="format-desc">保留伴奏</text>
          </view>
          <view class="format-item" :class="{ active: vocalMode === 'vocal' }" @click="vocalMode = 'vocal'">
            <text class="format-label">提取人声</text>
            <text class="format-desc">中置混合</text>
          </view>
        </view>
        <view class="tips-box compact">
          <text class="tips-text">当前为基于立体声相位/中置声道的轻量处理，不是 Demucs 级 AI 分离，效果取决于原音频。</text>
        </view>
      </view>

      <view class="card option-card" v-if="operation === 'transcribe'">
        <view class="section-title-row">
          <text class="section-title">转写设置</text>
          <text class="section-badge">Whisper</text>
        </view>
        <view class="format-grid">
          <view class="format-item" :class="{ active: language === item.value }" v-for="item in languages" :key="item.value" @click="language = item.value">
            <text class="format-label">{{ item.label }}</text>
            <text class="format-desc">{{ item.desc }}</text>
          </view>
        </view>
        <view class="tips-box compact">
          <text class="tips-text">声音转文字在服务器本地使用 Whisper 能力；长音频会比较慢，请优先上传短音频。</text>
        </view>
      </view>

      <view class="card format-card" v-if="operation !== 'transcribe'">
        <view class="section-title-row">
          <text class="section-title">输出格式</text>
          <text class="section-badge">{{ targetFormat.toUpperCase() }}</text>
        </view>
        <view class="format-grid">
          <view
            class="format-item"
            :class="{ active: targetFormat === item.value }"
            v-for="item in targetFormats"
            :key="item.value"
            @click="targetFormat = item.value"
          >
            <text class="format-label">{{ item.label }}</text>
            <text class="format-desc">{{ item.desc }}</text>
          </view>
        </view>
      </view>

      <button class="primary-btn" :disabled="!canSubmit || loading" @click="submitMediaTask">
        {{ loading ? '处理中...' : selectedOperation?.action || '开始处理' }}
      </button>

      <view class="card result-card" v-if="convertedFile || transcriptText">
        <view class="section-title-row">
          <text class="section-title">处理结果</text>
          <text class="section-badge success">完成</text>
        </view>
        <view v-if="transcriptText" class="transcript-box">
          <text class="transcript-title">识别文本</text>
          <textarea class="transcript-text" :value="transcriptText" disabled />
          <button class="ghost-btn" @click="copyTranscript">复制文字</button>
        </view>
        <view v-if="convertedFile" class="result-file">
          <text class="file-name">{{ convertedFile.filename }}</text>
          <text class="file-size">{{ convertedFile.media_type }}</text>
          <button class="download-btn" @click="downloadConvertedFile">下载/保存文件</button>
        </view>
      </view>

      <view class="card scene-card">
        <view class="section-title-row">
          <text class="section-title">能力说明</text>
          <text class="section-badge">本地处理</text>
        </view>
        <view class="scene-list">
          <view class="scene-item">音频裁剪：按开始/结束秒数截取片段</view>
          <view class="scene-item">音频拼接：多个音频按顺序接到一起</view>
          <view class="scene-item">音频合并：多个音频叠加混音</view>
          <view class="scene-item">声音转文字：调用服务器 Whisper 能力，输出文本</view>
          <view class="scene-item">人声消除/提取：轻量声道处理，复杂歌曲不保证完美</view>
          <view class="scene-item">视频转音频/链接提取：输出 MP3/WAV/M4A/AAC</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { convertMediaBase64, extractUrlAudioBase64, type MediaConvertResult } from '@/api'
import { useTheme } from '@/utils/theme'

declare const wx: any

const { themeClass } = useTheme()
const MAX_FILE_SIZE = 50 * 1024 * 1024

type Operation = 'trim' | 'concat' | 'merge' | 'transcribe' | 'vocal_remove' | 'volume' | 'video_to_audio' | 'url_extract'

interface PickedFile {
  name: string
  size: number
  path?: string
  raw?: File | Blob
  file?: File | Blob
  tempFilePath?: string
}

const operations: Array<{ value: Operation; label: string; icon: string; desc: string; action: string; multi?: boolean }> = [
  { value: 'trim', label: '音频裁剪', icon: '✂️', desc: '截取指定时间段', action: '开始裁剪' },
  { value: 'concat', label: '音频拼接', icon: '🔗', desc: '按顺序连接多个音频', action: '开始拼接', multi: true },
  { value: 'merge', label: '音频合并', icon: '🎚️', desc: '多个音轨叠加混音', action: '开始合并', multi: true },
  { value: 'transcribe', label: '声音转文字', icon: '📝', desc: '语音识别输出文字', action: '开始识别' },
  { value: 'vocal_remove', label: '人声消除/提取', icon: '🎤', desc: '轻量分离伴奏或人声', action: '开始处理' },
  { value: 'volume', label: '音量调节', icon: '🔊', desc: '放大或降低音量', action: '调节音量' },
  { value: 'video_to_audio', label: '视频转音频', icon: '🎬', desc: '从视频文件提取音频', action: '提取音频' },
  { value: 'url_extract', label: '链接提取音频', icon: '🌐', desc: '从视频直链提取音频', action: '提取链接音频' }
]

const targetFormats = [
  { value: 'mp3', label: 'MP3', desc: '通用压缩音频' },
  { value: 'wav', label: 'WAV', desc: '无损/大文件' },
  { value: 'm4a', label: 'M4A', desc: '移动端友好' },
  { value: 'aac', label: 'AAC', desc: '高压缩率' }
]

const languages = [
  { value: 'zh', label: '中文', desc: '普通话/中文内容' },
  { value: 'en', label: '英文', desc: '英文内容' },
  { value: 'auto', label: '自动', desc: '自动判断语言' }
]

const operation = ref<Operation>('trim')
const selectedFiles = ref<PickedFile[]>([])
const targetFormat = ref('mp3')
const startTime = ref('0')
const endTime = ref('30')
const volumeLevel = ref('1.5')
const vocalMode = ref<'instrumental' | 'vocal'>('instrumental')
const language = ref('zh')
const videoUrl = ref('')
const loading = ref(false)
const convertedFile = ref<MediaConvertResult | null>(null)
const transcriptText = ref('')

const selectedOperation = computed(() => operations.find(item => item.value === operation.value))
const multiFileMode = computed(() => Boolean(selectedOperation.value?.multi))
const maxFileCount = computed(() => multiFileMode.value ? 6 : 1)
const showTimeOptions = computed(() => operation.value === 'trim')
const canSubmit = computed(() => {
  if (operation.value === 'url_extract') return /^https?:\/\//.test(videoUrl.value.trim())
  if (multiFileMode.value) return selectedFiles.value.length >= 2
  return selectedFiles.value.length >= 1
})

const selectOperation = (value: Operation) => {
  operation.value = value
  selectedFiles.value = []
  convertedFile.value = null
  transcriptText.value = ''
}

const normalizePickedFile = (file: any, index: number): PickedFile => {
  const path = file.path || file.tempFilePath || file.url || ''
  const name = file.name || (path ? path.split('/').pop() : '') || `media-${Date.now()}-${index}`
  return {
    name,
    size: Number(file.size || file.file?.size || file.raw?.size || 0),
    path,
    tempFilePath: file.tempFilePath,
    raw: file.raw,
    file: file.file || file
  }
}

const setPickedFiles = (files: PickedFile[]) => {
  const valid = files.filter(file => {
    if (file.size && file.size > MAX_FILE_SIZE) {
      uni.showToast({ title: `${file.name} 超过 50MB`, icon: 'none' })
      return false
    }
    return true
  })
  selectedFiles.value = multiFileMode.value ? [...selectedFiles.value, ...valid].slice(0, maxFileCount.value) : valid.slice(0, 1)
  convertedFile.value = null
  transcriptText.value = ''
}

const chooseMediaFiles = () => {
  const count = Math.max(1, maxFileCount.value - selectedFiles.value.length)
  // #ifdef MP-WEIXIN
  wx.chooseMessageFile({
    count,
    type: 'file',
    extension: ['mp3', 'wav', 'm4a', 'aac', 'ogg', 'flac', 'mp4', 'mov', 'm4v', 'webm'],
    success: (res: any) => {
      setPickedFiles((res.tempFiles || []).map((file: any, index: number) => normalizePickedFile(file, index)))
    }
  })
  // #endif

  // #ifdef H5
  uni.chooseFile({
    count,
    type: 'all',
    extension: ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.mp4', '.mov', '.m4v', '.webm'],
    success: (res: UniApp.ChooseFileSuccessCallbackResult) => {
      const tempFiles = Array.isArray(res.tempFiles) ? res.tempFiles : (res.tempFiles ? [res.tempFiles] : [])
      setPickedFiles(tempFiles.map((file: any, index: number) => normalizePickedFile(file, index)))
    }
  })
  // #endif
}

const clearSelectedFiles = () => {
  selectedFiles.value = []
  convertedFile.value = null
  transcriptText.value = ''
}

const readFileAsBase64 = async (file: PickedFile): Promise<string> => {
  const raw = file.file || file.raw
  if (raw && typeof (raw as Blob).arrayBuffer === 'function') {
    const buffer = await (raw as Blob).arrayBuffer()
    return arrayBufferToBase64(buffer)
  }
  // #ifdef MP-WEIXIN
  const fs = uni.getFileSystemManager()
  return await new Promise((resolve, reject) => {
    fs.readFile({
      filePath: file.path || file.tempFilePath || '',
      encoding: 'base64',
      success: res => resolve(String(res.data)),
      fail: reject
    })
  })
  // #endif

  // #ifdef H5
  if (file.path) {
    const response = await fetch(file.path as string)
    const buffer = await response.arrayBuffer()
    return arrayBufferToBase64(buffer)
  }
  // #endif
  throw new Error('读取文件失败')
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

const buildOptions = () => ({
  target_format: targetFormat.value,
  start: startTime.value,
  end: endTime.value,
  volume: volumeLevel.value,
  vocal_mode: vocalMode.value,
  language: language.value
})

const submitMediaTask = async () => {
  if (!canSubmit.value) {
    uni.showToast({ title: multiFileMode.value ? '请至少选择 2 个音频文件' : '请补全文件或链接', icon: 'none' })
    return
  }
  loading.value = true
  convertedFile.value = null
  transcriptText.value = ''
  try {
    let res
    if (operation.value === 'url_extract') {
      res = await extractUrlAudioBase64({ url: videoUrl.value.trim(), target_format: targetFormat.value })
    } else {
      const files = []
      for (const file of selectedFiles.value) {
        files.push({ filename: file.name, content_base64: await readFileAsBase64(file) })
      }
      res = await convertMediaBase64({ operation: operation.value, files, options: buildOptions() })
    }
    const data = res.data || {}
    if (operation.value === 'transcribe') {
      transcriptText.value = String(data.text || '')
      uni.showToast({ title: '识别完成', icon: 'success' })
    } else {
      convertedFile.value = data
      uni.showToast({ title: '处理完成', icon: 'success' })
    }
  } catch (error: any) {
    uni.showToast({ title: error?.message || '音视频处理失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const copyTranscript = () => {
  uni.setClipboardData({ data: transcriptText.value })
}

const base64ToArrayBuffer = (base64: string) => {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i)
  return bytes.buffer
}

const downloadConvertedFile = () => {
  if (!convertedFile.value?.base64 || !convertedFile.value.filename) return
  // #ifdef H5
  const blob = new Blob([base64ToArrayBuffer(convertedFile.value.base64)], { type: convertedFile.value.media_type || 'audio/mpeg' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = convertedFile.value.filename
  link.click()
  URL.revokeObjectURL(url)
  // #endif

  // #ifdef MP-WEIXIN
  const fs = uni.getFileSystemManager()
  const filePath = `${wx.env.USER_DATA_PATH}/${convertedFile.value.filename}`
  fs.writeFile({
    filePath,
    data: convertedFile.value.base64,
    encoding: 'base64',
    success: () => uni.showToast({ title: '已保存到小程序本地', icon: 'success' }),
    fail: () => uni.showToast({ title: '保存失败', icon: 'none' })
  })
  // #endif
}

const formatSize = (size: number) => {
  if (!size) return '未知大小'
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}
</script>

<style scoped>
.container { min-height: 100vh; background: var(--theme-bg, #f5f7fb); }
.page-shell { padding: 28rpx; }
.hero-card { padding: 36rpx; border-radius: 30rpx; background: linear-gradient(135deg, #111827, #7c3aed); color: #fff; box-shadow: 0 18rpx 42rpx rgba(17, 24, 39, .22); }
.title { display: block; font-size: 42rpx; font-weight: 800; margin-bottom: 14rpx; }
.subtitle { display: block; font-size: 26rpx; line-height: 1.6; opacity: .92; }
.card { margin-top: 24rpx; padding: 28rpx; border-radius: 28rpx; background: var(--theme-card, #fff); box-shadow: 0 12rpx 34rpx rgba(15, 23, 42, .08); }
.section-title-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20rpx; }
.section-title { font-size: 30rpx; font-weight: 800; color: var(--theme-text, #111827); }
.section-badge { padding: 8rpx 16rpx; border-radius: 999rpx; background: #eef2ff; color: #4f46e5; font-size: 22rpx; }
.section-badge.success { background: #dcfce7; color: #16a34a; }
.operation-grid, .format-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18rpx; }
.operation-item, .format-item { padding: 22rpx; border: 2rpx solid var(--theme-border, #e5e7eb); border-radius: 22rpx; background: var(--theme-muted, #f8fafc); }
.operation-item.active, .format-item.active { border-color: #7c3aed; background: #f5f3ff; }
.operation-icon { display: block; font-size: 34rpx; margin-bottom: 8rpx; }
.operation-label, .format-label { display: block; font-size: 27rpx; font-weight: 800; color: var(--theme-text, #111827); }
.operation-desc, .format-desc { display: block; margin-top: 8rpx; color: var(--theme-text-secondary, #64748b); font-size: 22rpx; line-height: 1.4; }
.select-btn, .primary-btn, .download-btn { width: 100%; border: none; border-radius: 22rpx; background: linear-gradient(135deg, #7c3aed, #2563eb); color: #fff; font-weight: 800; font-size: 28rpx; }
.select-btn { margin-bottom: 16rpx; }
.primary-btn { margin-top: 26rpx; height: 92rpx; line-height: 92rpx; }
.primary-btn[disabled], .select-btn[disabled] { opacity: .55; }
.ghost-btn { margin-top: 14rpx; border-radius: 20rpx; background: #f1f5f9; color: #475569; font-size: 25rpx; }
.file-preview { display: flex; justify-content: space-between; gap: 18rpx; padding: 18rpx 0; border-bottom: 1rpx solid var(--theme-border, #e5e7eb); }
.file-name { flex: 1; color: var(--theme-text, #111827); font-size: 25rpx; word-break: break-all; }
.file-size { color: var(--theme-text-secondary, #64748b); font-size: 22rpx; }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18rpx; }
.form-label { display: block; margin-bottom: 10rpx; font-size: 24rpx; color: var(--theme-text-secondary, #64748b); }
.text-input { box-sizing: border-box; width: 100%; height: 82rpx; padding: 0 22rpx; border: 2rpx solid var(--theme-border, #e5e7eb); border-radius: 18rpx; background: var(--theme-muted, #f8fafc); color: var(--theme-text, #111827); }
.tips-box { margin-top: 18rpx; padding: 18rpx; border-radius: 18rpx; background: #fff7ed; }
.tips-text { display: block; color: #9a3412; font-size: 23rpx; line-height: 1.5; }
.transcript-box { padding: 18rpx; border-radius: 20rpx; background: var(--theme-muted, #f8fafc); }
.transcript-title { display: block; margin-bottom: 12rpx; font-weight: 800; color: var(--theme-text, #111827); }
.transcript-text { box-sizing: border-box; width: 100%; min-height: 260rpx; padding: 18rpx; border-radius: 18rpx; background: #fff; color: #111827; font-size: 25rpx; line-height: 1.6; }
.result-file { padding: 18rpx; border-radius: 20rpx; background: var(--theme-muted, #f8fafc); }
.download-btn { margin-top: 18rpx; }
.scene-list { display: flex; flex-direction: column; gap: 14rpx; }
.scene-item { padding: 18rpx; border-radius: 18rpx; background: var(--theme-muted, #f8fafc); color: var(--theme-text-secondary, #64748b); font-size: 24rpx; line-height: 1.5; }
</style>
