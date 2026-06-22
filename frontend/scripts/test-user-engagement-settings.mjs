import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'

const settingsPath = path.resolve('src/pages/settings/index.vue')
const apiPath = path.resolve('src/api/index.ts')
const settings = fs.readFileSync(settingsPath, 'utf8')
const api = fs.readFileSync(apiPath, 'utf8')
const template = settings.match(/<template>[\s\S]*<\/template>/)?.[0] || ''

assert.match(api, /export interface FeedbackResult/, 'API should expose feedback result type')
assert.match(api, /export interface ReminderSubscription/, 'API should expose reminder subscription type')
assert.match(api, /export const submitFeedback\s*=\s*\(/, 'API should submit feedback')
assert.match(api, /export const getFeedbackList\s*=\s*\(/, 'API should fetch feedback history')
assert.match(api, /export const getReminderSubscriptions\s*=\s*\(/, 'API should fetch reminder subscriptions')
assert.match(api, /export const saveReminderSubscription\s*=\s*\(/, 'API should save reminder subscriptions')
assert.match(api, /export const disableReminderSubscription\s*=\s*\(/, 'API should disable reminder subscriptions')

assert.match(settings, /TOOLBOX_USER_KEY\s*=\s*'toolbox_user_key'/, 'settings should reuse the same lightweight anonymous user key')
assert.match(settings, /const\s+feedbackForm\s*=\s*reactive/, 'settings should keep feedback form state')
assert.match(settings, /const\s+reminderOptions\s*=\s*\[/, 'settings should define reminder presets')
assert.match(settings, /submitFeedback\(/, 'settings should submit feedback through API')
assert.match(settings, /getFeedbackList\(/, 'settings should load feedback history')
assert.match(settings, /getReminderSubscriptions\(/, 'settings should load reminder subscriptions')
assert.match(settings, /saveReminderSubscription\(/, 'settings should save reminder subscriptions')
assert.match(settings, /disableReminderSubscription\(/, 'settings should disable reminder subscriptions')
assert.match(settings, /onMounted\(\(\)\s*=>\s*\{[\s\S]*loadEngagementData\(\)/, 'settings should load feedback and reminder state on open')

assert.match(template, /反馈建议[\s\S]*feedback-form/, 'settings should render a feedback form')
assert.match(template, /textarea[\s\S]*v-model="feedbackForm\.content"/, 'feedback form should include textarea content input')
assert.match(template, /picker[\s\S]*feedbackCategoryLabels/, 'feedback form should include feedback category picker')
assert.match(template, /@click="submitFeedbackForm"/, 'feedback form should have a submit button')
assert.match(template, /订阅提醒[\s\S]*reminder-card/, 'settings should render reminder subscription card')
assert.match(template, /v-for="option in reminderOptions"/, 'settings should render reminder presets')
assert.match(template, /switch[\s\S]*@change="toggleReminder\(option, \$event\)"/, 'reminder presets should use switch toggles')
assert.match(template, /picker[\s\S]*mode="time"[\s\S]*@change="changeReminderTime\(option, \$event\)"/, 'reminders should support time picker')
assert.match(template, /feedback-history[\s\S]*v-for="item in feedbackList"/, 'settings should show feedback history')

console.log('settings page supports feedback system and reminder subscriptions')
