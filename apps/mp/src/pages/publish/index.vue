<template>
  <view class="container">
    <view class="section">
      <text class="eyebrow">Publish Center</text>
      <view style="height: 18rpx" />
      <text class="title">一个页面完成发帖、组队招募和恋爱匹配资料公开。</text>
      <view style="height: 18rpx" />
      <text class="subtitle">
        这里是 CampusClaw 的统一发布中心。你可以根据目标切换不同模式，把内容一次性整理好再对外展示。
      </text>
      <view style="height: 24rpx" />

      <view class="status-row">
        <view class="status-chip">
          <text>{{ hasToken ? '已登录' : '未登录' }}</text>
        </view>
        <view class="status-chip" :class="{ complete: profileComplete }">
          <text>{{ hasToken ? (profileComplete ? '资料已可发布' : '请先完善资料') : '登录后可发布' }}</text>
        </view>
      </view>
    </view>

    <view class="card section">
      <scroll-view scroll-x class="mode-scroll" enhanced show-scrollbar="false">
        <view class="mode-row">
          <button
            v-for="item in modeCards"
            :key="item.key"
            class="mode-chip"
            :class="{ active: activeMode === item.key }"
            @tap="switchMode(item.key)"
          >
            {{ item.label }}
          </button>
        </view>
      </scroll-view>

      <view style="height: 20rpx" />

      <view class="mode-summary">
        <view>
          <text class="section-title">{{ activeCard.title }}</text>
          <view style="height: 8rpx" />
          <text class="section-desc">{{ activeCard.description }}</text>
        </view>
        <text class="mode-badge">{{ activeCard.badge }}</text>
      </view>

      <view style="height: 18rpx" />

      <view class="tag-row">
        <text v-for="tag in activeCard.tags" :key="tag" class="tag">{{ tag }}</text>
      </view>
    </view>

    <view v-if="!hasToken" class="card empty">
      <text class="section-desc">登录后才能发布内容、招募队友或公开你的匹配资料。</text>
      <view style="height: 24rpx" />
      <button class="btn btn-primary" @tap="goLogin">去登录</button>
    </view>

    <view v-else-if="!profileComplete" class="card empty">
      <text class="section-desc">请先完成个人资料补全，再来发布内容。这样别人才知道你是谁，也更愿意回应你。</text>
      <view style="height: 24rpx" />
      <button class="btn btn-primary" @tap="goProfile">完善资料</button>
    </view>

    <view v-else-if="activeMode === 'forum'" class="card section">
      <view class="form">
        <view class="field compact-action">
          <view>
            <text class="label">完整发帖编辑器</text>
            <view style="height: 8rpx" />
            <text class="helper">支持发帖前选择图片、发布后自动上传、编辑和进入详情页。</text>
          </view>
          <button class="btn btn-ghost" size="mini" @tap="goForumCreate">打开</button>
        </view>

        <view class="field">
          <text class="label">帖子标题</text>
          <input v-model="forumForm.title" class="input" type="text" placeholder="一句话说清你想讨论什么" />
        </view>

        <view class="field">
          <text class="label">帖子分类</text>
          <picker :range="forumCategories" @change="handleForumCategoryChange">
            <view class="input">{{ forumForm.category || '请选择帖子分类' }}</view>
          </picker>
        </view>

        <view class="field">
          <text class="label">正文内容</text>
          <textarea
            v-model="forumForm.body"
            class="textarea"
            placeholder="写清背景、问题、诉求，或者你想和大家讨论的内容"
          />
        </view>

        <view class="field">
          <text class="label">标签</text>
          <input v-model="forumForm.tagsText" class="input" type="text" placeholder="AI, 校园活动, 求助, 实习" />
          <text class="helper">多个标签请用英文逗号分隔。</text>
        </view>

        <text v-if="forumError" class="error">{{ forumError }}</text>
        <button class="btn btn-primary" :disabled="forumSubmitting" @tap="submitForumPost">
          {{ forumSubmitting ? '发布中...' : '发布帖子' }}
        </button>
      </view>
    </view>

    <view v-else-if="activeMode === 'team'" class="card section">
      <view class="form">
        <view class="field">
          <text class="label">招募标题</text>
          <input v-model="teamForm.title" class="input" type="text" placeholder="例如：找 2 位同学一起做 AI 校园项目" />
        </view>

        <view class="field">
          <text class="label">一句话概述</text>
          <input v-model="teamForm.summary" class="input" type="text" placeholder="说明方向、节奏和你最想找什么样的人" />
        </view>

        <view class="field">
          <text class="label">详细说明</text>
          <textarea
            v-model="teamForm.details"
            class="textarea"
            placeholder="写清背景、目标、时间安排、分工和合作方式"
          />
        </view>

        <view class="field">
          <text class="label">目标人数</text>
          <input v-model="teamForm.targetSize" class="input" type="number" placeholder="2 - 20" />
        </view>

        <view class="field">
          <text class="label">项目标签</text>
          <input v-model="teamForm.tagsText" class="input" type="text" placeholder="AI, 产品, 比赛, 校园活动" />
        </view>

        <view class="field">
          <text class="label">需要的技能</text>
          <input v-model="teamForm.skillsText" class="input" type="text" placeholder="前端, 后端, 设计, 文案" />
        </view>

        <text v-if="teamError" class="error">{{ teamError }}</text>
        <button class="btn btn-primary" :disabled="teamSubmitting" @tap="submitTeamPost">
          {{ teamSubmitting ? '发布中...' : '发布组队招募' }}
        </button>
      </view>
    </view>

    <view v-else class="card section">
      <view class="form">
        <view class="field">
          <text class="label">展示昵称</text>
          <input v-model="datingForm.nickname" class="input" type="text" placeholder="在匹配页展示给别人的名字" />
        </view>

        <view class="field">
          <text class="label">性别</text>
          <picker :range="genderOptions" :value="datingGenderIndex" @change="handleDatingGenderChange">
            <view class="input">{{ getGenderLabel(datingForm.gender) }}</view>
          </picker>
        </view>

        <view class="field">
          <text class="label">兴趣标签</text>
          <input v-model="datingForm.interestsText" class="input" type="text" placeholder="摄影, Citywalk, AI, 电影" />
        </view>

        <view class="field">
          <text class="label">人格类型</text>
          <input v-model="datingForm.personalityType" class="input" type="text" placeholder="例如 INFP / ENTP" />
        </view>

        <view class="field">
          <text class="label">自我介绍</text>
          <textarea
            v-model="datingForm.bio"
            class="textarea"
            placeholder="简单介绍你的兴趣、相处节奏，以及你想认识什么样的人"
          />
        </view>

        <view class="field">
          <text class="label">希望匹配的性别</text>
          <input
            v-model="datingForm.preferredGendersText"
            class="input"
            type="text"
            placeholder="male, female, other, unknown"
          />
          <text class="helper">多个值请用英文逗号分隔。</text>
        </view>

        <view class="field toggle-field">
          <view>
            <text class="label">公开到匹配广场</text>
            <view style="height: 8rpx" />
            <text class="helper">打开后，别人就能在恋爱匹配页看到你。</text>
          </view>
          <switch :checked="datingForm.isVisible" color="#f16b4f" @change="handleVisibleChange" />
        </view>

        <text v-if="datingError" class="error">{{ datingError }}</text>

        <view class="btn-row">
          <button class="btn btn-primary" :disabled="datingSubmitting || datingLoading" @tap="submitDatingProfile">
            {{ datingSubmitting ? '保存中...' : datingLoading ? '读取中...' : '公开恋爱匹配资料' }}
          </button>
          <button class="btn btn-ghost" size="mini" @tap="goDating">去匹配页查看效果</button>
        </view>
      </view>
    </view>

    <view class="card tips-card">
      <text class="section-title">发布建议</text>
      <view style="height: 12rpx" />
      <view class="tips-list">
        <text v-for="tip in tips" :key="tip" class="section-desc">- {{ tip }}</text>
      </view>
    </view>

    <BottomTabBar />
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import BottomTabBar from '../../components/BottomTabBar.vue'
import type { DatingPreference, DatingProfile } from '../../types/api'
import { createForumPost } from '../../services/forum'
import { createTeammatePost } from '../../services/teammates'
import { fetchDatingPreference, fetchDatingProfile, updateDatingPreference, updateDatingProfile } from '../../services/dating'
import { isAuthenticated, profileOnboarded, redirectToLogin } from '../../utils/auth'
import { navigateTo } from '../../utils/navigation'
import { showToast } from '../../utils/ui'

