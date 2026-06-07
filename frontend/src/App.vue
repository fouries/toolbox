<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app'
import { initTheme } from '@/utils/theme'

onLaunch(() => {
  initTheme()
})
onShow(() => {})
onHide(() => {})
</script>

<style>
@import './uni.scss';
</style>
