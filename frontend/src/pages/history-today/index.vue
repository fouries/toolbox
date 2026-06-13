<template>
  <view :class="['container', themeClass]">
    <view class="page-shell history-shell">
      <view class="page-header history-header">
        <text class="title">📜 历史上的今天</text>
        <text class="subtitle">查看这一天发生过的历史事件</text>
      </view>

      <view class="history-picker-card card">
        <picker mode="date" :value="selectedDateText" @change="onDateChange">
          <view class="date-picker">
            <text class="picker-label">选择日期</text>
            <text class="picker-value">{{ displayDate }}</text>
          </view>
        </picker>
        <button class="calendar-btn" size="mini" @tap="goCalendar">返回老黄历</button>
      </view>

      <view class="summary-card card">
        <text class="summary-title">{{ monthDayText }} · 历史上的今天</text>
        <text class="summary-desc">精选 {{ events.length }} 条历史事件，按年份从早到晚排列。</text>
      </view>

      <view class="event-list">
        <view class="event-card" v-for="event in events" :key="`${event.year}-${event.title}`">
          <view class="event-year-wrap">
            <text class="event-year">{{ event.year }}</text>
            <text class="event-category">{{ event.category }}</text>
          </view>
          <view class="event-content">
            <text class="event-title">{{ event.title }}</text>
            <text class="event-desc">{{ event.desc }}</text>
          </view>
        </view>
      </view>

      <view class="note-card card">
        <text class="note-title">小提示</text>
        <text class="note-text">事件数据为本地精选内容，后续可继续扩展更多日期与更详细资料。</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useTheme } from '@/utils/theme'
import { formatDate, formatMonthDay, getHistoryTodayEvents } from '@/utils/history-today'

const { themeClass } = useTheme()

const selectedDate = ref(new Date())
const selectedDateText = computed(() => formatDate(selectedDate.value))
const monthDayText = computed(() => formatMonthDay(selectedDate.value).replace('-', '月') + '日')
const displayDate = computed(() => `${selectedDate.value.getFullYear()}年${monthDayText.value}`)
const events = computed(() => getHistoryTodayEvents(selectedDate.value))

const onDateChange = (event: any) => {
  const value = event?.detail?.value
  if (!value) return
  selectedDate.value = new Date(`${value}T00:00:00`)
}

const goCalendar = () => {
  uni.navigateBack({
    fail: () => {
      uni.redirectTo({ url: '/pages/calendar/index' })
    }
  })
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  padding: 30rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, #fff7ed 0%, #fffaf5 48%, #ffffff 100%);
}

.history-shell {
  max-width: 900px;
}

.history-header {
  margin-bottom: 24rpx;
}

.history-picker-card,
.summary-card,
.event-card,
.note-card {
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid rgba(249, 115, 22, 0.12);
  box-shadow: 0 14rpx 38rpx rgba(194, 65, 12, 0.09);
}

.history-picker-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.date-picker {
  min-width: 320rpx;
  padding: 18rpx 24rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #fb923c 0%, #f97316 100%);
  color: #fff;
  box-shadow: 0 10rpx 24rpx rgba(249, 115, 22, 0.22);
}

.picker-label,
.picker-value {
  display: block;
}

.picker-label {
  font-size: 22rpx;
  opacity: 0.86;
}

.picker-value {
  margin-top: 4rpx;
  font-size: 32rpx;
  font-weight: 750;
}

.calendar-btn {
  margin: 0;
  border: none;
  border-radius: 999rpx;
  background: #fff7ed;
  color: #c2410c;
  font-size: 24rpx;
  line-height: 2.4;
  padding: 0 24rpx;
}

.summary-card {
  margin-top: 24rpx;
}

.summary-title,
.summary-desc,
.event-title,
.event-desc,
.note-title,
.note-text {
  display: block;
}

.summary-title {
  color: #3b2415;
  font-size: 34rpx;
  font-weight: 800;
}

.summary-desc {
  margin-top: 8rpx;
  color: #8a5a35;
  font-size: 26rpx;
}

.event-list {
  margin-top: 24rpx;
}

.event-card {
  display: grid;
  grid-template-columns: 150rpx minmax(0, 1fr);
  gap: 20rpx;
  margin-bottom: 18rpx;
}

.event-year-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 120rpx;
  border-radius: 22rpx;
  background: #fff7ed;
}

.event-year {
  color: #c2410c;
  font-size: 34rpx;
  font-weight: 850;
}

.event-category {
  margin-top: 6rpx;
  padding: 4rpx 12rpx;
  border-radius: 999rpx;
  background: #ffedd5;
  color: #9a3412;
  font-size: 20rpx;
}

.event-content {
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.event-title {
  color: #3b2415;
  font-size: 30rpx;
  font-weight: 750;
}

.event-desc {
  margin-top: 10rpx;
  color: #8a5a35;
  font-size: 25rpx;
  line-height: 1.65;
}

.note-card {
  margin-top: 24rpx;
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

  .history-picker-card,
  .summary-card,
  .event-card,
  .note-card {
    padding: 28px;
  }

  .date-picker {
    min-width: 260px;
    padding: 14px 22px;
    border-radius: 18px;
  }

  .picker-label {
    font-size: 13px;
  }

  .picker-value {
    font-size: 24px;
  }

  .calendar-btn {
    font-size: 14px;
    padding: 0 18px;
  }

  .summary-title {
    font-size: 26px;
  }

  .summary-desc {
    font-size: 16px;
  }

  .event-card {
    grid-template-columns: 120px minmax(0, 1fr);
    gap: 22px;
  }

  .event-year-wrap {
    min-height: 108px;
    border-radius: 18px;
  }

  .event-year {
    font-size: 28px;
  }

  .event-category {
    font-size: 13px;
  }

  .event-title {
    font-size: 20px;
  }

  .event-desc {
    font-size: 15px;
  }
}
</style>
