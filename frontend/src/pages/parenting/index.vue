<template>
  <view class="container" :class="themeClass">
    <view class="page-shell parenting-shell">
      <view class="hero-card">
        <text class="hero-icon">👶</text>
        <text class="title">育儿工具</text>
        <text class="subtitle">覆盖孕晚期、0-1 岁、1-3 岁、3-6 岁的清单、提醒、喂养睡眠参考和成长记录</text>
      </view>

      <view class="card stage-card">
        <view class="section-title-row">
          <text class="section-title">选择阶段</text>
          <text class="section-badge">{{ activeStageInfo.label }}</text>
        </view>
        <view class="stage-grid">
          <view
            class="stage-item"
            :class="{ active: activeStage === item.id }"
            v-for="item in stages"
            :key="item.id"
            @click="activeStage = item.id"
          >
            <text class="stage-icon">{{ item.icon }}</text>
            <text class="stage-label">{{ item.label }}</text>
            <text class="stage-desc">{{ item.desc }}</text>
          </view>
        </view>
      </view>

      <view class="card tools-card" v-if="activeStage === 'pregnancy'">
        <view class="section-title-row">
          <text class="section-title">孕晚期助手</text>
          <text class="section-badge">28 周+</text>
        </view>
        <view class="form-grid">
          <view class="form-item">
            <text class="form-label">预产期</text>
            <picker mode="date" :value="dueDate" @change="onDueDateChange">
              <view class="picker-box">{{ dueDate || '选择预产期' }}</view>
            </picker>
          </view>
          <view class="form-item">
            <text class="form-label">距离预产期</text>
            <view class="result-pill">{{ dueDateSummary }}</view>
          </view>
        </view>
        <view class="counter-box">
          <view>
            <text class="counter-title">胎动计数</text>
            <text class="counter-desc">常用参考：2 小时内约 10 次；如明显减少请及时联系医生。</text>
          </view>
          <view class="counter-actions">
            <button class="mini-btn" @click="kickCount++">+1</button>
            <button class="mini-btn ghost" @click="kickCount = 0">重置</button>
          </view>
          <text class="counter-number">{{ kickCount }} 次</text>
        </view>
      </view>

      <view class="card tools-card" v-if="activeStage === 'infant'">
        <view class="section-title-row">
          <text class="section-title">0-1 岁喂养睡眠参考</text>
          <text class="section-badge">宝宝月龄</text>
        </view>
        <view class="form-grid">
          <view class="form-item">
            <text class="form-label">宝宝月龄</text>
            <input class="text-input" type="number" v-model="babyMonth" placeholder="如 3" />
          </view>
          <view class="form-item">
            <text class="form-label">体重 kg</text>
            <input class="text-input" type="digit" v-model="babyWeight" placeholder="如 6.5" />
          </view>
        </view>
        <view class="result-grid">
          <view class="result-card-mini">
            <text class="result-label">奶量估算</text>
            <text class="result-value">{{ milkSuggestion }}</text>
          </view>
          <view class="result-card-mini">
            <text class="result-label">睡眠参考</text>
            <text class="result-value">{{ sleepSuggestion }}</text>
          </view>
        </view>
      </view>

      <view class="card tools-card" v-if="activeStage === 'toddler'">
        <view class="section-title-row">
          <text class="section-title">1-3 岁日常养育</text>
          <text class="section-badge">习惯建立</text>
        </view>
        <view class="habit-grid">
          <view class="habit-item" v-for="item in toddlerHabits" :key="item.title">
            <text class="habit-icon">{{ item.icon }}</text>
            <text class="habit-title">{{ item.title }}</text>
            <text class="habit-desc">{{ item.desc }}</text>
          </view>
        </view>
      </view>

      <view class="card tools-card" v-if="activeStage === 'preschool'">
        <view class="section-title-row">
          <text class="section-title">3-6 岁入园成长</text>
          <text class="section-badge">能力准备</text>
        </view>
        <view class="habit-grid">
          <view class="habit-item" v-for="item in preschoolSkills" :key="item.title">
            <text class="habit-icon">{{ item.icon }}</text>
            <text class="habit-title">{{ item.title }}</text>
            <text class="habit-desc">{{ item.desc }}</text>
          </view>
        </view>
      </view>

      <view class="card checklist-card">
        <view class="section-title-row">
          <text class="section-title">阶段清单</text>
          <text class="section-badge">{{ checkedCount }}/{{ activeChecklist.length }}</text>
        </view>
        <view class="check-list">
          <view class="check-item" v-for="item in activeChecklist" :key="item" @click="toggleCheck(item)">
            <text class="check-box" :class="{ checked: checkedItems.includes(item) }">{{ checkedItems.includes(item) ? '✓' : '' }}</text>
            <text class="check-text">{{ item }}</text>
          </view>
        </view>
        <button class="ghost-btn" @click="clearChecks">清空本阶段勾选</button>
      </view>

      <view class="card vaccine-card" v-if="activeStage !== 'pregnancy'">
        <view class="section-title-row">
          <text class="section-title">疫苗/体检提醒</text>
          <text class="section-badge">参考</text>
        </view>
        <view class="timeline-list">
          <view class="timeline-item" v-for="item in activeVaccines" :key="item.age + item.text">
            <text class="timeline-age">{{ item.age }}</text>
            <text class="timeline-text">{{ item.text }}</text>
          </view>
        </view>
      </view>

      <view class="card redflag-card">
        <view class="section-title-row">
          <text class="section-title">需要及时就医/咨询的情况</text>
          <text class="section-badge danger">红旗</text>
        </view>
        <view class="redflag-list">
          <text class="redflag-item" v-for="item in redFlags" :key="item">• {{ item }}</text>
        </view>
      </view>

      <view class="card disclaimer-card">
        <text class="disclaimer-title">温馨提示</text>
        <text class="disclaimer-text">本工具用于家庭记录和常识提醒，不替代医生诊断、产检建议、儿童保健或急诊处理；疫苗、用药、辅食和发育评估请以当地医生/社区卫生服务中心建议为准。</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useTheme } from '@/utils/theme'

