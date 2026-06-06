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
    <text class="action-desc">{{ previewText }}</text>
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
          <button v-if="getRecommendationText(item, 'type') === 'dating'" class="action-button ghost compact" :disabled="disabled" @tap="$emit('recommend', action, item, 'interested')">
            感兴趣
          </button>
          <button v-if="getRecommendationText(item, 'type') === 'dating'" class="action-button ghost compact" :disabled="disabled" @tap="$emit('recommend', action, item, 'skip')">
            跳过
          </button>
          <button v-if="getRecommendationText(item, 'type') === 'trade'" class="action-button ghost compact" :disabled="disabled" @tap="$emit('recommend', action, item, 'favorite')">
            收藏
          </button>
        </view>
      </view>
    </view>

    <view v-else class="action-buttons">
      <button class="action-button primary" :disabled="disabled" @tap="$emit('execute', action)">
        填充并发布
      </button>
      <button class="action-button ghost" :disabled="disabled" @tap="$emit('fill', action)">
        仅填充
      </button>
      <button class="action-button ghost" :disabled="busy" @tap="$emit('generate', action)">
        仅生成
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
  execute: [AssistantActionProposal]
  fill: [AssistantActionProposal]
  generate: [AssistantActionProposal]
  recommend: [AssistantActionProposal, Record<string, unknown>, 'open' | 'contact' | 'fill' | 'interested' | 'skip' | 'favorite']
}>()

const disabled = computed(() => props.action.status !== 'pending' || Boolean(props.busy))
const statusText = computed(() => (props.action.status === 'pending' ? '待确认' : '已处理'))

const previewText = computed(() => {
  const preview = props.action.preview || {}
  return String(preview.body || preview.title || preview.action || 'AI 已准备好可执行内容，请确认后继续。')
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
.action-card {
  padding: 22rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.94);
  border: 1rpx solid rgba(241, 107, 79, 0.18);
  box-shadow: 0 14rpx 34rpx rgba(16, 33, 51, 0.06);
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
  font-weight: 800;
  color: #f16b4f;
}

.action-title {
  font-size: 30rpx;
  font-weight: 800;
  color: #102133;
}

.action-status {
  flex-shrink: 0;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(241, 107, 79, 0.1);
  color: #f16b4f;
  font-size: 20rpx;
  font-weight: 700;
}

.action-desc {
  font-size: 25rpx;
  line-height: 1.6;
  color: #44515f;
  white-space: pre-wrap;
}

.action-buttons,
.recommendation-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.action-button {
  min-height: 62rpx;
  padding: 0 20rpx;
  margin: 0;
  border-radius: 999rpx;
  border: 1rpx solid rgba(16, 33, 51, 0.12);
  font-size: 23rpx;
  font-weight: 800;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-button.primary {
  background: #f16b4f;
  color: #fff;
  border-color: #f16b4f;
}

.action-button.ghost {
  background: rgba(255, 255, 255, 0.86);
  color: #102133;
}

.action-button.compact {
  min-height: 54rpx;
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
  border-radius: 22rpx;
  background: rgba(255, 250, 245, 0.92);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
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
  font-weight: 800;
  color: #102133;
}

.recommendation-subtitle,
.recommendation-reason {
  font-size: 23rpx;
  line-height: 1.5;
  color: #68727f;
}

.recommendation-score {
  width: 76rpx;
  height: 76rpx;
  border-radius: 24rpx;
  background: rgba(241, 107, 79, 0.12);
  color: #f16b4f;
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
