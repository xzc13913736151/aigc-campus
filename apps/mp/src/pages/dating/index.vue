<template>
  <view class="container">
    <view class="section hero">
      <text class="eyebrow">CampusClaw 恋爱匹配</text>
      <view style="height: 18rpx" />
      <text class="title">先把自己说清楚，再遇见聊得来的人。</text>
    </view>

    <view v-if="!hasToken" class="card empty">
      <text class="section-desc">请先完成微信登录，再进入恋爱匹配功能。</text>
      <view style="height: 24rpx" />
      <button class="btn btn-primary" @tap="goLogin">去登录</button>
    </view>

    <view v-else-if="!profileComplete" class="card empty">
      <text class="section-desc">请先完成基础个人资料补全，这样匹配结果才更准确，也更方便别人认识你。</text>
      <view style="height: 24rpx" />
      <button class="btn btn-primary" @tap="goProfile">完善资料</button>
    </view>

    <view v-else class="section">
      <view class="grid stats-grid section">
        <view class="card stat-card">
          <text class="stat-value">{{ candidates.length }}</text>
          <view style="height: 8rpx" />
          <text class="section-desc">候选人</text>
        </view>
        <view class="card stat-card">
          <text class="stat-value">{{ matches.length }}</text>
          <view style="height: 8rpx" />
          <text class="section-desc">已匹配</text>
        </view>
        <view class="card stat-card">
          <text class="stat-value">{{ blockedUserIds.size }}</text>
          <view style="height: 8rpx" />
          <text class="section-desc">已拉黑</text>
        </view>
      </view>

      <view class="card section">
        <view class="section-head">
          <view>
            <text class="section-title">我的展示资料</text>
            <view style="height: 10rpx" />
            <text class="section-desc">这部分决定别人看到你的第一印象，也会影响候选人排序。</text>
          </view>
          <button v-if="!profileEditorOpen" class="btn btn-ghost" size="mini" @tap="openProfileEditor">
            修改资料
          </button>
        </view>
        <view style="height: 20rpx" />

        <view v-if="!profileEditorOpen" class="profile-summary">
          <view>
            <text class="candidate-name">{{ profileForm.nickname || '还没有填写展示昵称' }}</text>
            <view style="height: 8rpx" />
            <text class="helper">
              {{ getProfileMeta() }} · {{ profileForm.is_visible ? '公开展示' : '暂不公开' }}
            </text>
          </view>
          <view v-if="splitList(profileForm.interestsText).length" class="tag-row">
            <text v-for="tag in splitList(profileForm.interestsText)" :key="tag" class="tag">{{ tag }}</text>
          </view>
          <text class="section-desc">{{ profileForm.bio || '还没有填写自我介绍。' }}</text>
        </view>

        <view v-else class="form">
          <view class="field">
            <text class="label">展示昵称</text>
            <input v-model="profileForm.nickname" class="input" type="text" placeholder="别人看到你的名字" />
          </view>
          <view class="field">
            <text class="label">性别</text>
            <picker :range="genderOptionLabels" :value="profileGenderIndex" @change="handleProfileGenderChange">
              <view class="input">{{ getGenderLabel(profileForm.gender) }}</view>
            </picker>
          </view>
          <view class="field">
            <text class="label">身高（cm）</text>
            <view class="height-row">
              <input
                v-model="profileForm.height_cm"
                class="input height-input"
                type="digit"
                placeholder="例如 170.5"
                :disabled="profileForm.height_private"
              />
              <button
                class="height-toggle"
                :class="{ active: profileForm.height_private }"
                size="mini"
                @tap="toggleHeightPrivate"
              >
                不便透露
              </button>
            </view>
          </view>
          <view class="field">
            <text class="label">体重（kg）</text>
            <input v-model="profileForm.weight_kg" class="input" type="digit" placeholder="例如 55.5，可不填" />
          </view>
          <view class="field">
            <text class="label">年龄</text>
            <input v-model="profileForm.age" class="input" type="number" placeholder="例如 20，可不填" />
          </view>
          <view class="field">
            <text class="label">兴趣标签</text>
            <input v-model="profileForm.interestsText" class="input" type="text" placeholder="摄影, Citywalk, AI, 电影" />
          </view>
          <view class="field">
            <text class="label">自我介绍</text>
            <textarea
              v-model="profileForm.bio"
              class="textarea"
              placeholder="简单介绍你的兴趣、相处节奏和你想认识什么样的人"
            />
          </view>
          <view class="field toggle-field">
            <view>
              <text class="label">公开到匹配广场</text>
              <view style="height: 8rpx" />
              <text class="helper">打开后，别人就能在候选人列表里看到你。</text>
            </view>
            <switch :checked="profileForm.is_visible" color="#f16b4f" @change="handleVisibleChange" />
          </view>
          <button class="btn btn-primary" :disabled="savingProfile" @tap="saveProfile">
            {{ savingProfile ? '保存中...' : '保存展示资料' }}
          </button>
        </view>
      </view>

      <view class="card section">
        <view class="section-head">
          <view>
            <text class="section-title">匹配偏好</text>
            <view style="height: 10rpx" />
            <text class="section-desc">先用轻量配置表达偏好，后面我们还可以继续升级成更完整的问答方式。</text>
          </view>
          <button v-if="!preferenceEditorOpen" class="btn btn-ghost" size="mini" @tap="openPreferenceEditor">
            修改偏好
          </button>
        </view>
        <view style="height: 20rpx" />

        <view v-if="!preferenceEditorOpen" class="profile-summary">
          <text class="candidate-name">当前偏好：{{ getPreferenceGenderSummary() }}</text>
          <text class="helper">{{ getPreferenceRangeSummary() }}</text>
          <view v-if="splitList(preferenceForm.preferredInterestsText).length" class="tag-row">
            <text v-for="tag in splitList(preferenceForm.preferredInterestsText)" :key="tag" class="tag">{{ tag }}</text>
          </view>
          <text v-else class="section-desc">还没有填写偏好兴趣，可以点击“修改偏好”补充。</text>
        </view>

        <view v-else class="form">
          <view class="field">
            <text class="label">偏好性别</text>
            <picker :range="genderPreferenceLabels" :value="preferredGenderPickerIndex" @change="handlePreferredGenderChange">
              <view class="input">{{ preferredGenderLabel }}</view>
            </picker>
          </view>
          <view class="field">
            <text class="label">最低身高（cm）</text>
            <input v-model="preferenceForm.min_height_cm" class="input" type="number" placeholder="可不填" />
          </view>
          <view class="field">
            <text class="label">最高身高（cm）</text>
            <input v-model="preferenceForm.max_height_cm" class="input" type="number" placeholder="可不填" />
          </view>
          <view class="field">
            <text class="label">最低体重（kg）</text>
            <input v-model="preferenceForm.min_weight_kg" class="input" type="digit" placeholder="可不填" />
          </view>
          <view class="field">
            <text class="label">最高体重（kg）</text>
            <input v-model="preferenceForm.max_weight_kg" class="input" type="digit" placeholder="可不填" />
          </view>
          <view class="field">
            <text class="label">最低年龄</text>
            <input v-model="preferenceForm.min_age" class="input" type="number" placeholder="可不填" />
          </view>
          <view class="field">
            <text class="label">最高年龄</text>
            <input v-model="preferenceForm.max_age" class="input" type="number" placeholder="可不填" />
          </view>
          <view class="field">
            <text class="label">偏好兴趣</text>
            <input v-model="preferenceForm.preferredInterestsText" class="input" type="text" placeholder="音乐, 运动, 阅读, 旅行" />
          </view>
          <button class="btn btn-primary" :disabled="savingPreference" @tap="savePreference">
            {{ savingPreference ? '保存中...' : '保存匹配偏好' }}
          </button>
        </view>
      </view>

      <view class="card section">
        <view class="section-head">
          <view>
            <text class="section-title">候选人列表</text>
            <view style="height: 8rpx" />
            <text class="section-desc">系统会根据你当前偏好给出基础匹配分数，下拉页面可以同时刷新候选人和匹配结果。</text>
          </view>
        </view>
        <view style="height: 20rpx" />

        <view v-if="candidates.length" class="grid">
          <view v-for="candidate in candidates" :key="candidate.id" class="candidate-card">
            <view class="candidate-head">
              <view>
                <text class="section-title candidate-name">{{ candidate.nickname || candidate.user.nickname || candidate.user.email }}</text>
                <view style="height: 8rpx" />
                <text class="helper">{{ getCandidateMeta(candidate) }}</text>
              </view>
              <view class="score-pill">匹配度 {{ candidate.match_score }}</view>
            </view>

            <view style="height: 14rpx" />
            <view class="tag-row">
              <text v-for="tag in candidate.interests" :key="tag" class="tag">{{ tag }}</text>
            </view>

            <view style="height: 14rpx" />
            <text class="section-desc">{{ candidate.bio || '对方还没有填写更多介绍。' }}</text>

            <view style="height: 18rpx" />
            <view class="action-row">
              <button class="btn btn-primary" size="mini" :disabled="signalingId === candidate.user.id" @tap="handleSignal(candidate.user.id, 'interested')">
                {{ signalingId === candidate.user.id ? '提交中...' : '感兴趣' }}
              </button>
              <button class="btn btn-ghost" size="mini" :disabled="signalingId === candidate.user.id" @tap="handleSignal(candidate.user.id, 'not_interested')">
                {{ signalingId === candidate.user.id ? '提交中...' : '先跳过' }}
              </button>
              <button class="btn btn-ghost" size="mini" :disabled="reportingId === candidate.id" @tap="handleReportCandidate(candidate)">
                {{ reportingId === candidate.id ? '提交中...' : '举报' }}
              </button>
              <button
                class="btn btn-secondary"
                size="mini"
                :disabled="blockingId === candidate.user.id || blockedUserIds.has(candidate.user.id)"
                @tap="handleBlockCandidate(candidate)"
              >
                {{ blockedUserIds.has(candidate.user.id) ? '已拉黑' : blockingId === candidate.user.id ? '处理中...' : '拉黑' }}
              </button>
            </view>
          </view>
        </view>

        <view v-else class="empty">
          <text class="section-desc">暂时还没有候选人。可以先完善资料、打开展示开关，或者晚点再来看看。</text>
        </view>
      </view>

      <view class="card">
        <view class="section-head">
          <view>
            <text class="section-title">已匹配结果</text>
            <view style="height: 8rpx" />
            <text class="section-desc">只有双方都表达“感兴趣”时，才会出现在这里；下拉页面可刷新最新结果。</text>
          </view>
        </view>
        <view style="height: 20rpx" />

        <view v-if="matches.length" class="grid">
          <view v-for="item in matches" :key="item.id" class="match-card">
            <text class="section-title candidate-name">{{ item.counterpart?.nickname || item.counterpart?.full_name || item.counterpart?.email }}</text>
            <view style="height: 8rpx" />
            <text class="helper">匹配时间：{{ formatDate(item.created_at) }}</text>
            <view v-if="item.counterpart?.id" style="height: 18rpx" />
            <button v-if="item.counterpart?.id" class="btn btn-primary" size="mini" @tap="startChat(item.counterpart.id)">
              开始聊天
            </button>
          </view>
        </view>

        <view v-else class="empty">
          <text class="section-desc">还没有形成双向匹配。你可以先浏览候选人，慢慢建立连接。</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'