const { themeClass } = useTheme()

type StageId = 'pregnancy' | 'infant' | 'toddler' | 'preschool'

const activeStage = ref<StageId>('pregnancy')
const dueDate = ref('')
const kickCount = ref(0)
const babyMonth = ref('3')
const babyWeight = ref('6.5')
const checkedItems = ref<string[]>([])

const stages = [
  { id: 'pregnancy' as StageId, label: '孕晚期', desc: '待产、胎动、产检准备', icon: '🤰' },
  { id: 'infant' as StageId, label: '0-1 岁', desc: '喂养、睡眠、疫苗体检', icon: '🍼' },
  { id: 'toddler' as StageId, label: '1-3 岁', desc: '辅食过渡、语言、如厕', icon: '🧸' },
  { id: 'preschool' as StageId, label: '3-6 岁', desc: '入园、自理、社交启蒙', icon: '🎒' }
]

const checklistMap: Record<StageId, string[]> = {
  pregnancy: ['整理待产包：证件、产检资料、妈妈用品、宝宝衣物', '确认产检时间和分娩医院路线', '准备月子/产后照护安排', '练习数胎动并记录异常', '学习临产信号：规律宫缩、破水、见红', '安装/检查安全提篮或安全座椅'],
  infant: ['记录喂奶、尿布、睡眠和体温', '按月龄预约疫苗和儿童保健', '准备安全睡眠环境：仰卧、床面简洁', '4-6 月后根据医生建议评估辅食', '每天进行俯趴练习和亲子互动', '定期清洁奶瓶、玩具和口腔'],
  toddler: ['建立固定作息和睡前流程', '每天亲子阅读和语言互动', '逐步培养自主进食和喝水', '观察如厕准备信号，不强迫训练', '家中防摔、防烫、防误食', '限制屏幕时间，增加户外活动'],
  preschool: ['练习自己穿脱衣物、洗手、整理物品', '培养表达需求和情绪的能力', '准备入园体检和接送信息', '建立规则意识和轮流等待', '每日运动、绘本、精细动作练习', '关注视力、口腔、睡眠和情绪变化']
}

const vaccineMap = {
  infant: [
    { age: '出生', text: '乙肝第 1 剂、卡介苗等，以当地接种本为准' },
    { age: '1 月', text: '乙肝第 2 剂，儿童保健随访' },
    { age: '2-6 月', text: '脊灰、百白破等多剂次接种，按预约完成' },
    { age: '6-12 月', text: '乙肝第 3 剂、A 群流脑等，继续体检评估' }
  ],
  toddler: [
    { age: '12-18 月', text: '麻腮风/乙脑/甲肝等按地区程序接种' },
    { age: '18-24 月', text: '百白破、甲肝等加强/补种，关注语言运动发育' },
    { age: '2-3 岁', text: '年度儿保、口腔和视力筛查，补齐漏种疫苗' }
  ],
  preschool: [
    { age: '3-4 岁', text: '入园体检、视力口腔筛查、身高体重评估' },
    { age: '4 岁', text: '脊灰等加强接种，以接种本通知为准' },
    { age: '5-6 岁', text: '入学前体检、白破等加强/补种咨询' }
  ]
}

