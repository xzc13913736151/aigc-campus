<template>
  <view class="action-card">
    <view class="action-head">
      <view class="action-copy">
        <text class="action-kicker">{{ recommendations.length ? 'AI 推荐结果' : 'AI 动作建议' }}</text>
        <view style="height: 8rpx" />
        <text class="action-title">{{ action.title }}</text>
      </view>
      <text class="action-status">{{ statusText }}</text>
    </view>

    <view style="height: 14rpx" />
    <view v-if="previewFields.length" class="preview-fields">
      <view v-for="field in previewFields" :key="String(field.key)" class="preview-field">
        <text class="preview-label">{{ String(field.label || '') }}</text>
        <text class="preview-value">{{ String(field.display_value || '未说明') }}</text>
      </view>
    </view>
    <text v-else class="action-desc">{{ previewText }}</text>
    <view style="height: 16rpx" />

    <view v-if="recommendations.length" class="recommendation-list">
      <view v-for="item in recommendations" :key="getRecommendationKey(item)" class="recommendation-card">
        <view class="recommendation-head">
          <view class="recommendation-copy">
            <text class="recommendation-title">{{ getRecommendationText(item, 'title') }}</text>
            <text class="recommendation-subtitle">{{ getRecommendationText(item, 'subtitle') }}</text>
          </view>
          <view class="recommendation-score">
            <text>{{ getRecommendationScore(item) }}</text>
            <text class="recommendation-score-label">{{ getRecommendationText(item, 'score_label') }}</text>
          </view>
        </view>
        <text class="recommendation-reason">{{ getRecommendationText(item, 'reason') }}</text>
        <view class="recommendation-actions">
          <button class="action-button primary compact" :disabled="disabled" @tap="$emit('recommend', action, item, 'open')">
            查看
          </button>
          <button v-if="getRecommendationText(item, 'contact_page')" class="action-button ghost compact" :disabled="disabled" @tap="$emit('recommend', action, item, 'contact')">
            {{ contactButtonText(item) }}
          </button>
          <button v-if="hasDraft(item)" class="action-button ghost compact" :disabled="disabled" @tap="$emit('recommend', action, item, 'fill')">
            {{ fillButtonText(item) }}
          </button>
          <button v-if="getRecommendationText(item, 'type') === 'trade'" class="action-button ghost compact" :disabled="disabled" @tap="$emit('recommend', action, item, 'favorite')">
            收藏
          </button>
        </view>
      </view>
    </view>

    <view v-else-if="isMessageAction" class="action-buttons">
      <button class="action-button primary" :disabled="disabled" @tap="$emit('execute', action)">
        确认发送
      </button>
      <button class="action-button ghost" :disabled="disabled" @tap="$emit('revise', action)">
        继续修改
      </button>
    </view>

    <view v-else class="action-buttons">
      <button class="action-button primary" :disabled="disabled" @tap="$emit('fill', action)">
        填入表单
      </button>
      <button class="action-button ghost" :disabled="disabled" @tap="$emit('revise', action)">
        继续修改
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { AssistantActionProposal } from '../../types/api'

const props = defineProps<{
  action: AssistantActionProposal
  busy?: boolean
}>()

defineEmits<{
  fill: [AssistantActionProposal]
  execute: [AssistantActionProposal]
  revise: [AssistantActionProposal]
  recommend: [AssistantActionProposal, Record<string, unknown>, 'open' | 'contact' | 'fill' | 'favorite']
}>()

const disabled = computed(() => props.action.status !== 'pending' || Boolean(props.busy))
const isMessageAction = computed(() => ['chat_message_send', 'context_chat_message_send', 'chat_message_batch_send'].includes(props.action.kind))
const statusText = computed(() => {
  const labels: Record<string, string> = {
    pending: '待确认',
    executed: '已执行',
    dismissed: '已取消',
    expired: '已过期',
  }
  return labels[props.action.status] || '状态已更新'
})

const previewText = computed(() => {
  const preview = props.action.preview || {}
  return String(preview.body || preview.title || preview.action || 'AI 已准备好可执行内容，请确认后继续。')
})

const previewFields = computed<Record<string, unknown>[]>(() => {
  const fields = props.action.preview?.fields
  return Array.isArray(fields) ? fields.filter((field): field is Record<string, unknown> => Boolean(field && typeof field === 'object')) : []
})