type PublishMode = 'forum' | 'team' | 'dating'

const forumCategories = ['校园日常', '学习交流', '活动组局', '实习求职', '项目合作', '组队招募', '情绪树洞']
const genderOptions = ['unknown', 'male', 'female', 'other']

const hasToken = computed(() => isAuthenticated.value)
const profileComplete = computed(() => profileOnboarded.value)
const activeMode = ref<PublishMode>('forum')

const forumSubmitting = ref(false)
const teamSubmitting = ref(false)
const datingSubmitting = ref(false)
const datingLoading = ref(false)

const forumError = ref('')
const teamError = ref('')
const datingError = ref('')

const datingProfileLoaded = ref(false)
const datingPreferenceLoaded = ref(false)

const forumForm = reactive({
  title: '',
  category: '',
  body: '',
  tagsText: '',
})

const teamForm = reactive({
  title: '',
  summary: '',
  details: '',
  targetSize: '3',
  tagsText: '',
  skillsText: '',
})

const datingForm = reactive({
  nickname: '',
  gender: 'unknown' as DatingProfile['gender'],
  heightCm: '',
  interestsText: '',
  personalityType: '',
  bio: '',
  isVisible: true,
  preferredGendersText: '',
  preferredInterestsText: '',
  preferredTypesText: '',
})

