<template>
  <view class="container">
    <view class="section hero">
      <text class="eyebrow">CampusClaw Teaming</text>
      <view style="height: 18rpx" />
      <text class="title">把“想做什么”和“需要谁”说清楚，更容易找到合适队友。</text>
      <view style="height: 18rpx" />
      <text class="subtitle">
        这里适合发布项目招募、比赛组队、活动搭子和学习协作需求。先看广场，再决定要不要发起自己的招募。
      </text>
      <view style="height: 24rpx" />

      <view class="status-row">
        <view class="status-chip" :class="{ active: hasToken }">
          <text>{{ hasToken ? '已登录' : '未登录' }}</text>
        </view>
        <view class="status-chip" :class="{ complete: profileComplete }">
          <text>{{ hasToken ? (profileComplete ? '可以发起与申请' : '请先完善资料') : '登录后可操作' }}</text>
        </view>
      </view>
    </view>

    <view class="grid stats-grid section">
      <view class="card stat-card">
        <text class="stat-value">{{ posts.length }}</text>
        <view style="height: 8rpx" />
        <text class="section-desc">广场招募</text>
      </view>
      <view class="card stat-card">
        <text class="stat-value">{{ myPosts.length }}</text>
        <view style="height: 8rpx" />
        <text class="section-desc">我发起的</text>
      </view>
      <view class="card stat-card">
        <text class="stat-value">{{ pendingReceivedCount }}</text>
        <view style="height: 8rpx" />
        <text class="section-desc">待审核申请</text>
      </view>
    </view>

    <view class="card section">
      <view class="section-head">
        <view>
          <text class="section-title">组队广场</text>
          <view style="height: 8rpx" />
          <text class="section-desc">先搜索你感兴趣的方向，再决定是加入别人，还是自己发起一条招募。</text>
        </view>
        <button class="btn btn-ghost" size="mini" :disabled="loadingList" @tap="refreshAll">
          {{ loadingList ? '刷新中...' : '刷新广场' }}
        </button>
      </view>

      <view style="height: 20rpx" />

      <view class="field">
        <text class="label">搜索招募</text>
        <input
          v-model="query"
          class="input"
          type="text"
          placeholder="搜索项目方向、关键词或你想加入的团队"
          @confirm="refreshAll"
        />
      </view>

      <view style="height: 18rpx" />

      <view class="action-row">
        <button v-if="!hasToken" class="btn btn-primary" @tap="goLogin">去登录</button>
        <button v-else-if="!profileComplete" class="btn btn-primary" @tap="goProfile">完善资料</button>
        <button v-else class="btn btn-primary" @tap="scrollToComposer">发起组队</button>
        <button class="btn btn-ghost" @tap="focusMyPosts">看我的招募</button>
      </view>

      <view v-if="pageError" style="height: 14rpx" />
      <text v-if="pageError" class="error">{{ pageError }}</text>
    </view>

    <view v-if="hasToken && myPosts.length" id="my-posts" class="card section">
      <text class="section-title">我的招募</text>
      <view style="height: 10rpx" />
      <text class="section-desc">这些是你发起过的组队招募，方便你快速确认当前进展。</text>
      <view style="height: 20rpx" />

      <view class="grid">
        <view v-for="post in myPosts" :key="post.id" class="my-post-card">
          <view class="team-head">
            <view style="flex: 1">
              <text class="section-title team-title">{{ post.title }}</text>
              <view style="height: 8rpx" />
              <text class="section-desc">{{ post.summary }}</text>
            </view>
            <text class="tag">{{ getStatusText(post.status) }}</text>
          </view>
          <view style="height: 12rpx" />
          <view class="meta-row">
            <text class="helper">人数 {{ post.current_size }} / {{ post.target_size }}</text>
            <text class="helper">还差 {{ getOpenSeats(post) }} 人</text>
          </view>
          <view v-if="post.required_skills.length" style="height: 14rpx" />
          <view v-if="post.required_skills.length" class="tag-row">
            <text v-for="skill in post.required_skills" :key="skill" class="skill-tag">{{ skill }}</text>
          </view>
        </view>
      </view>
    </view>

    <view v-if="hasToken && myApplications.length" class="card section">
      <text class="section-title">我的申请</text>
      <view style="height: 10rpx" />
      <text class="section-desc">这里会显示你申请加入过哪些团队，以及目前处理到了哪一步。</text>
      <view style="height: 20rpx" />

      <view class="grid">
        <view v-for="application in myApplications" :key="application.id" class="application-card">
          <view class="team-head">
            <view style="flex: 1">
              <text class="section-title application-title">{{ application.post.title }}</text>
              <view style="height: 8rpx" />
              <text class="helper">发起人：{{ getPostAuthorName(application.post) }}</text>
            </view>
            <text class="tag" :class="statusTagClass(application.status)">{{ getApplicationStatusText(application.status) }}</text>
          </view>
          <view style="height: 12rpx" />
          <text class="section-desc">{{ application.message || '你没有填写额外申请留言。' }}</text>
        </view>
      </view>
    </view>

    <view v-if="hasToken && receivedApplications.length" class="card section">
      <text class="section-title">收到的申请</text>
      <view style="height: 10rpx" />
      <text class="section-desc">别人申请加入你的招募时，会出现在这里。你可以直接通过或拒绝。</text>
      <view style="height: 20rpx" />

      <view class="grid">
        <view v-for="application in receivedApplications" :key="application.id" class="application-card">
          <view class="team-head">
            <view style="flex: 1">
              <text class="section-title application-title">{{ application.post.title }}</text>
              <view style="height: 8rpx" />
              <text class="helper">申请人：{{ getApplicantName(application) }}</text>
            </view>
            <text class="tag" :class="statusTagClass(application.status)">{{ getApplicationStatusText(application.status) }}</text>
          </view>
          <view style="height: 12rpx" />
          <text class="section-desc">{{ application.message || '对方没有填写申请留言。' }}</text>
          <view v-if="application.status === 'pending'" style="height: 18rpx" />
          <view v-if="application.status === 'pending'" class="action-row">
            <button class="btn btn-secondary" size="mini" :disabled="reviewingId === application.id" @tap="handleReview(application.id, 'accepted')">
              {{ reviewingId === application.id ? '处理中...' : '通过' }}
            </button>
            <button class="btn btn-ghost" size="mini" :disabled="reviewingId === application.id" @tap="handleReview(application.id, 'rejected')">
              {{ reviewingId === application.id ? '处理中...' : '拒绝' }}
            </button>
          </view>
        </view>
      </view>
    </view>

    <view class="section">
      <view v-if="posts.length" class="grid">
        <view v-for="post in posts" :key="post.id" class="card team-card">
          <view class="team-head">
            <view style="flex: 1">
              <text class="section-title team-title">{{ post.title }}</text>
              <view style="height: 8rpx" />
              <text class="section-desc">{{ post.summary }}</text>
            </view>
            <view class="capacity-pill">{{ post.current_size }} / {{ post.target_size }}</view>
          </view>

          <view style="height: 14rpx" />
          <text class="helper">发起人：{{ getPostAuthorName(post) }}</text>
          <view style="height: 12rpx" />
          <text class="section-desc">{{ post.details }}</text>

          <view v-if="post.tags.length" style="height: 16rpx" />
          <view v-if="post.tags.length" class="tag-row">
            <text v-for="tag in post.tags" :key="tag" class="tag">#{{ tag }}</text>
          </view>

          <view v-if="post.required_skills.length" style="height: 12rpx" />
          <view v-if="post.required_skills.length" class="tag-row">
            <text v-for="skill in post.required_skills" :key="skill" class="skill-tag">需要：{{ skill }}</text>
          </view>

          <view style="height: 18rpx" />
          <text class="helper">当前状态：{{ getStatusText(post.status) }}</text>

          <view v-if="canApply(post)" style="height: 18rpx" />
          <view v-if="canApply(post)" class="apply-box">
            <textarea
              v-model="applyMessages[post.id]"
              class="textarea apply-textarea"
              placeholder="简单介绍一下你为什么适合加入，选填"
            />
            <button class="btn btn-primary" size="mini" :disabled="applyingPostId === post.id" @tap="handleApply(post.id)">
              {{ applyingPostId === post.id ? '申请中...' : '申请加入' }}
            </button>
          </view>
        </view>
      </view>

      <view v-else class="card empty">
        <text class="section-title">暂时还没有组队信息</text>
        <view style="height: 8rpx" />
        <text class="section-desc">可以先发布第一条招募，把项目方向、需要的人和合作方式写清楚。</text>
      </view>
    </view>

    <view id="composer" class="card">
      <text class="section-title">发起一条组队招募</text>
      <view style="height: 8rpx" />
      <text class="section-desc">适合发布项目组队、比赛招募、学习搭子或活动合作。写得越清楚，越容易遇到合适的人。</text>
      <view style="height: 24rpx" />

      <view v-if="!hasToken" class="empty">
        <text class="section-desc">发布组队前需要先完成微信登录。</text>
        <view style="height: 24rpx" />
        <button class="btn btn-primary" @tap="goLogin">去登录</button>
      </view>

      <view v-else-if="!profileComplete" class="empty">
        <text class="section-desc">请先补全个人资料，方便别人判断你是谁、适合做什么，以及怎么联系你。</text>
        <view style="height: 24rpx" />
        <button class="btn btn-primary" @tap="goProfile">完善资料</button>
      </view>

      <view v-else class="form">
        <view class="field">
          <text class="label">招募标题</text>
          <input v-model="form.title" class="input" type="text" placeholder="例如：找 2 位同学一起做 AI 校园工具项目" />
        </view>
        <view class="field">
          <text class="label">一句话概述</text>
          <input v-model="form.summary" class="input" type="text" placeholder="说明项目方向、节奏，以及你最想找什么样的人" />
        </view>
        <view class="field">
          <text class="label">详细说明</text>
          <textarea v-model="form.details" class="textarea" placeholder="写清背景、目标、分工、时间安排和合作预期" />
        </view>
        <view class="field">
          <text class="label">目标人数</text>
          <input v-model="form.target_size" class="input" type="number" placeholder="2 - 20" />
        </view>
        <view class="field">
          <text class="label">项目标签</text>
          <input v-model="form.tagsText" class="input" type="text" placeholder="AI, 产品, 比赛, 校园活动" />
          <text class="helper">多个标签请用英文逗号分隔。</text>
        </view>
        <view class="field">
          <text class="label">需要的技能</text>
          <input v-model="form.skillsText" class="input" type="text" placeholder="前端, 后端, 设计, 文案" />
          <text class="helper">多个技能请用英文逗号分隔。</text>
        </view>
        <text v-if="composerError" class="error">{{ composerError }}</text>
        <button class="btn btn-primary" :disabled="submitting" @tap="handleSubmit">
          {{ submitting ? '发布中...' : '发布组队' }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import type { TeamApplication, TeamPost } from '../../types/api'
import { currentUser, ensureAuthenticated, isAuthenticated, profileOnboarded, redirectToLogin } from '../../utils/auth'
import {
  applyToTeammatePost,
  createTeammatePost,
  fetchMyTeammateApplications,
  fetchReceivedTeammateApplications,
  fetchTeammatePosts,
  reviewTeammateApplication,
} from '../../services/teammates'
import { navigateTo } from '../../utils/navigation'
import { showToast } from '../../utils/ui'

const hasToken = ref(isAuthenticated.value)
const profileComplete = computed(() => profileOnboarded.value)
const query = ref('')
const loadingList = ref(false)
const submitting = ref(false)
const applyingPostId = ref('')
const reviewingId = ref('')
const pageError = ref('')
const composerError = ref('')
const posts = ref<TeamPost[]>([])
const myApplications = ref<TeamApplication[]>([])
const receivedApplications = ref<TeamApplication[]>([])

const form = reactive({
  title: '',
  summary: '',
  details: '',
  target_size: '3',
  tagsText: '',
  skillsText: '',
})

const applyMessages = reactive<Record<string, string>>({})

const myPosts = computed(() => {
  const email = currentUser.value?.email ?? ''
  if (!email) {
    return []
  }
  return posts.value.filter((post) => post.author.email === email)
})

const pendingReceivedCount = computed(() => receivedApplications.value.filter((application) => application.status === 'pending').length)

onMounted(() => {
  refreshAll()
})

onShow(() => {
  hasToken.value = isAuthenticated.value
  refreshAll()
})

async function refreshAll() {
  loadingList.value = true
  pageError.value = ''

  try {
    posts.value = await fetchTeammatePosts(query.value)
    if (hasToken.value) {
      const [mine, received] = await Promise.all([
        fetchMyTeammateApplications(),
        fetchReceivedTeammateApplications(),
      ])
      myApplications.value = mine
      receivedApplications.value = received
    } else {
      myApplications.value = []
      receivedApplications.value = []
    }
  } catch (error) {
    pageError.value = error instanceof Error ? error.message : '加载组队数据失败'
  } finally {
    loadingList.value = false
  }
}

function getPostAuthorName(post: TeamPost) {
  return post.author.nickname || post.author.full_name || post.author.email
}

function getApplicantName(application: TeamApplication) {
  return application.applicant.nickname || application.applicant.full_name || application.applicant.email
}

function getOpenSeats(post: TeamPost) {
  return Math.max(post.target_size - post.current_size, 0)
}

function getStatusText(status: TeamPost['status']) {
  if (status === 'filled') {
    return '已招满'
  }
  if (status === 'closed') {
    return '已关闭'
  }
  return '招募中'
}

function getApplicationStatusText(status: TeamApplication['status']) {
  if (status === 'accepted') {
    return '已通过'
  }
  if (status === 'rejected') {
    return '已拒绝'
  }
  if (status === 'withdrawn') {
    return '已撤回'
  }
  return '待处理'
}

function statusTagClass(status: TeamApplication['status']) {
  return {
    accepted: status === 'accepted',
    rejected: status === 'rejected',
    pending: status === 'pending',
  }
}

function canApply(post: TeamPost) {
  if (!hasToken.value || !profileComplete.value) {
    return false
  }
  if (post.author.email === (currentUser.value?.email ?? '')) {
    return false
  }
  if (post.status !== 'open') {
    return false
  }
  return !myApplications.value.some((application) => application.post.id === post.id)
}

function scrollToComposer() {
  uni.pageScrollTo({
    selector: '#composer',
    duration: 280,
  })
}

function focusMyPosts() {
  uni.pageScrollTo({
    selector: '#my-posts',
    duration: 280,
  })
}

async function handleApply(postId: string) {
  if (!ensureAuthenticated('/pages/teammates/index')) {
    return
  }

  applyingPostId.value = postId
  try {
    await applyToTeammatePost(postId, {
      message: (applyMessages[postId] ?? '').trim(),
    })
    applyMessages[postId] = ''
    showToast('申请已提交', 'success')
    await refreshAll()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '申请失败')
  } finally {
    applyingPostId.value = ''
  }
}

