<template>
  <view :class="['container', themeClass]">
    <view class="page-shell calendar-shell">
      <view class="page-header calendar-header">
        <text class="title">📅 黄历日历</text>
        <text class="subtitle">查看公历、农历、节气和每日宜忌</text>
      </view>

      <view class="calendar-card card">
        <view class="calendar-toolbar">
          <button class="month-btn" size="mini" @tap="goPrevMonth">‹ 上月</button>
          <picker mode="date" :value="selectedDateText" @change="onDateChange">
            <view class="date-picker">
              <text class="current-month">{{ currentYear }}年{{ currentMonth + 1 }}月</text>
              <text class="picker-hint">点击选择日期</text>
            </view>
          </picker>
          <button class="month-btn" size="mini" @tap="goNextMonth">下月 ›</button>
        </view>

        <view class="week-row">
          <text class="week-cell" v-for="week in weekLabels" :key="week">{{ week }}</text>
        </view>

        <view class="month-grid">
          <view
            v-for="day in monthDays"
            :key="day.dateText"
            class="day-cell"
            :class="{
              muted: !day.isCurrentMonth,
              today: day.isToday,
              selected: selectedDay.dateText === day.dateText,
              festival: Boolean(day.festival || day.solarTerm)
            }"
            @tap="selectDay(day)"
          >
            <text class="solar-day">{{ day.day }}</text>
            <text class="lunar-day">{{ day.lunarText }}</text>
          </view>
        </view>

        <button class="today-btn" size="mini" @tap="goToday">回到今天</button>
      </view>

      <view class="entry-card-grid">
        <view class="history-entry-card" @tap="goHistoryToday">
          <view class="history-entry-icon">📜</view>
          <view class="history-entry-content">
            <text class="history-entry-title">历史上的今天</text>
            <text class="history-entry-desc">看看这一天发生过哪些大事</text>
          </view>
          <text class="history-entry-arrow">›</text>
        </view>

        <view class="solar-term-entry-card" @tap="goSolarTerms">
          <view class="history-entry-icon solar-term-entry-icon">🌾</view>
          <view class="history-entry-content">
            <text class="history-entry-title">二十四节气</text>
            <text class="history-entry-desc">查询全年节气日期与物候提示</text>
          </view>
          <text class="history-entry-arrow">›</text>
        </view>
      </view>

      <view class="detail-card card">
        <view class="detail-top">
          <view class="date-stack">
            <text class="detail-date">{{ selectedDay.dateText }} {{ selectedDay.weekText }}</text>
            <text class="detail-lunar">农历 {{ selectedDay.lunarMonthText }}{{ selectedDay.lunarDayText }} · {{ selectedDay.lunarText }}</text>
          </view>
          <view class="zodiac-badge">
            <text>{{ selectedDay.zodiac }}</text>
          </view>
        </view>

        <view class="meta-grid">
          <view class="meta-item">
            <text class="meta-label">年柱</text>
            <text class="meta-value">{{ selectedDay.ganzhiYear }}</text>
          </view>
          <view class="meta-item">
            <text class="meta-label">月柱</text>
            <text class="meta-value">{{ selectedDay.ganzhiMonth }}</text>
          </view>
          <view class="meta-item">
            <text class="meta-label">日柱</text>
            <text class="meta-value">{{ selectedDay.ganzhiDay }}</text>
          </view>
        </view>

        <view class="festival-line" v-if="selectedDay.festival || selectedDay.solarTerm">
          <text class="festival-tag" v-if="selectedDay.festival">{{ selectedDay.festival }}</text>
          <text class="festival-tag term" v-if="selectedDay.solarTerm">{{ selectedDay.solarTerm }}</text>
        </view>

        <view class="almanac-grid">
          <view class="almanac-panel suit-panel">
            <view class="almanac-title">
              <text class="circle good">宜</text>
              <text>适合做</text>
            </view>
            <view class="tag-list">
              <text class="almanac-tag good-tag" v-for="item in selectedDay.suit" :key="`suit-${item}`">{{ item }}</text>
            </view>
          </view>

          <view class="almanac-panel avoid-panel">
            <view class="almanac-title">
              <text class="circle bad">忌</text>
              <text>尽量避开</text>
            </view>
            <view class="tag-list">
              <text class="almanac-tag bad-tag" v-for="item in selectedDay.avoid" :key="`avoid-${item}`">{{ item }}</text>
            </view>
          </view>
        </view>
      </view>

      <view class="note-card card">
        <text class="note-title">温馨提示</text>
        <text class="note-text">黄历宜忌基于传统民俗算法生成，仅供生活参考；重要事项请结合实际情况安排。</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useTheme } from '@/utils/theme'
