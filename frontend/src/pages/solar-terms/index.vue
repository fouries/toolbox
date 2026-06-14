<template>
  <view :class="['container', themeClass]">
    <view class="page-shell solar-shell">
      <view class="page-header solar-header">
        <text class="title">🌾 二十四节气</text>
        <text class="subtitle">查询全年节气日期、季节变化和养生提示</text>
      </view>

      <view class="summary-card card">
        <view>
          <text class="summary-label">当前日期</text>
          <text class="summary-date">{{ selectedDateText }}</text>
        </view>
        <picker mode="date" :value="selectedDateText" @change="onDateChange">
          <view class="date-switch">切换日期</view>
        </picker>
      </view>

      <view class="highlight-grid">
        <view class="highlight-card card" v-if="currentSolarTerm">
          <text class="highlight-label">当前节气</text>
          <text class="highlight-title">{{ currentSolarTerm.name }}</text>
          <text class="highlight-desc">{{ currentSolarTerm.date }} · {{ currentSolarTerm.desc }}</text>
        </view>
        <view class="highlight-card card" v-if="nextTerm">
          <text class="highlight-label">下一个节气</text>
          <text class="highlight-title">{{ nextTerm.name }}</text>
          <text class="highlight-desc">{{ nextTerm.date }} · {{ nextTerm.desc }}</text>
        </view>
      </view>

      <view class="term-list card">
        <view
          class="term-card"
          :class="{ active: currentSolarTerm?.date === term.date, next: nextTerm?.date === term.date }"
          v-for="term in solarTerms"
          :key="term.name"
        >
          <view class="term-date">
            <text class="term-month">{{ term.month }}月</text>
            <text class="term-day">{{ term.day }}</text>
          </view>
          <view class="term-info">
            <text class="term-name">{{ term.name }}</text>
            <text class="term-season">{{ term.season }}季 · 第 {{ term.index + 1 }} 个节气</text>
            <text class="term-desc">{{ term.desc }}</text>
          </view>
        </view>
      </view>

      <view class="note-card card">
        <text class="note-title">说明</text>
        <text class="note-text">节气日期采用常用近似日期，适合日常查询参考；精确交节时刻请以天文历法为准。</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useTheme } from '@/utils/theme'
import { formatDate, getSolarTermsForYear, type SolarTermItem } from '@/utils/lunar-calendar'

const { themeClass } = useTheme()
const selectedDate = ref(new Date())
const currentYear = computed(() => selectedDate.value.getFullYear())
const selectedDateText = computed(() => formatDate(selectedDate.value))
const solarTerms = computed(() => getSolarTermsForYear(currentYear.value))

const currentSolarTerm = computed<SolarTermItem | null>(() => {
  const selectedTime = selectedDate.value.getTime()
  const passedTerms = solarTerms.value.filter(term => new Date(`${term.date}T00:00:00`).getTime() <= selectedTime)
  if (passedTerms.length > 0) return passedTerms[passedTerms.length - 1]

  const previousYearTerms = getSolarTermsForYear(currentYear.value - 1)
  return previousYearTerms[previousYearTerms.length - 1] || null
})
const nextTerm = computed<SolarTermItem | null>(() => {
  const selectedTime = selectedDate.value.getTime()
  return solarTerms.value.find(term => new Date(`${term.date}T00:00:00`).getTime() >= selectedTime) || solarTerms.value[0]
})

const setDate = (value?: string) => {
  if (!value) return
  const date = new Date(`${value}T00:00:00`)
  if (!Number.isNaN(date.getTime())) selectedDate.value = date
}

const onDateChange = (event: any) => {
  setDate(event?.detail?.value)
}

onLoad((options: any) => {
  setDate(options?.date)
})
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 30rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #ecfdf5 0%, #f7fee7 48%, #ffffff 100%);
}

.solar-shell {
  max-width: 980px;
}

.solar-header {
  margin-bottom: 24rpx;
}

.summary-card,
.highlight-card,
.term-list,
.note-card {
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid rgba(34, 197, 94, 0.14);
  box-shadow: 0 14rpx 38rpx rgba(22, 101, 52, 0.08);
}

.summary-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 22rpx;
}

.summary-label,
.summary-date,
.highlight-label,
.highlight-title,
.highlight-desc,
.term-month,
.term-day,
.term-name,
.term-season,
.term-desc,
.note-title,
.note-text {
  display: block;
}

.summary-label,
.highlight-label {
  color: #64748b;
  font-size: 24rpx;
}

.summary-date {
  margin-top: 6rpx;
  color: #14532d;
  font-size: 42rpx;
  font-weight: 800;
}

.date-switch {
  padding: 14rpx 26rpx;
  border-radius: 999rpx;
  background: #16a34a;
  color: #fff;
  font-size: 26rpx;
  font-weight: 700;
}

.highlight-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18rpx;
  margin-bottom: 22rpx;
}

.highlight-title {
  margin-top: 10rpx;
  color: #166534;
  font-size: 38rpx;
  font-weight: 800;
}

.highlight-desc,
.term-desc,
.note-text {
  margin-top: 8rpx;
  color: #64748b;
  font-size: 24rpx;
  line-height: 1.65;
}

.term-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16rpx;
}

.term-card {
  display: flex;
  gap: 18rpx;
  padding: 20rpx;
  border-radius: 24rpx;
  background: #f8fafc;
  border: 1rpx solid #e2e8f0;
}

.term-card.active,
.term-card.next {
  background: #ecfdf5;
  border-color: #86efac;
}

.term-date {
  width: 96rpx;
  height: 96rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.term-month {
  font-size: 22rpx;
}

.term-day {
  font-size: 36rpx;
  font-weight: 800;
}

.term-info {
  flex: 1;
  min-width: 0;
}

.term-name {
  color: #17233d;
  font-size: 30rpx;
  font-weight: 760;
}

.term-season {
  margin-top: 6rpx;
  color: #16a34a;
  font-size: 23rpx;
}

.note-card {
  margin-top: 22rpx;
}

.note-title {
  color: #14532d;
  font-size: 28rpx;
  font-weight: 760;
}

@media screen and (min-width: 768px) {
  .container {
    padding: 40px 24px 72px;
  }

  .summary-card,
  .highlight-card,
  .term-list,
  .note-card {
    padding: 28px;
  }

  .highlight-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .term-list {
    grid-template-columns: repeat(2, 1fr);
    gap: 18px;
  }

  .summary-date {
    font-size: 34px;
  }

  .highlight-title {
    font-size: 30px;
  }
}
</style>