async function handleReview(applicationId: string, status: 'accepted' | 'rejected') {
  reviewingId.value = applicationId
  try {
    await reviewTeammateApplication(applicationId, { status })
    showToast(status === 'accepted' ? '已通过申请' : '已拒绝申请', 'success')
    await refreshAll()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '审核失败')
  } finally {
    reviewingId.value = ''
  }
}

async function handleSubmit() {
  composerError.value = ''

  const targetSize = Number(form.target_size)
  if (form.title.trim().length < 4) {
    composerError.value = '标题至少需要 4 个字'
    return
  }
  if (form.summary.trim().length < 8) {
    composerError.value = '一句话概述至少需要 8 个字'
    return
  }
  if (form.details.trim().length < 20) {
    composerError.value = '详细说明至少需要 20 个字'
    return
  }
  if (!Number.isInteger(targetSize) || targetSize < 2 || targetSize > 20) {
    composerError.value = '目标人数需要在 2 到 20 之间'
    return
  }
  if (!ensureAuthenticated('/pages/teammates/index')) {
    return
  }

  submitting.value = true
  try {
    await createTeammatePost({
      title: form.title.trim(),
      summary: form.summary.trim(),
      details: form.details.trim(),
      target_size: targetSize,
      tags: form.tagsText
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean),
      required_skills: form.skillsText
        .split(',')
        .map((skill) => skill.trim())
        .filter(Boolean),
    })

    form.title = ''
    form.summary = ''
    form.details = ''
    form.target_size = '3'
    form.tagsText = ''
    form.skillsText = ''

    showToast('组队发布成功', 'success')
    await refreshAll()
    uni.pageScrollTo({ scrollTop: 0, duration: 200 })
  } catch (error) {
    composerError.value = error instanceof Error ? error.message : '发布组队失败'
  } finally {
    submitting.value = false
  }
}

