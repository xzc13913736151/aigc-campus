<template>
  <view id="composer" class="card">
    <text class="section-title">{{ titleText }}</text>
    <view style="height: 8rpx" />
    <text class="section-desc">适合发布项目组队、比赛招募、学习搭子或活动合作。写得越清楚，越容易遇到合适的人。</text>
    <view style="height: 24rpx" />

    <view v-if="!hasToken" class="empty">
      <text class="section-desc">发布组队前需要先完成微信登录。</text>
      <view style="height: 24rpx" />
      <button class="btn btn-primary" @tap="$emit('login')">去登录</button>
    </view>

    <view v-else-if="!profileComplete" class="empty">
      <text class="section-desc">请先补全个人资料，方便别人判断你是谁、适合做什么，以及怎么联系你。</text>
      <view style="height: 24rpx" />
      <button class="btn btn-primary" @tap="$emit('profile')">完善资料</button>
    </view>

    <view v-else class="form">
      <view class="field">
        <text class="label">招募标题</text>
        <input class="input" type="text" placeholder="例如：找 2 位同学一起做 AI 校园工具项目" :value="title" @input="setTitle" />
      </view>
      <view class="field">
        <text class="label">一句话概述</text>
        <input class="input" type="text" placeholder="说明项目方向、节奏，以及你最想找什么样的人" :value="summary" @input="setSummary" />
      </view>
      <view class="field">
        <text class="label">详细说明</text>
        <textarea class="textarea" placeholder="写清背景、目标、分工、时间安排和合作预期" :value="details" @input="setDetails" />
      </view>
      <view class="field">
        <text class="label">目标人数</text>
        <input class="input" type="number" placeholder="2 - 20" :value="targetSize" @input="setTargetSize" />
      </view>
      <view class="field">
        <text class="label">项目标签</text>
        <input class="input" type="text" placeholder="AI, 产品, 比赛, 校园活动" :value="tagsText" @input="setTagsText" />
        <text class="helper">多个标签请用英文逗号分隔。</text>
      </view>
      <view class="field">
        <text class="label">需要的技能</text>
        <input class="input" type="text" placeholder="前端, 后端, 设计, 文案" :value="skillsText" @input="setSkillsText" />
        <text class="helper">多个技能请用英文逗号分隔。</text>
      </view>

      <text v-if="errorMessage" class="error">{{ errorMessage }}</text>

      <view class="composer-actions">
        <view class="composer-button primary-action" :class="{ disabled: submitting }" @tap="handleSubmit">
          <text class="composer-button-text primary-text">{{ submitText }}</text>
        </view>
        <view v-if="editingPost" class="composer-button secondary-action" @tap="cancelEdit">
          <text class="composer-button-text secondary-text">取消编辑</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import type { TeamPost } from '../../types/api'
import { createTeammatePost, updateTeammatePost } from '../../services/teammates'
import { showToast } from '../../utils/ui'

const props = defineProps<{
  hasToken: boolean
  profileComplete: boolean
  editingPost: TeamPost | null
  assistantDraft?: Record<string, unknown> | null
}>()

const emit = defineEmits<{
  (event: 'login'): void
  (event: 'profile'): void
  (event: 'saved'): void
  (event: 'cancel'): void
}>()

const submitting = ref(false)
const errorMessage = ref('')
const title = ref('')
const summary = ref('')
const details = ref('')
const targetSize = ref('3')
const tagsText = ref('')
const skillsText = ref('')

const titleText = computed(() => (props.editingPost ? '编辑组队招募' : '发起一条组队招募'))
const submitText = computed(() => {
  if (submitting.value) {
    return props.editingPost ? '保存中...' : '发布中...'
  }
  return props.editingPost ? '保存修改' : '发布组队'
})

watch(
  () => props.editingPost,
  (post) => {
    if (!post) {
      resetForm()
      return
    }
    title.value = post.title
    summary.value = post.summary
    details.value = post.details
    targetSize.value = String(post.target_size)
    tagsText.value = post.tags.join(', ')
    skillsText.value = post.required_skills.join(', ')
    errorMessage.value = ''
  },
  { immediate: true },
)