const toddlerHabits = [
  { icon: '🍚', title: '吃饭', desc: '三餐两点，鼓励自己吃，不用零食替代正餐。' },
  { icon: '💬', title: '语言', desc: '多回应、多扩展句子，少用命令，多描述正在发生的事。' },
  { icon: '🚽', title: '如厕', desc: '能表达、尿布较长时间干爽后再尝试，避免责骂。' },
  { icon: '🛡️', title: '安全', desc: '药品清洁剂上锁，窗边防护，热水和小物件远离孩子。' }
]

const preschoolSkills = [
  { icon: '🧼', title: '自理', desc: '洗手、如厕、穿脱衣物、收拾书包逐步独立。' },
  { icon: '🤝', title: '社交', desc: '练习轮流、等待、表达拒绝和寻求帮助。' },
  { icon: '📚', title: '认知', desc: '绘本、数数、分类、拼图和开放式提问。' },
  { icon: '🏃', title: '运动', desc: '跑跳攀爬、平衡、画线剪纸等粗细动作结合。' }
]

const redFlags = ['孕晚期胎动明显减少、阴道流血、破水、剧烈腹痛或持续头痛眼花', '3 月龄内发热、呼吸困难、反应差、持续呕吐或抽搐', '孩子精神差、脱水、口唇发紫、高热不退或皮疹伴发热', '发育明显倒退、长期不看人不回应、语言/运动明显落后请做专业评估']

const activeStageInfo = computed(() => stages.find(item => item.id === activeStage.value) || stages[0])
const activeChecklist = computed(() => checklistMap[activeStage.value])
const checkedCount = computed(() => activeChecklist.value.filter(item => checkedItems.value.includes(item)).length)
const activeVaccines = computed(() => activeStage.value === 'pregnancy' ? [] : vaccineMap[activeStage.value])

const dueDateSummary = computed(() => {
  if (!dueDate.value) return '未设置'
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const due = new Date(dueDate.value)
  due.setHours(0, 0, 0, 0)
  const diff = Math.ceil((due.getTime() - today.getTime()) / 86400000)
  if (Number.isNaN(diff)) return '日期无效'
  if (diff > 0) return `还有 ${diff} 天`
  if (diff === 0) return '就是今天'
  return `已过 ${Math.abs(diff)} 天`
})

const milkSuggestion = computed(() => {
  const weight = Number(babyWeight.value)
  const month = Number(babyMonth.value)
  if (!weight || weight <= 0) return '填写体重后估算'
  if (month >= 6) return '6 月龄后奶量和辅食并行，请按儿保建议调整'
  const low = Math.round(weight * 120)
  const high = Math.round(weight * 150)
  return `约 ${low}-${high} ml/天，仅作粗略参考`
})

const sleepSuggestion = computed(() => {
  const month = Number(babyMonth.value)
  if (Number.isNaN(month)) return '填写月龄后查看'
  if (month < 3) return '约 14-17 小时/天'
  if (month < 6) return '约 12-16 小时/天'
  if (month < 12) return '约 12-15 小时/天'
  return '1 岁后约 11-14 小时/天'
})

const onDueDateChange = (event: any) => {
  dueDate.value = event.detail.value
}

const toggleCheck = (item: string) => {
  checkedItems.value = checkedItems.value.includes(item)
    ? checkedItems.value.filter(existing => existing !== item)
    : [...checkedItems.value, item]
}

const clearChecks = () => {
  checkedItems.value = checkedItems.value.filter(item => !activeChecklist.value.includes(item))
}
</script>

