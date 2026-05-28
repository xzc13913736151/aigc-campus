<template>
  <view class="container">
    <view class="section hero">
      <text class="eyebrow">CampusClaw 个人资料</text>
      <view style="height: 18rpx" />
      <text class="title">先把你自己介绍清楚，后面的论坛、组队、匹配和聊天体验才会完整。</text>
      <view style="height: 18rpx" />
      <text class="subtitle">
        这里负责首次登录后的资料补全，也负责后续的个人资料编辑。完成必填项后，系统会自动回到你原本想去的页面。
      </text>
    </view>

    <view v-if="!hasToken" class="card empty">
      <text class="section-title">请先登录</text>
      <view style="height: 12rpx" />
      <text class="section-desc">需要先完成微信登录，才能读取和保存你的个人资料。</text>
      <view style="height: 24rpx" />
      <button class="btn btn-primary" @tap="goLogin">去登录</button>
    </view>

    <view v-else class="section">
      <view class="grid stats-grid section">
        <view class="card stat-card">
          <text class="stat-value">{{ completedRequiredCount }}/{{ requiredFields.length }}</text>
          <view style="height: 8rpx" />
          <text class="section-desc">必填进度</text>
        </view>
        <view class="card stat-card">
          <text class="stat-value">{{ progressPercent }}%</text>
          <view style="height: 8rpx" />
          <text class="section-desc">资料完整度</text>
        </view>
        <view class="card stat-card">
          <text class="stat-value">{{ form.interestsText ? interestCount : 0 }}</text>
          <view style="height: 8rpx" />
          <text class="section-desc">兴趣标签</text>
        </view>
      </view>

      <view class="card section">
        <view class="profile-head">
          <view class="avatar-wrap">
            <image v-if="avatarPreview" class="avatar" :src="avatarPreview" mode="aspectFill" />
            <view v-else class="avatar avatar-placeholder">
              <text>{{ nicknameInitial }}</text>
            </view>
          </view>
          <view class="profile-copy">
            <text class="section-title profile-name">{{ form.nickname || '还没设置昵称' }}</text>
            <view style="height: 8rpx" />
            <text class="section-desc">{{ form.headline || '写一句话介绍，让别人更快认识你。' }}</text>
          </view>
        </view>

        <view style="height: 20rpx" />
        <view class="action-row">
          <button class="btn btn-secondary" open-type="chooseAvatar" @chooseavatar="handleChooseAvatar">使用微信头像</button>
          <button class="btn btn-ghost" :disabled="uploadingAvatar" @tap="chooseAvatarFromAlbum">
            {{ uploadingAvatar ? '上传中...' : '从相册选择' }}
          </button>
        </view>
      </view>

      <view class="card section">
        <view class="progress-head">
          <text class="section-title">首次登录资料要求</text>
          <text class="progress-value">{{ completedRequiredCount }}/{{ requiredFields.length }}</text>
        </view>
        <view style="height: 12rpx" />
        <view class="progress-bar">
          <view class="progress-bar-fill" :style="{ width: `${progressPercent}%` }" />
        </view>
        <view style="height: 12rpx" />
        <text class="section-desc">当前把“一句话介绍、专业、年级”作为首次登录的必填项，补齐后才算完成新手引导。</text>
        <view v-if="missingFieldLabels.length" style="height: 14rpx" />
        <view v-if="missingFieldLabels.length" class="hint-card">
          <text class="hint-title">还缺这些必填项</text>
          <text class="helper">{{ missingFieldLabels.join('、') }}</text>
        </view>
      </view>

      <view class="card">
        <text class="section-title">编辑个人资料</text>
        <view style="height: 10rpx" />
        <text class="section-desc">这些信息会影响你在论坛、组队、匹配和聊天里的展示方式。</text>
        <view style="height: 24rpx" />

        <view class="form">
          <view class="field">
            <view class="label-row">
              <text class="label">昵称</text>
              <text class="required">建议填写</text>
            </view>
            <input
              v-model="form.nickname"
              class="input"
              type="nickname"
              maxlength="60"
              placeholder="输入你希望展示的昵称"
            />
            <text class="helper">论坛发帖、评论、组队发布时会优先显示昵称。</text>
          </view>

          <view class="field">
            <view class="label-row">
              <text class="label">一句话介绍</text>
              <text class="required">必填</text>
            </view>
            <input
              v-model="form.headline"
              class="input"
              type="text"
              maxlength="120"
              placeholder="例如：AI 产品方向，想找同学一起做校园项目"
            />
          </view>

          <view class="field">
            <text class="label">性别</text>
            <picker :range="genderOptions" :value="genderIndex" @change="(e) => genderIndex = e.detail.value">
              <view class="input">{{ genderOptions[genderIndex] }}</view>
            </picker>
          </view>

          <view class="field">
            <view class="label-row">
              <text class="label">专业</text>
              <text class="required">必填</text>
            </view>
            <input v-model="form.major" class="input" type="text" maxlength="120" placeholder="例如：计算机科学与技术" />
          </view>

          <view class="field">
            <view class="label-row">
              <text class="label">年级</text>
              <text class="required">必填</text>
            </view>
            <input v-model="form.grade" class="input" type="text" maxlength="40" placeholder="例如：2023 级" />
          </view>

          <view class="field">
            <text class="label">兴趣标签</text>
            <input v-model="form.interestsText" class="input" type="text" placeholder="AI, 阅读, 跑步, 摄影" />
            <text class="helper">多个标签请用英文逗号分隔。</text>
          </view>

          <view class="field">
            <text class="label">个人简介</text>
            <textarea
              v-model="form.bio"
              class="textarea"
              maxlength="500"
              placeholder="简单介绍你的方向、正在做的事情，以及你想认识什么样的同学。"
            />
          </view>

          <text v-if="errorMessage" class="error">{{ errorMessage }}</text>
          <button class="btn btn-primary" :disabled="loading || submitting || uploadingAvatar" @tap="handleSubmit">
            {{ submitting ? '保存中...' : primaryButtonText }}
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import type { ProfileResponse } from '../../types/api'
import { fetchMyProfile, updateMyProfile, uploadMyAvatar } from '../../services/profile'
import {
  ensureAuthenticated,
  finishProfileOnboarding,
  isAuthenticated,
  isProfileComplete,
  profileOnboarded,
  redirectToLogin,
  setProfileOnboarded,
  syncCurrentUser,
} from '../../utils/auth'
import { consumeAssistantDraft } from '../../utils/assistantDraft'
import { chooseMediaAndUpload } from '../../utils/upload'
import { showToast } from '../../utils/ui'