import { buildMonthDays, getCalendarDay, type CalendarDay } from '@/utils/lunar-calendar'

const { themeClass } = useTheme()
const weekLabels = ['日', '一', '二', '三', '四', '五', '六']

const today = new Date()
const currentYear = ref(today.getFullYear())
const currentMonth = ref(today.getMonth())
const selectedDay = ref<CalendarDay>(getCalendarDay(today, today.getMonth()))

const monthDays = computed(() => buildMonthDays(currentYear.value, currentMonth.value))
const selectedDateText = computed(() => selectedDay.value.dateText)

const syncMonthToDate = (date: Date) => {
  currentYear.value = date.getFullYear()
  currentMonth.value = date.getMonth()
}

const selectDay = (day: CalendarDay) => {
  selectedDay.value = day
  if (!day.isCurrentMonth) {
    syncMonthToDate(day.date)
  }
}

const onDateChange = (event: any) => {
  const value = event?.detail?.value
  if (!value) return
  const date = new Date(`${value}T00:00:00`)
  syncMonthToDate(date)
  selectedDay.value = getCalendarDay(date, date.getMonth())
}

const goPrevMonth = () => {
  const date = new Date(currentYear.value, currentMonth.value - 1, 1)
  currentYear.value = date.getFullYear()
  currentMonth.value = date.getMonth()
}

const goNextMonth = () => {
  const date = new Date(currentYear.value, currentMonth.value + 1, 1)
  currentYear.value = date.getFullYear()
  currentMonth.value = date.getMonth()
}

const goToday = () => {
  const now = new Date()
  syncMonthToDate(now)
  selectedDay.value = getCalendarDay(now, now.getMonth())
}

const goHistoryToday = () => {
  uni.navigateTo({ url: `/pages/history-today/index?date=${selectedDay.value.dateText}` })
}

const goSolarTerms = () => {
  uni.navigateTo({ url: `/pages/solar-terms/index?date=${selectedDay.value.dateText}` })
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 30rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #fff7ed 0%, #fffaf5 46%, #ffffff 100%);
}

.calendar-shell {
  max-width: 980px;
}

.calendar-header {
  margin-bottom: 24rpx;
}

.calendar-card,
.history-entry-card,
.solar-term-entry-card,
.detail-card,
.note-card {
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid rgba(249, 115, 22, 0.12);
  box-shadow: 0 14rpx 38rpx rgba(194, 65, 12, 0.09);
}

.calendar-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 24rpx;
}

.month-btn,
.today-btn {
  margin: 0;
  border: none;
  border-radius: 999rpx;
  background: #fff7ed;
  color: #c2410c;
  font-size: 24rpx;
  line-height: 2.3;
  padding: 0 22rpx;
}

.date-picker {
  min-width: 260rpx;
  padding: 16rpx 24rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #fb923c 0%, #f97316 100%);
  color: #fff;
  text-align: center;
  box-shadow: 0 10rpx 24rpx rgba(249, 115, 22, 0.22);
}

.current-month,
.picker-hint {
  display: block;
}

.current-month {
  font-size: 34rpx;
  font-weight: 700;
}

.picker-hint {
  margin-top: 4rpx;
  font-size: 22rpx;
  opacity: 0.85;
}

.week-row,
.month-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
}

.week-row {
  margin-bottom: 10rpx;
}

.week-cell {
  text-align: center;
  font-size: 24rpx;
  color: #9a6a45;
  font-weight: 650;
}

.month-grid {
  gap: 8rpx;
}

.day-cell {
  min-height: 90rpx;
  border-radius: 18rpx;
  background: #fffaf5;
  border: 1rpx solid #ffedd5;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.day-cell.muted {
  opacity: 0.42;
}

.day-cell.today {
  border-color: #fb923c;
  box-shadow: inset 0 0 0 2rpx rgba(251, 146, 60, 0.22);
}

.day-cell.selected {
  background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
  color: #fff;
  transform: translateY(-2rpx);
  box-shadow: 0 10rpx 24rpx rgba(234, 88, 12, 0.24);
}

.day-cell.festival:not(.selected) {
  background: #fff7ed;
}

.solar-day {
  font-size: 30rpx;
  font-weight: 700;
  color: #3b2415;
}