import type { DatingCandidate, DatingMatch, DatingPreference, DatingProfile } from '../../types/api'
import {
  fetchDatingCandidates,
  fetchDatingMatches,
  fetchDatingPreference,
  fetchDatingProfile,
  sendDatingSignal,
  updateDatingPreference,
  updateDatingProfile,
} from '../../services/dating'
import { createBlock, createModerationReport, fetchMyBlocks } from '../../services/moderation'
import { ensureAuthenticated, isAuthenticated, profileOnboarded, redirectToLogin } from '../../utils/auth'
import { consumeAssistantDraft } from '../../utils/assistantDraft'
import { navigateTo } from '../../utils/navigation'
import { showToast } from '../../utils/ui'

const genderOptions = ['unknown', 'male', 'female', 'other']
const genderOptionLabels = ['不限制/未说明', '男', '女', '其他']
const genderPreferenceOptions = ['', ...genderOptions]
const genderPreferenceLabels = ['不限', ...genderOptionLabels]
const hasToken = ref(isAuthenticated.value)
const profileComplete = computed(() => profileOnboarded.value)
const savingProfile = ref(false)
const savingPreference = ref(false)
const loadingCandidates = ref(false)
const loadingMatches = ref(false)
const signalingId = ref('')
const reportingId = ref('')
const blockingId = ref('')
const candidates = ref<DatingCandidate[]>([])
const matches = ref<DatingMatch[]>([])
const blockedUserIds = ref<Set<string>>(new Set())
const profileEditorOpen = ref(false)
const profileLoaded = ref(false)
const preferenceEditorOpen = ref(false)
const preferenceLoaded = ref(false)

