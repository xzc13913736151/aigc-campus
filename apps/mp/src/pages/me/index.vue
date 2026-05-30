<template>
  <view class="container">
    <view class="card hero-card">
      <view class="hero-head">
        <view class="avatar-wrap">
          <view v-if="avatarUrl" class="avatar">
            <CachedImage :src="avatarUrl" mode="aspectFill" />
          </view>
          <view v-else class="avatar avatar-placeholder">
            <text>{{ displayInitial }}</text>
          </view>
        </view>
        <view class="hero-copy">
          <text class="section-title">{{ displayName }}</text>
          <text class="helper">{{ helperText }}</text>
          <view v-if="hasToken" style="height: 10rpx" />
          <text v-if="hasToken && profile.major" class="helper">{{ profile.grade || '未填写年级' }} · {{ profile.major }}</text>
        </view>
      </view>

      <view style="height: 24rpx" />

      <view class="status-row">
        <view class="status-chip">
          <text>{{ hasToken ? '已登录' : '未登录' }}</text>
        </view>
        <view v-if="hasToken && profile.claw_id" class="status-chip claw-chip" @tap="copyClawId">
          <text>Claw ID：{{ profile.claw_id }}</text>
        </view>
        <view class="status-chip" :class="{ complete: profileComplete }">
          <text>{{ profileComplete ? '资料已完善' : '待补全资料' }}</text>
        </view>
        <view v-if="isAdmin" class="status-chip admin-chip">
          <text>管理员</text>
        </view>
      </view>

      <view v-if="hasToken && profile.headline" style="height: 20rpx" />
      <text v-if="hasToken && profile.headline" class="section-desc">{{ profile.headline }}</text>
    </view>

    <view class="grid summary-grid">
      <view class="card summary-card">
        <text class="summary-value">{{ hasToken ? completionPercent : '0%' }}</text>
        <view style="height: 8rpx" />
        <text class="section-desc">资料完整度</text>
      </view>
      <view class="card summary-card">
        <text class="summary-value">{{ hasToken ? forumCount : 0 }}</text>
        <view style="height: 8rpx" />
        <text class="section-desc">我的帖子</text>
      </view>
      <view class="card summary-card">
        <text class="summary-value">{{ hasToken ? teamCount : 0 }}</text>
        <view style="height: 8rpx" />
        <text class="section-desc">我的组队</text>
      </view>
    </view>

    <view v-if="!hasToken" class="card empty">
      <text class="section-desc">登录后可以查看个人资料、发布记录、黑名单和更多个人管理能力。</text>
      <view style="height: 24rpx" />
      <button class="btn btn-primary" @tap="goLogin">去登录</button>
    </view>

    <template v-else>
      <view class="card section">
        <text class="section-title">个人资料</text>
        <view style="height: 10rpx" />
        <text class="section-desc">这里展示你当前对外可见的基础信息，也是论坛、组队和匹配页的主要身份来源。</text>
        <view style="height: 20rpx" />

        <view class="profile-grid">
          <view class="profile-item">
            <text class="profile-label">Claw ID</text>
            <text class="profile-value">{{ profile.claw_id || '未生成' }}</text>
          </view>
          <view class="profile-item">
            <text class="profile-label">昵称</text>
            <text class="profile-value">{{ profile.nickname || '未填写' }}</text>
          </view>
          <view class="profile-item">
            <text class="profile-label">性别</text>
            <text class="profile-value">{{ getGenderLabel(profile.gender) }}</text>
          </view>
          <view class="profile-item">
            <text class="profile-label">年级</text>
            <text class="profile-value">{{ profile.grade || '未填写' }}</text>
          </view>
          <view class="profile-item">
            <text class="profile-label">专业</text>
            <text class="profile-value">{{ profile.major || '未填写' }}</text>
          </view>
        </view>

        <view v-if="profile.bio" style="height: 18rpx" />
        <text v-if="profile.bio" class="section-desc">{{ profile.bio }}</text>

        <view v-if="profile.interests.length" style="height: 16rpx" />
        <view v-if="profile.interests.length" class="tag-row">
          <text v-for="tag in profile.interests" :key="tag" class="tag">{{ tag }}</text>
        </view>

        <view style="height: 20rpx" />
        <button class="btn btn-primary" @tap="goProfile">编辑个人资料</button>
      </view>

      <view class="card section">
        <text class="section-title">内容与关系管理</text>
        <view style="height: 10rpx" />
        <text class="section-desc">从这里快速进入你常用的个人管理区域。</text>
        <view style="height: 20rpx" />

        <view class="grid action-grid">
          <button class="btn btn-secondary" @tap="goProfile">完善资料</button>
          <button class="btn btn-ghost" @tap="goForum">查看我的帖子</button>
          <button class="btn btn-ghost" @tap="goBlocks">黑名单管理</button>
          <button class="btn btn-ghost" @tap="goAssistant">AI 助手</button>
          <button v-if="isAdmin" class="btn btn-secondary" @tap="goAdmin">管理后台</button>
        </view>
      </view>

      <view class="card section">
        <text class="section-title">我的概览</text>
        <view style="height: 10rpx" />
        <text class="section-desc">帮助你快速确认当前账号活跃情况和重要状态。</text>
        <view style="height: 20rpx" />

        <view class="grid overview-grid">
          <view class="overview-card">
            <text class="overview-title">论坛</text>
            <view style="height: 8rpx" />
            <text class="overview-value">{{ forumCount }} 条帖子</text>
          </view>
          <view class="overview-card">
            <text class="overview-title">组队</text>
            <view style="height: 8rpx" />
            <text class="overview-value">{{ teamCount }} 条招募</text>
          </view>
          <view class="overview-card">
            <text class="overview-title">黑名单</text>
            <view style="height: 8rpx" />
            <text class="overview-value">{{ blockCount }} 位用户</text>
          </view>
        </view>
      </view>

      <view class="card">
        <text class="section-title">账号操作</text>
        <view style="height: 10rpx" />
        <text class="section-desc">退出后会清理当前小程序登录态，需要重新微信登录才能继续使用。</text>
        <view style="height: 20rpx" />
        <button class="btn btn-primary" @tap="logout">退出登录</button>
      </view>
    </template>

    <BottomTabBar />
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import BottomTabBar from '../../components/BottomTabBar.vue'
import CachedImage from '../../components/CachedImage.vue'
import { fetchForumPosts, fetchMyForumPosts } from '../../services/forum'
import { fetchMyBlocks } from '../../services/moderation'
import { fetchMyProfile } from '../../services/profile'
import { fetchMyTeammatePosts } from '../../services/teammates'
import { currentUser, ensureAuthenticated, isAuthenticated, logoutUser, redirectToLogin } from '../../utils/auth'
import { navigateTo } from '../../utils/navigation'
import { showToast } from '../../utils/ui'