const modeCards = [
  {
    key: 'forum' as const,
    label: '发帖子',
    title: '论坛帖子发布',
    badge: '轻量表达',
    description: '适合分享想法、提问求助、记录进展或发起讨论，是最快速的内容发布方式。',
    tags: ['讨论', '求助', '分享'],
  },
  {
    key: 'team' as const,
    label: '发组队',
    title: '组队招募发布',
    badge: '合作招募',
    description: '适合发布项目招募、比赛组队、活动合作或学习搭子需求。',
    tags: ['项目', '招募', '协作'],
  },
  {
    key: 'dating' as const,
    label: '发恋爱匹配',
    title: '恋爱匹配公开资料',
    badge: '公开展示',
    description: '把你的匹配资料和偏好整理好，公开到匹配广场里，等待合适的人看到你。',
    tags: ['匹配', '资料', '公开展示'],
  },
]

const activeCard = computed(() => modeCards.find((item) => item.key === activeMode.value) ?? modeCards[0])
const datingGenderIndex = computed(() => {
  const index = genderOptions.indexOf(datingForm.gender)
  return index >= 0 ? index : 0
})

const tips = [
  '标题尽量明确，让别人一眼知道你想表达什么。',
  '如果是组队招募，最好写清目标、时间安排和你需要的人。',
  '如果是恋爱匹配资料，真实自然比“包装得很满”更容易建立信任。',
]

onShow(() => {
  if (hasToken.value && profileComplete.value && activeMode.value === 'dating') {
    void ensureDatingLoaded()
  }
})

async function switchMode(mode: PublishMode) {
  activeMode.value = mode
  clearErrors()
  if (mode === 'dating' && hasToken.value && profileComplete.value) {
    await ensureDatingLoaded()
  }
}

function clearErrors() {
  forumError.value = ''
  teamError.value = ''
  datingError.value = ''
}

function handleForumCategoryChange(event: { detail?: { value?: string | number } }) {
  forumForm.category = forumCategories[Number(event.detail?.value ?? 0)] ?? ''
}

async function submitForumPost() {
  forumError.value = ''

  if (forumForm.title.trim().length < 4) {
    forumError.value = '标题至少需要 4 个字'
    return
  }
  if (!forumForm.category.trim()) {
    forumError.value = '请选择帖子分类'
    return
  }
  if (forumForm.body.trim().length < 10) {
    forumError.value = '正文至少需要 10 个字'
    return
  }

  forumSubmitting.value = true
  try {
    const post = await createForumPost({
      title: forumForm.title.trim(),
      body: forumForm.body.trim(),
      category: forumForm.category.trim(),
      tags: splitList(forumForm.tagsText),
    })
    forumForm.title = ''
    forumForm.category = ''
    forumForm.body = ''
    forumForm.tagsText = ''
    showToast('帖子发布成功', 'success')
    navigateTo(`/pages/forum/detail?id=${post.id}`)
  } catch (error) {
    forumError.value = error instanceof Error ? error.message : '发帖失败'
  } finally {
    forumSubmitting.value = false
  }
}

async function submitTeamPost() {
  teamError.value = ''
  const targetSize = Number(teamForm.targetSize)

  if (teamForm.title.trim().length < 4) {
    teamError.value = '标题至少需要 4 个字'
    return
  }
  if (teamForm.summary.trim().length < 8) {
    teamError.value = '一句话概述至少需要 8 个字'
    return
  }
  if (teamForm.details.trim().length < 20) {
    teamError.value = '详细说明至少需要 20 个字'
    return
  }
  if (!Number.isInteger(targetSize) || targetSize < 2 || targetSize > 20) {
    teamError.value = '目标人数需要在 2 到 20 之间'
    return
  }

  teamSubmitting.value = true
  try {
    await createTeammatePost({
      title: teamForm.title.trim(),
      summary: teamForm.summary.trim(),
      details: teamForm.details.trim(),
      target_size: targetSize,
      tags: splitList(teamForm.tagsText),
      required_skills: splitList(teamForm.skillsText),
    })
    teamForm.title = ''
    teamForm.summary = ''
    teamForm.details = ''
    teamForm.targetSize = '3'
    teamForm.tagsText = ''
    teamForm.skillsText = ''
    showToast('组队招募发布成功', 'success')
    navigateTo('/pages/teammates/index')
  } catch (error) {
    teamError.value = error instanceof Error ? error.message : '发布组队失败'
  } finally {
    teamSubmitting.value = false
  }
}