const profileForm = reactive({
  nickname: '',
  gender: 'unknown' as DatingProfile['gender'],
  height_cm: '',
  height_private: false,
  weight_kg: '',
  age: '',
  interestsText: '',
  bio: '',
  is_visible: true,
})

const preferenceForm = reactive({
  preferredGendersText: '',
  min_height_cm: '',
  max_height_cm: '',
  min_weight_kg: '',
  max_weight_kg: '',
  min_age: '',
  max_age: '',
  preferredInterestsText: '',
})

const profileGenderIndex = computed(() => {
  const idx = genderOptions.indexOf(profileForm.gender)
  return idx >= 0 ? idx : 0
})

const preferredGenderPickerIndex = computed(() => {
  const values = splitList(preferenceForm.preferredGendersText)
  if (!values.length) {
    return 0
  }
  const idx = genderPreferenceOptions.indexOf(values[0])
  return idx >= 0 ? idx : 0
})

const preferredGenderLabel = computed(() => {
  const values = splitList(preferenceForm.preferredGendersText)
  if (!values.length) {
    return '不限'
  }
  return values.map(getGenderLabel).join('、')
})

onShow(() => {
  hasToken.value = isAuthenticated.value
  if (hasToken.value && profileComplete.value) {
    void bootstrapDating()
  }
})

