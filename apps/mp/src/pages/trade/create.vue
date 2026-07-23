<template>
  <view class="container">
    <view class="header">
      <text class="header-title">发布交易</text>
    </view>

    <scroll-view class="form-area" scroll-y enhanced :show-scrollbar="false">
      <view class="card" :class="{ 'ai-filled': aiFilled }">
        <view v-if="aiFilled" class="ai-fill-note">
          <text>AI 已生成交易草稿</text>
          <text class="helper">价格、成色和描述都可以继续修改。</text>
        </view>
        <view class="field">
          <text class="label">类型 · 必填</text>
          <picker :range="typeOptions" :value="typeIndex" @change="handleTypeChange">
            <view class="input">{{ typeOptions[typeIndex] }}</view>
          </picker>
        </view>

        <view class="field">
          <text class="label">标题 · 必填</text>
          <input v-model="form.title" class="input" type="text" placeholder="简明描述你的商品或服务" />
          <text v-if="fieldError === 'title'" class="error">{{ errorMessage }}</text>
        </view>

        <view class="field">
          <text class="label">描述 · 必填</text>
          <textarea v-model="form.description" class="textarea" placeholder="详细说明商品状况、来源、期望价格等" />
          <text v-if="fieldError === 'description'" class="error">{{ errorMessage }}</text>
        </view>

        <view class="field">
          <text class="label">价格（元）· 选填</text>
          <input v-model="form.price" class="input" type="digit" placeholder="留空则表示价格面议" />
        </view>

        <view class="field">
          <text class="label">成色 · 选填</text>
          <input v-model="form.condition" class="input" type="text" placeholder="如：全新、9成新、7成新" />
        </view>

        <view class="field">
          <text class="label">标签 · 选填</text>
          <input v-model="form.tagsText" class="input" type="text" placeholder="多个标签用逗号分隔，如：数码,书本,衣物" />
        </view>

        <view class="toggle-field">
          <text class="label">可议价</text>
          <switch :checked="form.is_negotiable" color="#c15f3c" @change="handleNegotiableChange" />
        </view>

        <text v-if="errorMessage && !fieldError" class="error">{{ errorMessage }}</text>

        <view v-if="showPreview" class="preview-card">
          <text class="eyebrow">发布前预览</text>
          <text class="section-title">{{ form.title }}</text>
          <text class="preview-price">{{ form.price ? `¥ ${form.price}` : '价格面议' }}</text>
          <text class="section-desc">{{ form.description }}</text>
          <text class="helper">{{ form.condition || '未填写成色' }} · {{ form.is_negotiable ? '可议价' : '不议价' }}</text>
        </view>

        <button class="btn btn-primary" :disabled="submitting" @tap="showPreview ? confirmSubmit() : handleSubmit()">
          {{ submitting ? '发布中...' : showPreview ? '确认并发布' : '预览交易' }}
        </button>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import { createTradePost } from '../../services/trade'
import { consumeAssistantDraft } from '../../utils/assistantDraft'
import { ensureAuthenticated } from '../../utils/auth'
import { showToast } from '../../utils/ui'

const typeOptions = ['出售', '求购', '交换', '服务']
const typeValues = ['sell', 'buy', 'exchange', 'service']

const submitting = ref(false)
const errorMessage = ref('')
const fieldError = ref('')
const showPreview = ref(false)
const aiFilled = ref(false)

const form = reactive({
  post_type: 'sell' as const,
  title: '',
  description: '',
  price: '',
  condition: '',
  tagsText: '',
  is_negotiable: true,
})

const typeIndex = computed(() => typeValues.indexOf(form.post_type))

onShow(() => {
  if (!ensureAuthenticated('/pages/trade/create')) {
    return
  }
  applyAssistantDraft()
})

function applyAssistantDraft() {
  const draft = consumeAssistantDraft('/pages/trade/create', ['trade_post_create'])
  if (!draft) {
    return
  }
  const payload = draft.fill_payload
  if (typeof payload.post_type === 'string' && typeValues.includes(payload.post_type)) {
    form.post_type = payload.post_type as typeof form.post_type
  }
  form.title = typeof payload.title === 'string' ? payload.title : form.title
  form.description = typeof payload.description === 'string' ? payload.description : form.description
  form.price = payload.price === null || payload.price === undefined ? form.price : String(payload.price)
  form.condition = typeof payload.condition === 'string' ? payload.condition : form.condition
  if (Array.isArray(payload.tags)) {
    form.tagsText = payload.tags.map(String).join(', ')
  } else if (typeof payload.tags === 'string') {
    form.tagsText = payload.tags
  }
  showToast('AI 已填入交易草稿', 'success')
  aiFilled.value = true
  setTimeout(() => {
    aiFilled.value = false
  }, 2400)
}

function handleTypeChange(e: { detail?: { value?: string | number } }) {
  const idx = Number(e.detail?.value ?? 0)
  form.post_type = typeValues[idx] as typeof form.post_type
}

function handleNegotiableChange(e: { detail?: { value?: boolean } }) {
  form.is_negotiable = Boolean(e.detail?.value)
}

function splitList(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function handleSubmit() {
  errorMessage.value = ''
  fieldError.value = ''

  if (form.title.trim().length < 4) {
    fieldError.value = 'title'
    errorMessage.value = '标题至少需要 4 个字'
    return
  }
  if (form.description.trim().length < 10) {
    fieldError.value = 'description'
    errorMessage.value = '描述至少需要 10 个字'
    return
  }

  showPreview.value = true
}

async function confirmSubmit() {
  submitting.value = true
  try {
    const price = form.price ? parseFloat(form.price) : null
    await createTradePost({
      post_type: form.post_type,
      title: form.title.trim(),
      description: form.description.trim(),
      price,
      is_negotiable: form.is_negotiable,
      condition: form.condition.trim(),
      tags: splitList(form.tagsText),
    })
    showToast('发布成功', 'success')
    setTimeout(() => {
      uni.navigateBack()
    }, 1500)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '发布失败'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped lang="scss">
@use '../../styles/tokens' as t;

.container {
  min-height: 100vh;
  background: #f5f1e8;
}

.header {
  padding: 32rpx 24rpx 24rpx;
  background: #fffcf7;
  border-bottom: 1rpx solid rgba(16, 33, 51, 0.08);
}

.header-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #2f2a24;
}

.form-area {
  height: calc(100vh - 120rpx);
  padding: 24rpx;
}

.toggle-field {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 0;
}

.error {
  display: block;
  color: #b75347;
  font-size: 26rpx;
  margin-bottom: 16rpx;
}

.ai-fill-note,
.preview-card {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  padding: 22rpx;
  margin-bottom: 24rpx;
  border: 1rpx solid t.$color-line;
  border-radius: t.$radius-md;
  background: t.$color-surface;
}

.ai-fill-note {
  color: t.$color-ai;
}

.preview-price {
  color: t.$color-brand-deep;
  font-size: 34rpx;
  font-weight: 650;
}

.ai-filled .input,
.ai-filled .textarea {
  animation: ai-field-highlight 2.4s ease;
}

@keyframes ai-field-highlight {
  0%,
  35% {
    border-color: t.$color-brand;
    background: t.$color-brand-soft;
  }
  100% {
    border-color: t.$color-line;
    background: t.$color-input;
  }
}
</style>