const hasToken = computed(() => isAuthenticated.value)
const isAdmin = computed(() => currentUser.value?.role === 'admin')
const avatarUrl = ref('')
const profileComplete = ref(false)
const forumCount = ref(0)
const teamCount = ref(0)
const blockCount = ref(0)

const profile = reactive({
  claw_id: '',
  nickname: '',
  headline: '',
  bio: '',
  gender: '',
  major: '',
  grade: '',
  interests: [] as string[],
})

const completionPercent = computed(() => {
  const fields = [
    profile.nickname.trim(),
    profile.headline.trim(),
    profile.bio.trim(),
    profile.gender.trim(),
    profile.major.trim(),
    profile.grade.trim(),
    profile.interests.length ? 'yes' : '',
  ]
  const completed = fields.filter(Boolean).length
  return `${Math.round((completed / fields.length) * 100)}%`
})

const displayName = computed(() => {
  if (!hasToken.value) {
    return '未登录'
  }
  if (profile.nickname) {
    return profile.nickname
  }
  if (isAdmin.value) {
    return '管理员'
  }
  return currentUser.value?.email || '微信用户'
})

const displayInitial = computed(() => displayName.value.trim().slice(0, 1) || '我')

const helperText = computed(() => {
  if (!hasToken.value) {
    return '登录后可以同步头像昵称、完善资料，并进入你的个人中心。'
  }
  if (isAdmin.value) {
    return '当前账号拥有内容审核台权限，可直接处理举报和违规内容。'
  }
  return profileComplete.value
    ? '当前资料已经可以用于论坛、组队、匹配和聊天场景。'
    : '建议先把资料补完整，这样别人更容易认识你，也更愿意回应你。'
})