const hasToken = ref(isAuthenticated.value)
const loading = ref(false)
const submitting = ref(false)
const uploadingAvatar = ref(false)
const errorMessage = ref('')
const avatarPreview = ref('')

const genderOptions = ['未说明', '男', '女', '其他']
const genderValues = ['unknown', 'male', 'female', 'other']

const genderIndex = computed({
  get: () => genderValues.indexOf(form.gender) >= 0 ? genderValues.indexOf(form.gender) : 0,
  set: (val: number) => { form.gender = genderValues[val] }
})

const form = reactive({
  nickname: '',
  avatar_url: '',
  headline: '',
  bio: '',
  gender: 'unknown',
  major: '',
  grade: '',
  interestsText: '',
})

const requiredFields = [
  { key: 'headline', label: '一句话介绍' },
  { key: 'major', label: '专业' },
  { key: 'grade', label: '年级' },
] as const

const completedRequiredCount = computed(() =>
  requiredFields.filter((field) => String(form[field.key]).trim()).length,
)

const progressPercent = computed(() => Math.round((completedRequiredCount.value / requiredFields.length) * 100))
const missingFieldLabels = computed(() =>
  requiredFields.filter((field) => !String(form[field.key]).trim()).map((field) => field.label),
)
const primaryButtonText = computed(() => (profileOnboarded.value ? '保存资料' : '完成资料补全并继续'))
const nicknameInitial = computed(() => form.nickname.trim().slice(0, 1) || '我')
const interestCount = computed(() =>
  form.interestsText
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean).length,
)

function validateProfileForm() {
  if (!form.headline.trim()) {
    return '请先填写一句话介绍'
  }
  if (!form.major.trim()) {
    return '请先填写专业'
  }
  if (!form.grade.trim()) {
    return '请先填写年级'
  }
  return ''
}

function applyProfile(profile: ProfileResponse) {
  form.nickname = profile.nickname ?? profile.user?.nickname ?? ''
  form.avatar_url = profile.avatar_url ?? ''
  form.headline = profile.headline ?? ''
  form.bio = profile.bio ?? ''
  form.gender = profile.gender ?? 'unknown'
  form.major = profile.major ?? ''
  form.grade = profile.grade ?? ''
  form.interestsText = (profile.interests ?? []).join(', ')
  avatarPreview.value = profile.avatar_url ?? ''
  syncCurrentUser(profile.user ?? null)
  setProfileOnboarded(isProfileComplete(profile))
}

async function loadProfile() {
  loading.value = true
  errorMessage.value = ''
  try {
    const profile = await fetchMyProfile()
    applyProfile(profile)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载资料失败'
  } finally {
    loading.value = false
  }
}

