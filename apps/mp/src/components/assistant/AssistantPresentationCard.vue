<template>
  <view class="presentation-card">
    <view class="presentation-head">
      <text class="presentation-title">{{ presentation.title || '内容草稿' }}</text>
      <text class="presentation-state">待检查</text>
    </view>

    <view class="field-list">
      <view v-for="field in presentation.fields" :key="field.key" class="field-row">
        <view class="field-meta">
          <text class="field-label">{{ field.label }}</text>
          <text class="field-source" :class="`source-${field.source}`">{{ sourceText(field.source, field.key) }}</text>
        </view>
        <text class="field-value" :class="{ missing: field.source === 'missing' }">{{ field.display_value }}</text>
        <text v-if="field.hint" class="field-hint">{{ field.hint }}</text>
        <view v-if="displayOptions(field).length || customPrompt(field)" class="field-options">
          <button
            v-for="option in displayOptions(field)"
            :key="String(option.value)"
            class="field-option"
            :class="{ active: isOptionActive(field, option.value) }"
            @tap="stageOption(field.key, option.label, option.value)"
          >
            {{ option.label }}
          </button>
          <button
            v-if="customPrompt(field)"
            class="field-option custom"
            @tap="$emit('custom', customPrompt(field))"
          >
            自己填写
          </button>
        </view>
      </view>
    </view>

    <button v-if="hasPendingSelections" class="apply-selection-button" @tap="applySelections">
      应用选择
    </button>

    <view v-if="visibleSuggestions.length" class="suggestion-row">
      <button
        v-for="suggestion in visibleSuggestions"
        :key="suggestion"
        class="suggestion-button"
        @tap="$emit('suggest', suggestion)"
      >
        {{ suggestion }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'

import type { AssistantPresentation, AssistantPresentationField } from '../../types/api'

const props = defineProps<{ presentation: AssistantPresentation }>()
const emit = defineEmits<{ suggest: [string]; custom: [string] }>()
const pendingSelections = reactive<Record<string, { label: string; value: unknown }>>({})
const hasPendingSelections = computed(() => Object.keys(pendingSelections).length > 0)

const visibleSuggestions = computed(() =>
  (props.presentation.suggestions || []).filter((item) => !['可以议价', '不议价'].includes(item)),
)

function displayOptions(field: AssistantPresentationField) {
  return (field.options || []).slice(0, 2)
}

function customPrompt(field: AssistantPresentationField) {
  if (field.custom_prompt) return field.custom_prompt
  if (field.key === 'category') return '分类改成'
  if (field.key === 'condition') return '成色：'
  if (field.key === 'post_type' && field.source === 'missing') return '交易类型是'
  return ''
}

function sourceText(source: string, fieldKey: string) {
  if (source === 'user') return '用户提供'
  if (source === 'context') return '页面信息'
  if (source === 'ai') return fieldKey === 'category' ? 'AI 判断' : 'AI 润色'
  return '未说明'
}

function optionMessage(fieldKey: string, label: string) {
  if (fieldKey === 'category') return `分类改成${label}`
  if (fieldKey === 'is_negotiable') return label === '可以' ? '可以议价' : '不议价'
  if (fieldKey === 'recipient_names') return `收件人添加：${label}`
  if (fieldKey === 'post_type') return `交易类型是${label}`
  if (fieldKey === 'condition') return `成色：${label}`
  return label
}

function stageOption(fieldKey: string, label: string, value: unknown) {
  pendingSelections[fieldKey] = { label, value }
}

function applySelections() {
  const messages = props.presentation.fields
    .filter((field) => pendingSelections[field.key])
    .map((field) => optionMessage(field.key, pendingSelections[field.key].label))
  if (!messages.length) return
  Object.keys(pendingSelections).forEach((key) => delete pendingSelections[key])
  emit('suggest', messages.join('；'))
}

function isOptionActive(field: AssistantPresentationField, optionValue: unknown) {
  const value = pendingSelections[field.key]?.value ?? field.value
  return Array.isArray(value) ? value.includes(optionValue) : value === optionValue
}
</script>

<style scoped lang="scss">
.presentation-card {
  width: 100%;
  padding: 22rpx;
  box-sizing: border-box;
  border: 1rpx solid rgba(16, 33, 51, 0.1);
  border-radius: 16rpx;
  background: #fff;
}

.presentation-head,
.field-meta,
.suggestion-row {
  display: flex;
  align-items: center;
}

.presentation-head {
  justify-content: space-between;
  gap: 16rpx;
  padding-bottom: 16rpx;
  border-bottom: 1rpx solid rgba(16, 33, 51, 0.08);
}

.presentation-title {
  min-width: 0;
  font-size: 28rpx;
  font-weight: 700;
  color: #102133;
}

.presentation-state,
.field-source {
  flex-shrink: 0;
  padding: 4rpx 10rpx;
  border-radius: 8rpx;
  font-size: 19rpx;
  color: #6b7280;
  background: #f2f4f6;
}

.field-list {
  display: flex;
  flex-direction: column;
}

.field-row {
  padding: 16rpx 0;
  border-bottom: 1rpx solid rgba(16, 33, 51, 0.06);
}

.field-row:last-child {
  border-bottom: 0;
}

.field-meta {
  justify-content: space-between;
  gap: 12rpx;
  margin-bottom: 8rpx;
}

.field-label {
  font-size: 22rpx;
  font-weight: 600;
  color: #52606d;
}

.source-user,
.source-context {
  color: #17745b;
  background: #e9f6f1;
}

.source-ai {
  color: #b84d38;
  background: #fff0eb;
}

.source-missing {
  color: #7a5b20;
  background: #fff6dc;
}

.field-value {
  display: block;
  max-width: 100%;
  overflow-wrap: anywhere;
  white-space: pre-wrap;
  font-size: 25rpx;
  line-height: 1.6;
  color: #102133;
}

.field-value.missing {
  color: #7a5b20;
}

.field-hint {
  display: block;
  margin-top: 6rpx;
  color: #6b7280;
  font-size: 21rpx;
  line-height: 1.5;
}

.field-options {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 12rpx;
}

.field-option {
  min-height: 52rpx;
  margin: 0;
  padding: 0 16rpx;
  border: 1rpx solid rgba(16, 33, 51, 0.14);
  border-radius: 8rpx;
  background: #fff;
  color: #52606d;
  font-size: 21rpx;
  line-height: 52rpx;
}

.field-option.active {
  border-color: #17745b;
  color: #17745b;
  background: #e9f6f1;
}

.field-option.custom {
  border-style: dashed;
  color: #6b7280;
  background: #f7f8f9;
}

.field-option::after {
  border: 0;
}

.suggestion-row {
  flex-wrap: wrap;
  gap: 12rpx;
  padding-top: 16rpx;
}

.suggestion-button {
  min-height: 56rpx;
  margin: 0;
  padding: 0 20rpx;
  border: 1rpx solid rgba(241, 107, 79, 0.32);
  border-radius: 28rpx;
  background: #fff7f4;
  color: #c5523d;
  font-size: 22rpx;
  line-height: 56rpx;
}

.suggestion-button::after {
  border: 0;
}

.apply-selection-button {
  width: 100%;
  min-height: 64rpx;
  margin: 14rpx 0 0;
  border-radius: 8rpx;
  background: #17745b;
  color: #fff;
  font-size: 24rpx;
  line-height: 64rpx;
}

.apply-selection-button::after {
  border: 0;
}
</style>