onPullDownRefresh(async () => {
  if (hasToken.value && profileComplete.value) {
    await bootstrapDating()
  }
  uni.stopPullDownRefresh()
})

onReachBottom(() => {
  if (hasToken.value && profileComplete.value) {
    void Promise.all([loadCandidates(), loadMatches(), loadBlocks()])
  }
})

async function bootstrapDating() {
  await Promise.all([loadProfile(), loadPreference(), loadCandidates(), loadMatches(), loadBlocks()])
  applyAssistantDraft()
}

function applyAssistantDraft() {
  const draft = consumeAssistantDraft('/pages/dating/index', ['dating_profile_update', 'dating_preference_update'])
  if (!draft) {
    return
  }
  const payload = draft.fill_payload
  if (draft.kind === 'dating_profile_update') {
    profileEditorOpen.value = true
    profileForm.nickname = typeof payload.nickname === 'string' ? payload.nickname : profileForm.nickname
    profileForm.gender = typeof payload.gender === 'string' ? payload.gender as DatingProfile['gender'] : profileForm.gender
    profileForm.height_cm = payload.height_cm === null || payload.height_cm === undefined ? profileForm.height_cm : String(payload.height_cm)
    profileForm.height_private = payload.height_cm === null || payload.height_cm === undefined
    profileForm.weight_kg = payload.weight_kg === null || payload.weight_kg === undefined ? profileForm.weight_kg : String(payload.weight_kg)
    profileForm.age = payload.age === null || payload.age === undefined ? profileForm.age : String(payload.age)
    profileForm.bio = typeof payload.bio === 'string' ? payload.bio : profileForm.bio
    profileForm.is_visible = typeof payload.is_visible === 'boolean' ? payload.is_visible : profileForm.is_visible
    if (Array.isArray(payload.interests)) {
      profileForm.interestsText = payload.interests.map(String).join(', ')
    } else if (typeof payload.interests === 'string') {
      profileForm.interestsText = payload.interests
    }
    showToast('AI 已填入展示资料草稿', 'success')
    return
  }
  preferenceEditorOpen.value = true
  preferenceForm.preferredGendersText = Array.isArray(payload.preferred_genders)
    ? payload.preferred_genders.map(String).join(', ')
    : preferenceForm.preferredGendersText
  preferenceForm.min_height_cm = payload.min_height_cm === null || payload.min_height_cm === undefined ? preferenceForm.min_height_cm : String(payload.min_height_cm)
  preferenceForm.max_height_cm = payload.max_height_cm === null || payload.max_height_cm === undefined ? preferenceForm.max_height_cm : String(payload.max_height_cm)
  preferenceForm.min_weight_kg = payload.min_weight_kg === null || payload.min_weight_kg === undefined ? preferenceForm.min_weight_kg : String(payload.min_weight_kg)
  preferenceForm.max_weight_kg = payload.max_weight_kg === null || payload.max_weight_kg === undefined ? preferenceForm.max_weight_kg : String(payload.max_weight_kg)
  preferenceForm.min_age = payload.min_age === null || payload.min_age === undefined ? preferenceForm.min_age : String(payload.min_age)
  preferenceForm.max_age = payload.max_age === null || payload.max_age === undefined ? preferenceForm.max_age : String(payload.max_age)
  if (Array.isArray(payload.preferred_interests)) {
    preferenceForm.preferredInterestsText = payload.preferred_interests.map(String).join(', ')
  } else if (typeof payload.preferred_interests === 'string') {
    preferenceForm.preferredInterestsText = payload.preferred_interests
  }
  showToast('AI 已填入匹配偏好草稿', 'success')
}