async function ensureDatingLoaded() {
  if (datingLoading.value || (datingProfileLoaded.value && datingPreferenceLoaded.value)) {
    return
  }

  datingLoading.value = true
  datingError.value = ''
  try {
    const [profile, preference] = await Promise.all([fetchDatingProfile(), fetchDatingPreference()])
    applyDatingProfile(profile)
    applyDatingPreference(preference)
    datingProfileLoaded.value = true
    datingPreferenceLoaded.value = true
  } catch (error) {
    datingError.value = error instanceof Error ? error.message : '读取恋爱匹配资料失败'
  } finally {
    datingLoading.value = false
  }
}

function applyDatingProfile(profile: DatingProfile) {
  datingForm.nickname = profile.nickname ?? ''
  datingForm.gender = profile.gender ?? 'unknown'
  datingForm.heightCm = profile.height_cm ? String(profile.height_cm) : ''
  datingForm.interestsText = (profile.interests ?? []).join(', ')
  datingForm.personalityType = profile.personality_type ?? ''
  datingForm.bio = profile.bio ?? ''
  datingForm.isVisible = profile.is_visible
}

function applyDatingPreference(preference: DatingPreference) {
  datingForm.preferredGendersText = (preference.preferred_genders ?? []).join(', ')
  datingForm.preferredInterestsText = (preference.preferred_interests ?? []).join(', ')
  datingForm.preferredTypesText = (preference.preferred_personality_types ?? []).join(', ')
}

async function submitDatingProfile() {
  datingError.value = ''
  await ensureDatingLoaded()

  if (!datingForm.nickname.trim()) {
    datingError.value = '请填写展示昵称'
    return
  }
  if (datingForm.bio.trim().length < 10) {
    datingError.value = '自我介绍至少需要 10 个字'
    return
  }

  datingSubmitting.value = true
  try {
    await Promise.all([
      updateDatingProfile({
        nickname: datingForm.nickname.trim(),
        gender: datingForm.gender,
        height_cm: datingForm.heightCm ? Number(datingForm.heightCm) : null,
        interests: splitList(datingForm.interestsText),
        personality_type: datingForm.personalityType.trim(),
        bio: datingForm.bio.trim(),
        is_visible: datingForm.isVisible,
      }),
      updateDatingPreference({
        preferred_genders: splitList(datingForm.preferredGendersText) as DatingPreference['preferred_genders'],
        min_height_cm: null,
        max_height_cm: null,
        preferred_interests: splitList(datingForm.preferredInterestsText),
        preferred_personality_types: splitList(datingForm.preferredTypesText),
      }),
    ])
    showToast(datingForm.isVisible ? '恋爱匹配资料已公开' : '恋爱匹配资料已保存', 'success')
    navigateTo('/pages/dating/index')
  } catch (error) {
    datingError.value = error instanceof Error ? error.message : '保存恋爱匹配资料失败'
  } finally {
    datingSubmitting.value = false
  }
}

function handleDatingGenderChange(event: { detail?: { value?: string | number } }) {
  datingForm.gender = (genderOptions[Number(event.detail?.value ?? 0)] ?? 'unknown') as DatingProfile['gender']
}

function handleVisibleChange(event: { detail?: { value?: boolean } }) {
  datingForm.isVisible = Boolean(event.detail?.value)
}

function splitList(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
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

function goLogin() {
  redirectToLogin('/pages/publish/index')
}

function goProfile() {
  navigateTo('/pages/profile/index')
}

function goForumCreate() {
  navigateTo('/pages/forum/create')
}

function goDating() {
  navigateTo('/pages/dating/index')
}
</script>

<style scoped lang="scss">
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

.status-chip.complete {
  background: rgba(77, 166, 106, 0.18);
  color: #2e7d49;
}

.mode-scroll {
  width: 100%;
  white-space: nowrap;
}

.mode-row {
  display: inline-flex;
  gap: 16rpx;
}

.mode-chip {
  min-height: 70rpx;
  padding: 0 26rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.86);
  border: 1rpx solid rgba(16, 33, 51, 0.1);
  color: #102133;
  font-size: 24rpx;
  font-weight: 700;
}

.mode-chip::after {
  border: 0;
}

.mode-chip.active {
  background: rgba(241, 107, 79, 0.14);
  border-color: rgba(241, 107, 79, 0.22);
  color: #f16b4f;
}

.mode-summary {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16rpx;
}

.mode-badge {
  flex-shrink: 0;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(241, 107, 79, 0.12);
  color: #f16b4f;
  font-size: 22rpx;
  font-weight: 700;
}

.toggle-field {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.compact-action {
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  padding: 20rpx;
  border-radius: 24rpx;
  background: rgba(241, 107, 79, 0.08);
}

.compact-action > view {
  flex: 1;
  min-width: 0;
}

.tips-card {
  margin-bottom: 16rpx;
}

.tips-list {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}
</style>