watch(
  () => props.assistantDraft,
  (draft) => {
    if (!draft || props.editingPost) {
      return
    }
    title.value = typeof draft.title === 'string' ? draft.title : title.value
    summary.value = typeof draft.summary === 'string' ? draft.summary : summary.value
    details.value = typeof draft.details === 'string' ? draft.details : details.value
    targetSize.value = draft.target_size === undefined || draft.target_size === null ? targetSize.value : String(draft.target_size)
    if (Array.isArray(draft.tags)) {
      tagsText.value = draft.tags.map(String).join(', ')
    } else if (typeof draft.tags === 'string') {
      tagsText.value = draft.tags
    }
    if (Array.isArray(draft.required_skills)) {
      skillsText.value = draft.required_skills.map(String).join(', ')
    } else if (typeof draft.required_skills === 'string') {
      skillsText.value = draft.required_skills
    }
  },
  { immediate: true },
)

function setTitle(event: { detail?: { value?: string } }) {
  title.value = event.detail?.value ?? ''
}

function setSummary(event: { detail?: { value?: string } }) {
  summary.value = event.detail?.value ?? ''
}

function setDetails(event: { detail?: { value?: string } }) {
  details.value = event.detail?.value ?? ''
}

function setTargetSize(event: { detail?: { value?: string } }) {
  targetSize.value = event.detail?.value ?? ''
}

function setTagsText(event: { detail?: { value?: string } }) {
  tagsText.value = event.detail?.value ?? ''
}

function setSkillsText(event: { detail?: { value?: string } }) {
  skillsText.value = event.detail?.value ?? ''
}

function splitList(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function validateForm() {
  const parsedTargetSize = Number(targetSize.value)
  if (title.value.trim().length < 4) {
    return '标题至少需要 4 个字'
  }
  if (summary.value.trim().length < 8) {
    return '一句话概述至少需要 8 个字'
  }
  if (details.value.trim().length < 20) {
    return '详细说明至少需要 20 个字'
  }
  if (!Number.isInteger(parsedTargetSize) || parsedTargetSize < 2 || parsedTargetSize > 20) {
    return '目标人数需要在 2 到 20 之间'
  }
  return ''
}

async function handleSubmit() {
  if (submitting.value) {
    return
  }

  errorMessage.value = validateForm()
  if (errorMessage.value) {
    return
  }

  submitting.value = true
  try {
    const payload = {
      title: title.value.trim(),
      summary: summary.value.trim(),
      details: details.value.trim(),
      target_size: Number(targetSize.value),
      tags: splitList(tagsText.value),
      required_skills: splitList(skillsText.value),
    }

    if (props.editingPost) {
      await updateTeammatePost(props.editingPost.id, payload)
    } else {
      await createTeammatePost(payload)
    }

    showToast(props.editingPost ? '组队已更新' : '组队发布成功', 'success')
    resetForm()
    emit('saved')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存组队失败'
  } finally {
    submitting.value = false
  }
}

function cancelEdit() {
  resetForm()
  emit('cancel')
}

function resetForm() {
  title.value = ''
  summary.value = ''
  details.value = ''
  targetSize.value = '3'
  tagsText.value = ''
  skillsText.value = ''
  errorMessage.value = ''
}
</script>

<style scoped lang="scss">
.composer-actions {
  display: flex;
  gap: 20rpx;
  align-items: center;
}

.composer-button {
  height: 88rpx;
  min-height: 88rpx;
  padding: 0 32rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.composer-button.disabled {
  opacity: 0.65;
  pointer-events: none;
}

.composer-button-text {
  font-size: 28rpx;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
}

.primary-action {
  flex: 1;
  background: #f16b4f;
}

.secondary-action {
  flex: 0 0 190rpx;
  background: rgba(255, 255, 255, 0.88);
  border: 1rpx solid rgba(16, 33, 51, 0.12);
}

.primary-text {
  color: #fff;
}

.secondary-text {
  color: #102133;
}
</style>
