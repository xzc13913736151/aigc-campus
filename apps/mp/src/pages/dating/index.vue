<template>
  <view class="container">
    <view class="section hero">
      <text class="eyebrow">CampusClaw Dating</text>
      <view style="height: 18rpx" />
      <text class="title">先把自己说清楚，再去认识那些和你可能聊得来的人。</text>
      <view style="height: 18rpx" />
      <text class="subtitle">
        这一页把资料、偏好、候选人和匹配结果收在一起。你可以先完善展示信息，再决定喜欢、跳过、举报或拉黑。
      </text>
      <view style="height: 24rpx" />

      <view class="status-row">
        <view class="status-chip" :class="{ active: hasToken }">
          <text>{{ hasToken ? '已登录' : '未登录' }}</text>
        </view>
        <view class="status-chip" :class="{ complete: profileComplete }">
          <text>{{ profileComplete ? '基础资料已完成' : '请先补全基础资料' }}</text>
        </view>
      </view>
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
        <text class="section-title">我的展示资料</text>
        <view style="height: 10rpx" />
        <text class="section-desc">这部分决定别人看到你的第一印象，也会影响候选人排序。</text>
        <view style="height: 20rpx" />

        <view class="form">
          <view class="field">
            <text class="label">展示昵称</text>
            <input v-model="profileForm.nickname" class="input" type="text" placeholder="别人看到你的名字" />
          </view>
          <view class="field">
            <text class="label">性别</text>
            <picker :range="genderOptions" :value="profileGenderIndex" @change="handleProfileGenderChange">
              <view class="input">{{ getGenderLabel(profileForm.gender) }}</view>
            </picker>
          </view>
          <view class="field">
            <text class="label">身高（cm）</text>
            <input v-model="profileForm.height_cm" class="input" type="number" placeholder="例如 170" />
          </view>
          <view class="field">
            <text class="label">兴趣标签</text>
            <input v-model="profileForm.interestsText" class="input" type="text" placeholder="摄影, Citywalk, AI, 电影" />
          </view>
          <view class="field">
            <text class="label">人格类型</text>
            <input v-model="profileForm.personality_type" class="input" type="text" placeholder="例如 INFP / ENTP" />
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
        <text class="section-title">匹配偏好</text>
        <view style="height: 10rpx" />
        <text class="section-desc">先用轻量配置表达偏好，后面我们还可以继续升级成更完整的问答方式。</text>
        <view style="height: 20rpx" />

        <view class="form">
          <view class="field">
            <text class="label">偏好性别</text>
            <input v-model="preferenceForm.preferredGendersText" class="input" type="text" placeholder="male, female, other, unknown" />
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
            <text class="label">偏好兴趣</text>
            <input v-model="preferenceForm.preferredInterestsText" class="input" type="text" placeholder="音乐, 运动, 阅读, 旅行" />
          </view>
          <view class="field">
            <text class="label">偏好人格类型</text>
            <input v-model="preferenceForm.preferredPersonalityTypesText" class="input" type="text" placeholder="INFJ, ENFP, ISTJ" />
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
            <text class="section-desc">系统会根据你当前偏好给出基础匹配分数，遇到不合适对象时也可以直接举报或拉黑。</text>
          </view>
          <button class="btn btn-ghost" size="mini" :disabled="loadingCandidates" @tap="loadCandidates">
            {{ loadingCandidates ? '刷新中...' : '刷新候选人' }}
          </button>
        </view>
        <view style="height: 20rpx" />

        <view v-if="candidates.length" class="grid">
          <view v-for="candidate in candidates" :key="candidate.id" class="candidate-card">
            <view class="candidate-head">
              <view>
                <text class="section-title candidate-name">{{ candidate.nickname || candidate.user.nickname || candidate.user.email }}</text>
                <view style="height: 8rpx" />
                <text class="helper">{{ getGenderLabel(candidate.gender) }} · {{ candidate.height_cm || '未填写身高' }}</text>
              </view>
              <view class="score-pill">匹配度 {{ candidate.match_score }}</view>
            </view>

            <view style="height: 14rpx" />
            <view class="tag-row">
              <text v-for="tag in candidate.interests" :key="tag" class="tag">{{ tag }}</text>
              <text v-if="candidate.personality_type" class="tag">{{ candidate.personality_type }}</text>
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
            <text class="section-desc">只有双方都表达“感兴趣”时，才会出现在这里。</text>
          </view>
          <button class="btn btn-ghost" size="mini" :disabled="loadingMatches" @tap="loadMatches">
            {{ loadingMatches ? '刷新中...' : '刷新匹配' }}
          </button>
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
import { onShow } from '@dcloudio/uni-app'

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
import { navigateTo } from '../../utils/navigation'
import { showToast } from '../../utils/ui'