function goLogin() {
  redirectToLogin('/pages/teammates/index')
}

function goProfile() {
  navigateTo('/pages/profile/index')
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
.team-head,
.meta-row,
.action-row {
  display: flex;
  gap: 16rpx;
  flex-wrap: wrap;
}

.section-head,
.team-head {
  justify-content: space-between;
  align-items: flex-start;
}

.team-title,
.application-title {
  margin-bottom: 0;
  font-size: 32rpx;
}

.team-card,
.my-post-card,
.application-card {
  display: flex;
  flex-direction: column;
}

.my-post-card {
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(241, 107, 79, 0.08);
  border: 1rpx solid rgba(241, 107, 79, 0.12);
}

.application-card {
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.76);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
}

.capacity-pill {
  flex-shrink: 0;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(241, 107, 79, 0.12);
  color: #f16b4f;
  font-size: 22rpx;
  font-weight: 700;
}

.skill-tag {
  padding: 10rpx 20rpx;
  border-radius: 999rpx;
  background: rgba(16, 33, 51, 0.08);
  font-size: 22rpx;
  color: #102133;
}

.apply-box {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.apply-textarea {
  min-height: 120rpx;
}

.tag.accepted {
  background: rgba(77, 166, 106, 0.18);
  color: #2e7d49;
}

.tag.rejected {
  background: rgba(220, 38, 38, 0.12);
  color: #dc2626;
}

.tag.pending {
  background: rgba(241, 107, 79, 0.12);
  color: #f16b4f;
}
</style>
