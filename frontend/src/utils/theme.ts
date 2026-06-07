import { computed, ref } from 'vue'

export type ThemeId = 'light' | 'warm' | 'fresh' | 'minimal' | 'night'

export interface ThemeOption {
  id: ThemeId
  name: string
  icon: string
  className: string
}

const STORAGE_KEY = 'toolbox-theme'

export const themes: ThemeOption[] = [
  { id: 'light', name: '默认浅色', icon: '☀️', className: 'theme-light' },
  { id: 'warm', name: '暖阳橙', icon: '🌇', className: 'theme-warm' },
  { id: 'fresh', name: '清新绿', icon: '🌿', className: 'theme-fresh' },
  { id: 'minimal', name: '极简灰', icon: '◻️', className: 'theme-minimal' },
  { id: 'night', name: '暗夜蓝', icon: '🌙', className: 'theme-night' }
]

const currentThemeId = ref<ThemeId>('light')

function findTheme(id?: string | null): ThemeOption {
  return themes.find(theme => theme.id === id) || themes[0]
}

function persistTheme(id: ThemeId) {
  try {
    uni.setStorageSync('toolbox-theme', id)
  } catch (error) {
    console.warn('保存主题失败', error)
  }
}

function applyDocumentTheme(id: ThemeId) {
  // #ifdef H5
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', id)
  }
  // #endif
}

export function setTheme(id: ThemeId, options: { persist?: boolean } = {}) {
  const theme = findTheme(id)
  currentThemeId.value = theme.id
  applyDocumentTheme(theme.id)
  if (options.persist !== false) {
    persistTheme(theme.id)
  }
}

export function initTheme() {
  let savedTheme = ''
  try {
    savedTheme = uni.getStorageSync(STORAGE_KEY)
  } catch (error) {
    console.warn('读取主题失败', error)
  }
  setTheme(findTheme(savedTheme).id, { persist: false })
}

export function showThemePicker() {
  uni.showActionSheet({
    itemList: themes.map(theme => `${theme.icon} ${theme.name}`),
    success: ({ tapIndex }) => {
      const theme = themes[tapIndex]
      if (theme) {
        setTheme(theme.id)
      }
    }
  })
}

export function useTheme() {
  const currentTheme = computed(() => findTheme(currentThemeId.value))
  const themeClass = computed(() => currentTheme.value.className)

  return {
    themes,
    currentTheme,
    themeClass,
    setTheme,
    showThemePicker
  }
}