async function syncAvatar(filePath: string) {
  uploadingAvatar.value = true
  errorMessage.value = ''
  try {
    avatarPreview.value = filePath
    const profile = await uploadMyAvatar(filePath)
    applyProfile(profile)
    showToast('头像已更新', 'success')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '头像上传失败'
  } finally {
    uploadingAvatar.value = false
  }
}

async function handleChooseAvatar(event: { detail?: { avatarUrl?: string } }) {
  const filePath = event.detail?.avatarUrl ?? ''
  if (!filePath) {
    return
  }
  await syncAvatar(filePath)
}

async function chooseAvatarFromAlbum() {
  uploadingAvatar.value = true
  errorMessage.value = ''
  try {
    const profile = await chooseMediaAndUpload<ProfileResponse>('profile/me/avatar/')
    applyProfile(profile)
    showToast('头像已更新', 'success')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '头像上传失败'
  } finally {
    uploadingAvatar.value = false
  }
}

async function handleSubmit() {
  errorMessage.value = ''
  const validationMessage = validateProfileForm()
  if (validationMessage) {
    errorMessage.value = validationMessage
    return
  }

  const shouldFinishOnboarding = !profileOnboarded.value

  submitting.value = true
  try {
    const updatedProfile = await updateMyProfile({
      nickname: form.nickname.trim().slice(0, 60),
      avatar_url: form.avatar_url,
      headline: form.headline.trim().slice(0, 120),
      bio: form.bio.trim().slice(0, 500),
      gender: form.gender.trim() || 'unknown',
      major: form.major.trim().slice(0, 120),
      grade: form.grade.trim().slice(0, 40),
      interests: form.interestsText.split(',').map((item) => item.trim()).filter(Boolean),
    })

    applyProfile(updatedProfile)

    if (shouldFinishOnboarding && isProfileComplete(updatedProfile)) {
      showToast('资料补全成功', 'success')
      finishProfileOnboarding()
      return
    }

    showToast('资料已保存', 'success')
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '保存失败'
  } finally {
    submitting.value = false
  }
}

function goLogin() {
  redirectToLogin('/pages/profile/index')
}

onShow(async () => {
  hasToken.value = isAuthenticated.value
  if (!ensureAuthenticated('/pages/profile/index')) {
    return
  }
  await loadProfile()
  applyAssistantDraft()
})

function applyAssistantDraft() {
  const draft = consumeAssistantDraft('/pages/profile/index', ['profile_update'])
  if (!draft) {
    return
  }
  const payload = draft.fill_payload
  form.nickname = typeof payload.nickname === 'string' ? payload.nickname : form.nickname
  form.headline = typeof payload.headline === 'string' ? payload.headline : form.headline
  form.bio = typeof payload.bio === 'string' ? payload.bio : form.bio
  form.gender = typeof payload.gender === 'string' ? payload.gender : form.gender
  form.major = typeof payload.major === 'string' ? payload.major : form.major
  form.grade = typeof payload.grade === 'string' ? payload.grade : form.grade
  if (Array.isArray(payload.interests)) {
    form.interestsText = payload.interests.map(String).join(', ')
  } else if (typeof payload.interests === 'string') {
    form.interestsText = payload.interests
  }
  showToast('AI 已填入个人资料草稿', 'success')
}
</script>

<style scoped lang="scss">
.hero {
  padding-top: 12rpx;
}

.stats-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.stat-card {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 42rpx;
  font-weight: 700;
  color: #102133;
}

.profile-head {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.profile-copy {
  flex: 1;
}

.profile-name {
  margin-bottom: 0;
  font-size: 34rpx;
}

.avatar-wrap {
  flex-shrink: 0;
}

.avatar {
  width: 132rpx;
  height: 132rpx;
  border-radius: 50%;
  overflow: hidden;
  background: rgba(16, 33, 51, 0.08);
}

.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 44rpx;
  font-weight: 700;
  color: #f16b4f;
}

.action-row {
  display: flex;
  gap: 20rpx;
  flex-wrap: wrap;
}

.progress-head,
.label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.progress-value,
.required {
  font-size: 22rpx;
  font-weight: 700;
  color: #f16b4f;
}

.progress-bar {
  width: 100%;
  height: 14rpx;
  border-radius: 999rpx;
  overflow: hidden;
  background: rgba(16, 33, 51, 0.1);
}

.progress-bar-fill {
  height: 100%;
  border-radius: 999rpx;
  background: linear-gradient(90deg, #f16b4f 0%, #ff9c6a 100%);
}

.hint-card {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(241, 107, 79, 0.08);
  border: 1rpx solid rgba(241, 107, 79, 0.16);
}

.hint-title {
  font-size: 26rpx;
  font-weight: 700;
  color: #102133;
}
</style>
