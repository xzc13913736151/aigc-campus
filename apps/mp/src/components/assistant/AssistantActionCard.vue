<template>
  <view class="action-card">
    <view class="action-head">
      <view class="action-copy">
        <text class="action-kicker">AI 动作建议</text>
        <view style="height: 8rpx" />
        <text class="action-title">{{ action.title }}</text>
      </view>
      <text class="action-status">{{ statusText }}</text>
    </view>

    <view style="height: 14rpx" />
    <text class="action-desc">{{ previewText }}</text>
    <view style="height: 16rpx" />

    <view class="action-buttons">
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
}>()

const disabled = computed(() => props.action.status !== 'pending' || Boolean(props.busy))
const statusText = computed(() => (props.action.status === 'pending' ? '待确认' : '已处理'))

const previewText = computed(() => {
  const preview = props.action.preview || {}
  return String(preview.body || preview.title || preview.action || 'AI 已准备好可执行内容，请确认后继续。')
})
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

.action-buttons {
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

.action-button::after {
  border: 0;
}
</style>