const genderOptions = ['unknown', 'male', 'female', 'other']
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

const profileForm = reactive({
  nickname: '',
  gender: 'unknown' as DatingProfile['gender'],
  height_cm: '',
  interestsText: '',
  personality_type: '',
  bio: '',
  is_visible: true,
})

const preferenceForm = reactive({
  preferredGendersText: '',
  min_height_cm: '',
  max_height_cm: '',
  preferredInterestsText: '',
  preferredPersonalityTypesText: '',
})

const profileGenderIndex = computed(() => {
  const idx = genderOptions.indexOf(profileForm.gender)
  return idx >= 0 ? idx : 0
})

onShow(() => {
  hasToken.value = isAuthenticated.value
  if (hasToken.value && profileComplete.value) {
    bootstrapDating()
  }
})

async function bootstrapDating() {
  await Promise.all([loadProfile(), loadPreference(), loadCandidates(), loadMatches(), loadBlocks()])
}

async function loadProfile() {
  try {
    const profile = await fetchDatingProfile()
    profileForm.nickname = profile.nickname ?? ''
    profileForm.gender = profile.gender ?? 'unknown'
    profileForm.height_cm = profile.height_cm ? String(profile.height_cm) : ''
    profileForm.interestsText = (profile.interests ?? []).join(', ')
    profileForm.personality_type = profile.personality_type ?? ''
    profileForm.bio = profile.bio ?? ''
    profileForm.is_visible = profile.is_visible
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
    preferenceForm.preferredInterestsText = (preference.preferred_interests ?? []).join(', ')
    preferenceForm.preferredPersonalityTypesText = (preference.preferred_personality_types ?? []).join(', ')
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
  savingProfile.value = true
  try {
    await updateDatingProfile({
      nickname: profileForm.nickname.trim(),
      gender: profileForm.gender,
      height_cm: profileForm.height_cm ? Number(profileForm.height_cm) : null,
      interests: splitList(profileForm.interestsText),
      personality_type: profileForm.personality_type.trim(),
      bio: profileForm.bio.trim(),
      is_visible: profileForm.is_visible,
    })
    showToast('匹配资料已保存', 'success')
    await loadCandidates()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '保存匹配资料失败')
  } finally {
    savingProfile.value = false
  }
}

async function savePreference() {
  savingPreference.value = true
  try {
    await updateDatingPreference({
      preferred_genders: splitList(preferenceForm.preferredGendersText) as DatingPreference['preferred_genders'],
      min_height_cm: preferenceForm.min_height_cm ? Number(preferenceForm.min_height_cm) : null,
      max_height_cm: preferenceForm.max_height_cm ? Number(preferenceForm.max_height_cm) : null,
      preferred_interests: splitList(preferenceForm.preferredInterestsText),
      preferred_personality_types: splitList(preferenceForm.preferredPersonalityTypesText),
    })
    showToast('匹配偏好已保存', 'success')
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

function handleVisibleChange(event: { detail?: { value?: boolean } }) {
  profileForm.is_visible = Boolean(event.detail?.value)
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