async function loadProfile() {
  try {
    const profile = await fetchDatingProfile()
    profileForm.nickname = profile.nickname ?? ''
    profileForm.gender = profile.gender ?? 'unknown'
    profileForm.height_cm = profile.height_cm ? String(profile.height_cm) : ''
    profileForm.height_private = profile.height_cm == null
    profileForm.weight_kg = profile.weight_kg ? String(profile.weight_kg) : ''
    profileForm.age = profile.age ? String(profile.age) : ''
    profileForm.interestsText = (profile.interests ?? []).join(', ')
    profileForm.bio = profile.bio ?? ''
    profileForm.is_visible = profile.is_visible
    profileLoaded.value = true
    profileEditorOpen.value = !isDisplayProfileComplete()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '加载匹配资料失败')
  }
}

async function loadPreference() {
  try {
    const preference = await fetchDatingPreference()
    preferenceForm.preferredGendersText = (preference.preferred_genders ?? []).join(', ')
    preferenceForm.min_height_cm = preference.min_height_cm ? String(preference.min_height_cm) : ''
    preferenceForm.max_height_cm = preference.max_height_cm ? String(preference.max_height_cm) : ''
    preferenceForm.min_weight_kg = preference.min_weight_kg ? String(preference.min_weight_kg) : ''
    preferenceForm.max_weight_kg = preference.max_weight_kg ? String(preference.max_weight_kg) : ''
    preferenceForm.min_age = preference.min_age ? String(preference.min_age) : ''
    preferenceForm.max_age = preference.max_age ? String(preference.max_age) : ''
    preferenceForm.preferredInterestsText = (preference.preferred_interests ?? []).join(', ')
    preferenceLoaded.value = true
    preferenceEditorOpen.value = !isPreferenceConfigured()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '加载匹配偏好失败')
  }
}

async function loadCandidates() {
  loadingCandidates.value = true
  try {
    candidates.value = await fetchDatingCandidates()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '加载候选人失败')
  } finally {
    loadingCandidates.value = false
  }
}