onShow(async () => {
  resetLocalState()
  if (!hasToken.value) {
    return
  }

  try {
    const [myProfile, myForumPosts, myTeamPosts, blocks] = await Promise.all([
      fetchMyProfile(),
      fetchMyForumPosts(),
      fetchMyTeammatePosts(),
      fetchMyBlocks(),
    ])

    avatarUrl.value = myProfile.avatar_url ?? ''
    profile.claw_id = myProfile.user?.claw_id ?? ''
    profile.nickname = myProfile.nickname ?? ''
    profile.headline = myProfile.headline ?? ''
    profile.bio = myProfile.bio ?? ''
    profile.gender = myProfile.gender ?? ''
    profile.major = myProfile.major ?? ''
    profile.grade = myProfile.grade ?? ''
    profile.interests = myProfile.interests ?? []
    profileComplete.value = isAdmin.value || Boolean(myProfile.headline.trim() && myProfile.major.trim() && myProfile.grade.trim())
    forumCount.value = myForumPosts.length
    teamCount.value = myTeamPosts.length
    blockCount.value = blocks.length
  } catch (error) {
    showToast(error instanceof Error ? error.message : '加载个人中心失败')
  }
})

function resetLocalState() {
  avatarUrl.value = ''
  profileComplete.value = false
  forumCount.value = 0
  teamCount.value = 0
  blockCount.value = 0
  profile.claw_id = ''
  profile.nickname = ''
  profile.headline = ''
  profile.bio = ''
  profile.gender = ''
  profile.major = ''
  profile.grade = ''
  profile.interests = []
}

function getGenderLabel(value: string) {
  const map: Record<string, string> = {
    male: '男',
    female: '女',
    other: '其他',
    unknown: '未说明',
  }
  return map[value] || value || '未填写'
}

function goLogin() {
  redirectToLogin('/pages/me/index')
}

function copyClawId() {
  if (!profile.claw_id) {
    return
  }
  uni.setClipboardData({
    data: profile.claw_id,
    success: () => showToast('Claw ID 已复制', 'success'),
  })
}

function goProfile() {
  if (hasToken.value && !ensureAuthenticated('/pages/profile/index')) {
    return
  }
  navigateTo('/pages/profile/index')
}

function goBlocks() {
  if (!hasToken.value) {
    redirectToLogin('/pages/blocks/index')
    return
  }
  if (!ensureAuthenticated('/pages/blocks/index')) {
    return
  }
  navigateTo('/pages/blocks/index')
}

function goForum() {
  uni.switchTab({ url: '/pages/forum/index' })
}

function goAssistant() {
  if (!hasToken.value) {
    redirectToLogin('/pages/assistant/index')
    return
  }
  if (!ensureAuthenticated('/pages/assistant/index')) {
    return
  }
  navigateTo('/pages/assistant/index')
}

function goAdmin() {
  if (!ensureAuthenticated('/pages/admin/index')) {
    return
  }
  navigateTo('/pages/admin/index')
}

async function logout() {
  await logoutUser()
  resetLocalState()
  showToast('已退出登录', 'success')
}
</script>

<style scoped lang="scss">
.hero-card {
  gap: 0;
}

.hero-head {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  flex: 1;
}

.avatar-wrap {
  flex-shrink: 0;
}

.avatar {
  width: 136rpx;
  height: 136rpx;
  border-radius: 50%;
  overflow: hidden;
  background: rgba(16, 33, 51, 0.08);
}

.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 46rpx;
  font-weight: 700;
  color: #f16b4f;
}

.status-row {
  display: flex;
  gap: 16rpx;
  flex-wrap: wrap;
}

.status-chip {
  padding: 12rpx 20rpx;
  border-radius: 999rpx;
  background: rgba(16, 33, 51, 0.08);
  color: #102133;
  font-size: 24rpx;
  font-weight: 600;
}

.status-chip.complete {
  background: rgba(77, 166, 106, 0.16);
  color: #2e7d49;
}

.claw-chip {
  background: rgba(241, 107, 79, 0.12);
  color: #f16b4f;
}

.admin-chip {
  background: rgba(16, 33, 51, 0.12);
  color: #102133;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20rpx;
}

.summary-card {
  text-align: center;
}

.summary-value {
  font-size: 34rpx;
  font-weight: 700;
  color: #102133;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20rpx;
}

.profile-item {
  padding: 20rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.7);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
}

.profile-label {
  display: block;
  font-size: 22rpx;
  color: #6b7280;
}

.profile-value {
  display: block;
  margin-top: 8rpx;
  font-size: 28rpx;
  color: #102133;
  font-weight: 600;
}

.action-grid,
.overview-grid {
  display: grid;
  gap: 20rpx;
}

.overview-card {
  padding: 22rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.74);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
}

.overview-title {
  font-size: 24rpx;
  color: #6b7280;
}

.overview-value {
  font-size: 30rpx;
  font-weight: 700;
  color: #102133;
}
</style>