const recommendations = computed<Record<string, unknown>[]>(() => {
  const value = props.action.preview?.recommendations
  return Array.isArray(value) ? value.filter((item): item is Record<string, unknown> => Boolean(item && typeof item === 'object')) : []
})

function getRecommendationText(item: Record<string, unknown>, key: string) {
  return String(item[key] ?? '')
}

function getRecommendationScore(item: Record<string, unknown>) {
  const score = Number(item.score ?? 0)
  return Number.isFinite(score) ? `${Math.round(score)}` : '0'
}

function getRecommendationKey(item: Record<string, unknown>) {
  return String(item.post_id || item.target_user_id || item.title || Math.random())
}

function hasDraft(item: Record<string, unknown>) {
  return Boolean(item.draft && typeof item.draft === 'object')
}

function contactButtonText(item: Record<string, unknown>) {
  const type = getRecommendationText(item, 'type')
  if (type === 'team') return '联系发起人'
  if (type === 'trade') return '联系卖家'
  return '联系TA'
}

function fillButtonText(item: Record<string, unknown>) {
  const type = getRecommendationText(item, 'type')
  if (type === 'team') return '填充申请'
  if (type === 'trade') return '填充询问'
  return '填充开场白'
}
</script>

<style scoped lang="scss">
@use '../../styles/tokens' as t;

.action-card {
  padding: 24rpx;
  border-radius: t.$radius-md;
  background: t.$color-card;
  border: 1rpx solid t.$color-line;
  border-left: 6rpx solid t.$color-ai;
}

.action-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16rpx;
}

.action-copy {
  min-width: 0;
}

.action-kicker {
  font-size: 20rpx;
  font-weight: 650;
  color: t.$color-ai;
}

.action-title {
  font-size: 30rpx;
  font-weight: 650;
  color: t.$color-ink;
}

.action-status {
  flex-shrink: 0;
  padding: 8rpx 14rpx;
  border-radius: t.$radius-sm;
  background: t.$color-brand-soft;
  color: t.$color-brand-deep;
  font-size: 20rpx;
  font-weight: 700;
}

.action-desc {
  font-size: 25rpx;
  line-height: 1.6;
  color: t.$color-ink-secondary;
  white-space: pre-wrap;
}

.preview-fields {
  display: flex;
  flex-direction: column;
}

.preview-field {
  display: grid;
  grid-template-columns: 128rpx minmax(0, 1fr);
  gap: 14rpx;
  padding: 13rpx 0;
  border-bottom: 1rpx solid rgba(16, 33, 51, 0.07);
}

.preview-field:last-child {
  border-bottom: 0;
}

.preview-label {
  font-size: 22rpx;
  color: #6b7280;
}

.preview-value {
  min-width: 0;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
  font-size: 24rpx;
  line-height: 1.55;
  color: #102133;
}

.action-buttons,
.recommendation-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.action-button {
  min-height: 72rpx;
  padding: 0 20rpx;
  margin: 0;
  border-radius: t.$radius-sm;
  border: 1rpx solid t.$color-line;
  font-size: 23rpx;
  font-weight: 620;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-button.primary {
  background: t.$color-brand;
  color: t.$color-inverse;
  border-color: t.$color-brand;
}

.action-button.ghost {
  background: t.$color-surface;
  color: t.$color-ink;
}

.action-button.compact {
  min-height: 68rpx;
  padding: 0 18rpx;
  font-size: 22rpx;
}

.action-button::after {
  border: 0;
}

.recommendation-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.recommendation-card {
  padding: 18rpx;
  border-radius: t.$radius-sm;
  background: t.$color-surface;
  border: 1rpx solid t.$color-line;
}

.recommendation-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14rpx;
}

.recommendation-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.recommendation-title {
  font-size: 27rpx;
  font-weight: 650;
  color: t.$color-ink;
}

.recommendation-subtitle,
.recommendation-reason {
  font-size: 23rpx;
  line-height: 1.5;
  color: t.$color-ink-secondary;
}

.recommendation-score {
  width: 76rpx;
  height: 76rpx;
  border-radius: t.$radius-sm;
  background: t.$color-brand-soft;
  color: t.$color-brand-deep;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 27rpx;
  font-weight: 900;
  flex-shrink: 0;
}

.recommendation-score-label {
  margin-top: 2rpx;
  font-size: 17rpx;
  font-weight: 700;
}

.recommendation-reason {
  display: block;
  margin-top: 12rpx;
}

.recommendation-actions {
  margin-top: 14rpx;
}
</style>