async function loadMatches() {
  loadingMatches.value = true
  try {
    matches.value = await fetchDatingMatches()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '加载匹配结果失败')
  } finally {
    loadingMatches.value = false
  }
}

async function loadBlocks() {
  try {
    const blocks = await fetchMyBlocks()
    blockedUserIds.value = new Set(blocks.map((item) => item.blocked_user_detail.id))
  } catch {
    blockedUserIds.value = new Set()
  }
}

async function saveProfile() {
  const height = normalizeHeight(profileForm.height_cm, profileForm.height_private)
  const weight = normalizeOptionalFloat(profileForm.weight_kg)
  const age = normalizeOptionalInteger(profileForm.age)
  if (height === undefined || weight === undefined || age === undefined) {
    showToast('身高、体重或年龄格式不正确')
    return
  }

  savingProfile.value = true
  try {
    await updateDatingProfile({
      nickname: profileForm.nickname.trim(),
      gender: profileForm.gender,
      height_cm: height,
      weight_kg: weight,
      age,
      interests: splitList(profileForm.interestsText),
      personality_type: '',
      bio: profileForm.bio.trim(),
      is_visible: profileForm.is_visible,
    })
    showToast('匹配资料已保存', 'success')
    profileEditorOpen.value = false
    await loadCandidates()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '保存匹配资料失败')
  } finally {
    savingProfile.value = false
  }
}

async function savePreference() {
  const minHeight = normalizeOptionalHeight(preferenceForm.min_height_cm)
  const maxHeight = normalizeOptionalHeight(preferenceForm.max_height_cm)
  const minWeight = normalizeOptionalFloat(preferenceForm.min_weight_kg)
  const maxWeight = normalizeOptionalFloat(preferenceForm.max_weight_kg)
  const minAge = normalizeOptionalInteger(preferenceForm.min_age)
  const maxAge = normalizeOptionalInteger(preferenceForm.max_age)
  if (minHeight === undefined || maxHeight === undefined || minWeight === undefined || maxWeight === undefined || minAge === undefined || maxAge === undefined) {
    showToast('偏好范围请填写数字')
    return
  }

  savingPreference.value = true
  try {
    await updateDatingPreference({
      preferred_genders: splitList(preferenceForm.preferredGendersText) as DatingPreference['preferred_genders'],
      min_height_cm: minHeight,
      max_height_cm: maxHeight,
      min_weight_kg: minWeight,
      max_weight_kg: maxWeight,
      min_age: minAge,
      max_age: maxAge,
      preferred_interests: splitList(preferenceForm.preferredInterestsText),
      preferred_personality_types: [],
    })
    showToast('匹配偏好已保存', 'success')
    preferenceLoaded.value = true
    preferenceEditorOpen.value = false
    await loadCandidates()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '保存匹配偏好失败')
  } finally {
    savingPreference.value = false
  }
}

async function handleSignal(targetUserId: string, signal: 'interested' | 'not_interested') {
  signalingId.value = targetUserId
  try {
    const result = await sendDatingSignal({ target_user_id: targetUserId, signal })
    showToast(result.matched ? '匹配成功，已加入匹配结果' : signal === 'interested' ? '已表达感兴趣' : '已跳过', 'success')
    await Promise.all([loadCandidates(), loadMatches()])
  } catch (error) {
    showToast(error instanceof Error ? error.message : '提交失败')
  } finally {
    signalingId.value = ''
  }
}