<style scoped>
.container { min-height: 100vh; background: var(--theme-bg, #f6f7fb); }
.page-shell { padding: 28rpx; }
.hero-card { position: relative; overflow: hidden; padding: 38rpx; border-radius: 32rpx; color: #fff; background: linear-gradient(135deg, #fb7185, #f97316 52%, #facc15); box-shadow: 0 18rpx 44rpx rgba(251, 113, 133, .25); }
.hero-icon { display: block; font-size: 54rpx; margin-bottom: 10rpx; }
.title { display: block; font-size: 44rpx; font-weight: 900; margin-bottom: 12rpx; }
.subtitle { display: block; font-size: 26rpx; line-height: 1.6; opacity: .95; }
.card { margin-top: 24rpx; padding: 28rpx; border-radius: 28rpx; background: var(--theme-card, #fff); box-shadow: 0 12rpx 34rpx rgba(15, 23, 42, .08); }
.section-title-row { display: flex; justify-content: space-between; align-items: center; gap: 16rpx; margin-bottom: 20rpx; }
.section-title { font-size: 30rpx; font-weight: 900; color: var(--theme-text, #111827); }
.section-badge { flex-shrink: 0; padding: 8rpx 16rpx; border-radius: 999rpx; background: #fff1f2; color: #e11d48; font-size: 22rpx; font-weight: 700; }
.section-badge.danger { background: #fee2e2; color: #dc2626; }
.stage-grid, .habit-grid, .result-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18rpx; }
.stage-item, .habit-item, .result-card-mini { padding: 22rpx; border: 2rpx solid var(--theme-border, #e5e7eb); border-radius: 22rpx; background: var(--theme-muted, #f8fafc); }
.stage-item.active { border-color: #fb7185; background: #fff1f2; }
.stage-icon, .habit-icon { display: block; font-size: 36rpx; margin-bottom: 8rpx; }
.stage-label, .habit-title, .result-label { display: block; font-size: 27rpx; font-weight: 900; color: var(--theme-text, #111827); }
.stage-desc, .habit-desc { display: block; margin-top: 8rpx; color: var(--theme-text-secondary, #64748b); font-size: 22rpx; line-height: 1.45; }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18rpx; }
.form-label { display: block; margin-bottom: 10rpx; font-size: 24rpx; color: var(--theme-text-secondary, #64748b); }
.text-input, .picker-box, .result-pill { box-sizing: border-box; width: 100%; min-height: 82rpx; padding: 0 22rpx; border: 2rpx solid var(--theme-border, #e5e7eb); border-radius: 18rpx; background: var(--theme-muted, #f8fafc); color: var(--theme-text, #111827); line-height: 82rpx; font-size: 25rpx; }
.result-pill { color: #e11d48; font-weight: 900; }
.counter-box { margin-top: 20rpx; padding: 22rpx; border-radius: 22rpx; background: #fff7ed; }
.counter-title { display: block; font-size: 28rpx; font-weight: 900; color: #9a3412; }
.counter-desc { display: block; margin-top: 8rpx; font-size: 23rpx; line-height: 1.5; color: #9a3412; }
.counter-actions { display: flex; gap: 14rpx; margin-top: 18rpx; }
.mini-btn { flex: 1; height: 72rpx; line-height: 72rpx; border-radius: 18rpx; border: none; background: #fb7185; color: #fff; font-size: 25rpx; font-weight: 900; }
.mini-btn.ghost, .ghost-btn { background: #f1f5f9; color: #475569; }
.counter-number { display: block; margin-top: 16rpx; font-size: 36rpx; color: #e11d48; font-weight: 900; text-align: center; }
.result-card-mini { background: #f0f9ff; }
.result-value { display: block; margin-top: 10rpx; font-size: 24rpx; line-height: 1.45; color: #0369a1; font-weight: 800; }
.check-list, .timeline-list, .redflag-list { display: flex; flex-direction: column; gap: 14rpx; }
.check-item { display: flex; align-items: flex-start; gap: 14rpx; padding: 16rpx; border-radius: 18rpx; background: var(--theme-muted, #f8fafc); }
.check-box { flex-shrink: 0; width: 36rpx; height: 36rpx; border-radius: 10rpx; border: 2rpx solid #fda4af; text-align: center; line-height: 36rpx; color: #fff; font-weight: 900; }
.check-box.checked { background: #fb7185; border-color: #fb7185; }
.check-text { flex: 1; font-size: 25rpx; line-height: 1.45; color: var(--theme-text, #111827); }
.ghost-btn { margin-top: 18rpx; border-radius: 20rpx; font-size: 25rpx; }
.timeline-item { display: flex; gap: 18rpx; padding: 16rpx; border-radius: 18rpx; background: #f8fafc; }
.timeline-age { flex-shrink: 0; min-width: 110rpx; color: #e11d48; font-weight: 900; font-size: 24rpx; }
.timeline-text, .redflag-item { flex: 1; color: var(--theme-text-secondary, #64748b); font-size: 24rpx; line-height: 1.5; }
.redflag-card { background: #fff7f7; }
.disclaimer-card { background: #fffbeb; }
.disclaimer-title { display: block; color: #92400e; font-size: 28rpx; font-weight: 900; margin-bottom: 10rpx; }
.disclaimer-text { display: block; color: #92400e; font-size: 23rpx; line-height: 1.6; }
@media (max-width: 380px) {
  .stage-grid, .habit-grid, .result-grid, .form-grid { grid-template-columns: 1fr; }
}
</style>
