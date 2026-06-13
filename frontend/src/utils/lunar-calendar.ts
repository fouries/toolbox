export interface SolarTermItem {
  name: string
  date: string
  month: number
  day: number
  index: number
  season: string
  desc: string
}

export interface CalendarDay {
  date: Date
  dateText: string
  day: number
  isCurrentMonth: boolean
  isToday: boolean
  weekText: string
  lunarText: string
  lunarMonthText: string
  lunarDayText: string
  ganzhiYear: string
  ganzhiMonth: string
  ganzhiDay: string
  zodiac: string
  solarTerm: string
  festival: string
  suit: string[]
  avoid: string[]
}

const lunarInfo = [
  0x04bd8, 0x04ae0, 0x0a570, 0x054d5, 0x0d260, 0x0d950, 0x16554, 0x056a0, 0x09ad0, 0x055d2,
  0x04ae0, 0x0a5b6, 0x0a4d0, 0x0d250, 0x1d255, 0x0b540, 0x0d6a0, 0x0ada2, 0x095b0, 0x14977,
  0x04970, 0x0a4b0, 0x0b4b5, 0x06a50, 0x06d40, 0x1ab54, 0x02b60, 0x09570, 0x052f2, 0x04970,
  0x06566, 0x0d4a0, 0x0ea50, 0x06e95, 0x05ad0, 0x02b60, 0x186e3, 0x092e0, 0x1c8d7, 0x0c950,
  0x0d4a0, 0x1d8a6, 0x0b550, 0x056a0, 0x1a5b4, 0x025d0, 0x092d0, 0x0d2b2, 0x0a950, 0x0b557,
  0x06ca0, 0x0b550, 0x15355, 0x04da0, 0x0a5d0, 0x14573, 0x052d0, 0x0a9a8, 0x0e950, 0x06aa0,
  0x0aea6, 0x0ab50, 0x04b60, 0x0aae4, 0x0a570, 0x05260, 0x0f263, 0x0d950, 0x05b57, 0x056a0,
  0x096d0, 0x04dd5, 0x04ad0, 0x0a4d0, 0x0d4d4, 0x0d250, 0x0d558, 0x0b540, 0x0b6a0, 0x195a6,
  0x095b0, 0x049b0, 0x0a974, 0x0a4b0, 0x0b27a, 0x06a50, 0x06d40, 0x0af46, 0x0ab60, 0x09570,
  0x04af5, 0x04970, 0x064b0, 0x074a3, 0x0ea50, 0x06b58, 0x055c0, 0x0ab60, 0x096d5, 0x092e0,
  0x0c960, 0x0d954, 0x0d4a0, 0x0da50, 0x07552, 0x056a0, 0x0abb7, 0x025d0, 0x092d0, 0x0cab5,
  0x0a950, 0x0b4a0, 0x0baa4, 0x0ad50, 0x055d9, 0x04ba0, 0x0a5b0, 0x15176, 0x052b0, 0x0a930,
  0x07954, 0x06aa0, 0x0ad50, 0x05b52, 0x04b60, 0x0a6e6, 0x0a4e0, 0x0d260, 0x0ea65, 0x0d530,
  0x05aa0, 0x076a3, 0x096d0, 0x04bd7, 0x04ad0, 0x0a4d0, 0x1d0b6, 0x0d250, 0x0d520, 0x0dd45,
  0x0b5a0, 0x056d0, 0x055b2, 0x049b0, 0x0a577, 0x0a4b0, 0x0aa50, 0x1b255, 0x06d20, 0x0ada0,
  0x14b63
]