async function handleReportCandidate(candidate: DatingCandidate) {
  reportingId.value = candidate.id
  try {
    const reasons = ['骚扰言论', '虚假资料', '不当内容', '冒充身份', '其他原因']
    const reasonIndex = await new Promise<number>((resolve, reject) => {
      uni.showActionSheet({
        itemList: reasons,
        success: ({ tapIndex }) => resolve(tapIndex),
        fail: reject,
      })
    })

    const details = await new Promise<string>((resolve) => {
      uni.showModal({
        title: '补充说明',
        editable: true,
        placeholderText: '可选，简单说明问题',
        success: (result) => {
          if (!result.confirm) {
            resolve('')
            return
          }
          resolve(((result as { content?: string }).content ?? '').trim())
        },
        fail: () => resolve(''),
      })
    })

    await createModerationReport({
      target_type: 'dating_profile',
      target_id: candidate.id,
      reason: reasons[reasonIndex] ?? '其他原因',
      details,
    })
    showToast('举报已提交，我们会尽快处理', 'success')
  } catch {
    return
  } finally {
    reportingId.value = ''
  }
}

async function handleBlockCandidate(candidate: DatingCandidate) {
  blockingId.value = candidate.user.id
  try {
    await createBlock({
      blocked_user: candidate.user.id,
      reason: '来自匹配页的手动拉黑',
    })
    blockedUserIds.value = new Set([...blockedUserIds.value, candidate.user.id])
    candidates.value = candidates.value.filter((item) => item.user.id !== candidate.user.id)
    showToast('已拉黑该用户，后续不会继续向你展示', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '拉黑失败')
  } finally {
    blockingId.value = ''
  }
}

function splitList(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function handleProfileGenderChange(event: { detail?: { value?: string | number } }) {
  profileForm.gender = (genderOptions[Number(event.detail?.value ?? 0)] ?? 'unknown') as DatingProfile['gender']
}

function handlePreferredGenderChange(event: { detail?: { value?: string | number } }) {
  const selected = genderPreferenceOptions[Number(event.detail?.value ?? 0)] ?? ''
  preferenceForm.preferredGendersText = selected
}

function handleVisibleChange(event: { detail?: { value?: boolean } }) {
  profileForm.is_visible = Boolean(event.detail?.value)
}

function openProfileEditor() {
  profileEditorOpen.value = true
}

function openPreferenceEditor() {
  preferenceEditorOpen.value = true
}

function toggleHeightPrivate() {
  profileForm.height_private = !profileForm.height_private
  if (profileForm.height_private) {
    profileForm.height_cm = ''
  }
}

function normalizeHeight(value: string, privateHeight: boolean) {
  if (privateHeight) {
    return null
  }
  return normalizeOptionalHeight(value)
}

function normalizeOptionalHeight(value: string) {
  return normalizeOptionalFloat(value)
}

function normalizeOptionalFloat(value: string) {
  const trimmed = value.trim()
  if (!trimmed) {
    return null
  }
  const parsed = Number(trimmed)
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return undefined
  }
  return parsed
}

function normalizeOptionalInteger(value: string) {
  const parsed = normalizeOptionalFloat(value)
  if (parsed === undefined || parsed === null) {
    return parsed
  }
  if (!Number.isInteger(parsed)) {
    return undefined
  }
  return parsed
}

function isDisplayProfileComplete() {
  if (!profileLoaded.value) {
    return false
  }
  return Boolean(profileForm.nickname.trim() || profileForm.bio.trim() || splitList(profileForm.interestsText).length)
}

function isPreferenceConfigured() {
  if (!preferenceLoaded.value) {
    return false
  }
  return Boolean(
    splitList(preferenceForm.preferredGendersText).length
      || preferenceForm.min_height_cm.trim()
      || preferenceForm.max_height_cm.trim()
      || preferenceForm.min_weight_kg.trim()
      || preferenceForm.max_weight_kg.trim()
      || preferenceForm.min_age.trim()
      || preferenceForm.max_age.trim()
      || splitList(preferenceForm.preferredInterestsText).length,
  )
}

function getHeightLabel(value: string) {
  if (profileForm.height_private || !value.trim()) {
    return '不便透露身高'
  }
  return `${value.trim()}cm`
}

function getOptionalLabel(value: string, unit: string, emptyText: string) {
  return value.trim() ? `${value.trim()}${unit}` : emptyText
}