.lunar-day {
  max-width: 92%;
  margin-top: 6rpx;
  font-size: 20rpx;
  color: #b45309;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.day-cell.selected .solar-day,
.day-cell.selected .lunar-day {
  color: #fff;
}

.today-btn {
  display: block;
  margin: 24rpx auto 0;
  background: #f97316;
  color: #fff;
}

.detail-card {
  margin-top: 24rpx;
}

.entry-card-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18rpx;
  margin-top: 24rpx;
}

.history-entry-card,
.solar-term-entry-card {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 24rpx;
}

.history-entry-icon {
  width: 76rpx;
  height: 76rpx;
  border-radius: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #fb923c 0%, #f97316 100%);
  color: #fff;
  font-size: 36rpx;
  box-shadow: 0 10rpx 24rpx rgba(249, 115, 22, 0.22);
}

.solar-term-entry-icon {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
  box-shadow: 0 10rpx 24rpx rgba(34, 197, 94, 0.2);
}

.history-entry-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.history-entry-title {
  color: #3b2415;
  font-size: 30rpx;
  font-weight: 760;
}

.history-entry-desc {
  color: #8a5a35;
  font-size: 24rpx;
}

.history-entry-arrow {
  color: #c2410c;
  font-size: 48rpx;
  line-height: 1;
}

.detail-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 22rpx;
}

.date-stack {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.detail-date {
  font-size: 34rpx;
  color: #3b2415;
  font-weight: 750;
}

.detail-lunar {
  font-size: 26rpx;
  color: #8a5a35;
}

.zodiac-badge {
  width: 86rpx;
  height: 86rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff7ed;
  color: #c2410c;
  font-size: 34rpx;
  font-weight: 800;
  border: 1rpx solid #fed7aa;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12rpx;
  margin-bottom: 22rpx;
}

.meta-item {
  padding: 18rpx 12rpx;
  border-radius: 18rpx;
  background: #fff7ed;
  text-align: center;
}

.meta-label,
.meta-value {
  display: block;
}

.meta-label {
  font-size: 22rpx;
  color: #b78b66;
}

.meta-value {
  margin-top: 6rpx;
  font-size: 28rpx;
  color: #7c2d12;
  font-weight: 700;
}

.festival-line {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-bottom: 22rpx;
}

.festival-tag {
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: #ffedd5;
  color: #c2410c;
  font-size: 24rpx;
  font-weight: 650;
}

.festival-tag.term {
  background: #ecfdf5;
  color: #047857;
}

.almanac-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 18rpx;
}

.almanac-panel {
  padding: 20rpx;
  border-radius: 22rpx;
  background: #fffaf5;
  border: 1rpx solid #ffedd5;
}

.almanac-title {
  display: flex;
  align-items: center;
  gap: 10rpx;
  margin-bottom: 14rpx;
  color: #3b2415;
  font-size: 28rpx;
  font-weight: 700;
}

.circle {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 24rpx;
}

.circle.good {
  background: #22c55e;
}

.circle.bad {
  background: #ef4444;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.almanac-tag {
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  font-size: 24rpx;
}

.good-tag {
  background: #ecfdf5;
  color: #047857;
}

.bad-tag {
  background: #fef2f2;
  color: #b91c1c;
}

.note-card {
  margin-top: 24rpx;
}

.note-title,
.note-text {
  display: block;
}

.note-title {
  color: #7c2d12;
  font-size: 28rpx;
  font-weight: 700;
  margin-bottom: 8rpx;
}

.note-text {
  color: #8a5a35;
  font-size: 24rpx;
  line-height: 1.7;
}

@media screen and (min-width: 768px) {
  .container {
    padding: 40px 24px 72px;
  }

  .calendar-card,
  .history-entry-card,
  .solar-term-entry-card,
  .detail-card,
  .note-card {
    padding: 28px;
  }

  .calendar-toolbar {
    margin-bottom: 22px;
  }

  .date-picker {
    min-width: 260px;
    padding: 14px 24px;
    border-radius: 18px;
  }

  .current-month {
    font-size: 26px;
  }

  .picker-hint {
    font-size: 13px;
  }

  .month-btn,
  .today-btn {
    font-size: 14px;
    padding: 0 18px;
  }

  .month-grid {
    gap: 10px;
  }

  .day-cell {
    min-height: 88px;
    border-radius: 16px;
  }

  .solar-day {
    font-size: 24px;
  }

  .lunar-day {
    font-size: 13px;
  }

  .detail-date {
    font-size: 26px;
  }

  .detail-lunar,
  .almanac-title {
    font-size: 17px;
  }

  .meta-grid,
  .entry-card-grid,
  .almanac-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .entry-card-grid,
  .almanac-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