const heavenlyStems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
const earthlyBranches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
const zodiacAnimals = ['鼠', '牛', '虎', '兔', '龙', '蛇', '马', '羊', '猴', '鸡', '狗', '猪']
const lunarMonths = ['正月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '冬月', '腊月']
const lunarDays = ['初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十', '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十', '廿一', '廿二', '廿三', '廿四', '廿五', '廿六', '廿七', '廿八', '廿九', '三十']
const weekTexts = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

const solarTermDefinitions = [
  { key: '01-05', name: '小寒', season: '冬', desc: '寒气渐盛，注意防寒保暖。' },
  { key: '01-20', name: '大寒', season: '冬', desc: '一年中最寒冷时段，适合养藏。' },
  { key: '02-04', name: '立春', season: '春', desc: '春气始建，万物复苏。' },
  { key: '02-19', name: '雨水', season: '春', desc: '降水渐增，草木萌动。' },
  { key: '03-05', name: '惊蛰', season: '春', desc: '春雷惊蛰，万物生发。' },
  { key: '03-20', name: '春分', season: '春', desc: '昼夜平分，春意正浓。' },
  { key: '04-04', name: '清明', season: '春', desc: '气清景明，踏青祭扫。' },
  { key: '04-20', name: '谷雨', season: '春', desc: '雨生百谷，适合播种。' },
  { key: '05-05', name: '立夏', season: '夏', desc: '夏季开始，万物繁茂。' },
  { key: '05-21', name: '小满', season: '夏', desc: '麦类籽粒渐满但未成熟。' },
  { key: '06-05', name: '芒种', season: '夏', desc: '有芒作物成熟，忙于耕种。' },
  { key: '06-21', name: '夏至', season: '夏', desc: '白昼最长，暑气渐盛。' },
  { key: '07-07', name: '小暑', season: '夏', desc: '暑热初盛，注意避暑。' },
  { key: '07-22', name: '大暑', season: '夏', desc: '一年中最热时段，防暑降温。' },
  { key: '08-07', name: '立秋', season: '秋', desc: '秋季开始，暑热未消。' },
  { key: '08-23', name: '处暑', season: '秋', desc: '暑气渐止，天气转凉。' },
  { key: '09-07', name: '白露', season: '秋', desc: '露凝而白，昼夜温差加大。' },
  { key: '09-23', name: '秋分', season: '秋', desc: '昼夜平分，秋意渐深。' },
  { key: '10-08', name: '寒露', season: '秋', desc: '露水带寒，注意添衣。' },
  { key: '10-23', name: '霜降', season: '秋', desc: '初霜将至，秋末冬来。' },
  { key: '11-07', name: '立冬', season: '冬', desc: '冬季开始，万物收藏。' },
  { key: '11-22', name: '小雪', season: '冬', desc: '气温下降，初雪渐临。' },
  { key: '12-07', name: '大雪', season: '冬', desc: '降雪可能增多，宜温补。' },
  { key: '12-21', name: '冬至', season: '冬', desc: '阴极阳生，白昼渐长。' }
]

const solarTerms = new Map<string, string>(solarTermDefinitions.map(item => [item.key, item.name]))

const solarFestivals: Record<string, string> = {
  '01-01': '元旦',
  '02-14': '情人节',
  '03-08': '妇女节',
  '05-01': '劳动节',
  '06-01': '儿童节',
  '10-01': '国庆节',
  '12-25': '圣诞节'
}

const lunarFestivals: Record<string, string> = {
  '1-1': '春节',
  '1-15': '元宵节',
  '5-5': '端午节',
  '7-7': '七夕',
  '8-15': '中秋节',
  '9-9': '重阳节',
  '12-8': '腊八节',
  '12-23': '小年'
}

const suitPool = ['祭祀', '祈福', '求嗣', '出行', '开市', '交易', '纳财', '嫁娶', '订盟', '动土', '安床', '入宅', '修造', '会友', '沐浴', '扫舍']
const avoidPool = ['破土', '安葬', '开仓', '词讼', '远行', '搬迁', '嫁娶', '开市', '动土', '修造', '探病', '纳畜', '栽种', '置产', '赴任', '签约']

function pad(num: number): string {
  return String(num).padStart(2, '0')
}

function normalizeDate(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

function leapMonth(year: number): number {
  return lunarInfo[year - 1900] & 0xf
}

function leapDays(year: number): number {
  if (leapMonth(year)) return (lunarInfo[year - 1900] & 0x10000) ? 30 : 29
  return 0
}

function monthDays(year: number, month: number): number {
  return (lunarInfo[year - 1900] & (0x10000 >> month)) ? 30 : 29
}

function yearDays(year: number): number {
  let sum = 348
  for (let bit = 0x8000; bit > 0x8; bit >>= 1) {
    if (lunarInfo[year - 1900] & bit) sum += 1
  }
  return sum + leapDays(year)
}

function ganzhi(index: number): string {
  return heavenlyStems[index % 10] + earthlyBranches[index % 12]
}

function pickDailyItems(pool: string[], seed: number, count: number): string[] {
  const items: string[] = []
  let cursor = Math.abs(seed)
  while (items.length < count) {
    const item = pool[cursor % pool.length]
    if (!items.includes(item)) items.push(item)
    cursor = Math.floor(cursor / 3) + 7
  }
  return items
}

function getLunar(date: Date) {
  const baseDate = new Date(1900, 0, 31)
  let offset = Math.floor((normalizeDate(date).getTime() - baseDate.getTime()) / 86400000)
  let lunarYear = 1900
  let daysOfYear = 0

  while (lunarYear < 2050 && offset > 0) {
    daysOfYear = yearDays(lunarYear)
    if (offset < daysOfYear) break
    offset -= daysOfYear
    lunarYear += 1
  }

  const leap = leapMonth(lunarYear)
  let isLeap = false
  let lunarMonth = 1
  let daysOfMonth = 0

  while (lunarMonth <= 12 && offset >= 0) {
    if (leap > 0 && lunarMonth === leap + 1 && !isLeap) {
      lunarMonth -= 1
      isLeap = true
      daysOfMonth = leapDays(lunarYear)
    } else {
      daysOfMonth = monthDays(lunarYear, lunarMonth)
    }

    if (offset < daysOfMonth) break
    offset -= daysOfMonth

    if (isLeap && lunarMonth === leap) {
      isLeap = false
    }
    lunarMonth += 1
  }

  const lunarDay = offset + 1
  return { lunarYear, lunarMonth, lunarDay, isLeap }
}

export function formatDate(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}


export function getSolarTermsForYear(year: number): SolarTermItem[] {
  return solarTermDefinitions.map((item, index) => {
    const [monthText, dayText] = item.key.split('-')
    return {
      name: item.name,
      date: `${year}-${item.key}`,
      month: Number(monthText),
      day: Number(dayText),
      index,
      season: item.season,
      desc: item.desc
    }
  })
}

export function getCalendarDay(date: Date, currentMonth = date.getMonth()): CalendarDay {
  const dayDate = normalizeDate(date)
  const today = normalizeDate(new Date())
  const lunar = getLunar(dayDate)
  const monthDayKey = `${pad(dayDate.getMonth() + 1)}-${pad(dayDate.getDate())}`
  const lunarKey = `${lunar.lunarMonth}-${lunar.lunarDay}`
  const solarTerm = solarTerms.get(monthDayKey) || ''
  const festival = solarFestivals[monthDayKey] || lunarFestivals[lunarKey] || ''
  const seed = dayDate.getFullYear() * 10000 + (dayDate.getMonth() + 1) * 100 + dayDate.getDate()
  const lunarMonthText = `${lunar.isLeap ? '闰' : ''}${lunarMonths[lunar.lunarMonth - 1]}`
  const lunarDayText = lunarDays[lunar.lunarDay - 1]
  const displayLunarText = festival || solarTerm || (lunar.lunarDay === 1 ? lunarMonthText : lunarDayText)

  return {
    date: dayDate,
    dateText: formatDate(dayDate),
    day: dayDate.getDate(),
    isCurrentMonth: dayDate.getMonth() === currentMonth,
    isToday: dayDate.getTime() === today.getTime(),
    weekText: weekTexts[dayDate.getDay()],
    lunarText: displayLunarText,
    lunarMonthText,
    lunarDayText,
    ganzhiYear: ganzhi(lunar.lunarYear - 4),
    ganzhiMonth: ganzhi((dayDate.getFullYear() - 1900) * 12 + dayDate.getMonth() + 12),
    ganzhiDay: ganzhi(Math.floor(dayDate.getTime() / 86400000) + 40),
    zodiac: zodiacAnimals[(lunar.lunarYear - 4) % 12],
    solarTerm,
    festival,
    suit: pickDailyItems(suitPool, seed, 5),
    avoid: pickDailyItems(avoidPool, seed + 17, 5)
  }
}

export function buildMonthDays(year: number, month: number): CalendarDay[] {
  const firstDay = new Date(year, month, 1)
  const startOffset = firstDay.getDay()
  const startDate = new Date(year, month, 1 - startOffset)
  const days: CalendarDay[] = []

  for (let i = 0; i < 42; i += 1) {
    const date = new Date(startDate)
    date.setDate(startDate.getDate() + i)
    days.push(getCalendarDay(date, month))
  }

  return days
}