function getProfileMeta() {
  return [
    getGenderLabel(profileForm.gender),
    getHeightLabel(profileForm.height_cm),
    getOptionalLabel(profileForm.weight_kg, 'kg', '未填写体重'),
    getOptionalLabel(profileForm.age, '岁', '未填写年龄'),
  ].join(' · ')
}

function getPreferenceGenderSummary() {
  const values = splitList(preferenceForm.preferredGendersText)
  if (!values.length) {
    return '性别不限'
  }
  return values.map(getGenderLabel).join('、')
}

function getRangeText(minValue: string, maxValue: string, unit: string, emptyText: string) {
  const minText = minValue.trim()
  const maxText = maxValue.trim()
  if (minText && maxText) {
    return `${minText}-${maxText}${unit}`
  }
  if (minText) {
    return `${minText}${unit}以上`
  }
  if (maxText) {
    return `${maxText}${unit}以下`
  }
  return emptyText
}

function getPreferenceRangeSummary() {
  return [
    getRangeText(preferenceForm.min_height_cm, preferenceForm.max_height_cm, 'cm', '身高不限'),
    getRangeText(preferenceForm.min_weight_kg, preferenceForm.max_weight_kg, 'kg', '体重不限'),
    getRangeText(preferenceForm.min_age, preferenceForm.max_age, '岁', '年龄不限'),
  ].join(' · ')
}

function getCandidateMeta(candidate: DatingCandidate) {
  return [
    getGenderLabel(candidate.gender),
    candidate.height_cm ? `${candidate.height_cm}cm` : '未填写身高',
    candidate.weight_kg ? `${candidate.weight_kg}kg` : '未填写体重',
    candidate.age ? `${candidate.age}岁` : '未填写年龄',
  ].join(' · ')
}

function getGenderLabel(value: string) {
  if (value === 'male') {
    return '男'
  }
  if (value === 'female') {
    return '女'
  }
  if (value === 'other') {
    return '其他'
  }
  return '未说明'
}

function formatDate(value: string) {
  return value.replace('T', ' ').slice(0, 16)
}

function goLogin() {
  redirectToLogin('/pages/dating/index')
}

function goProfile() {
  navigateTo('/pages/profile/index')
}

function startChat(targetUserId: string) {
  navigateTo(`/pages/chat/index?targetUserId=${targetUserId}`)
}
</script>

<style scoped lang="scss">
.hero {
  padding-top: 4rpx;
}

.status-row {
  display: flex;
  gap: 16rpx;
  flex-wrap: wrap;
}

.status-chip {
  padding: 12rpx 20rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.84);
  color: #102133;
  font-size: 24rpx;
  font-weight: 600;
}

.status-chip.active {
  background: rgba(241, 107, 79, 0.14);
  color: #f16b4f;
}

.status-chip.complete {
  background: rgba(77, 166, 106, 0.18);
  color: #2e7d49;
}

.stats-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.stat-card {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 44rpx;
  font-weight: 700;
  color: #102133;
}

.section-head,
.candidate-head,
.action-row {
  display: flex;
  gap: 16rpx;
  flex-wrap: wrap;
}

.section-head,
.candidate-head {
  justify-content: space-between;
  align-items: flex-start;
}

.toggle-field {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.profile-summary {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.height-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.height-input {
  flex: 1;
}

.height-toggle {
  flex-shrink: 0;
  min-height: 72rpx;
  padding: 0 22rpx;
  margin: 0;
  border: 0;
  border-radius: 999rpx;
  background: rgba(16, 33, 51, 0.08);
  color: #102133;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.height-toggle.active {
  background: rgba(241, 107, 79, 0.14);
  color: #f16b4f;
}

.height-toggle::after {
  border: 0;
}

.candidate-card,
.match-card {
  padding: 28rpx;
  border-radius: 28rpx;
  background: rgba(255, 250, 245, 0.86);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
}

.candidate-name {
  margin-bottom: 0;
  font-size: 32rpx;
}

.score-pill {
  flex-shrink: 0;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(241, 107, 79, 0.12);
  color: #f16b4f;
  font-size: 22rpx;
  font-weight: 700;
}
</style>
