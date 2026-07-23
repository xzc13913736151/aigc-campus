<template>
  <view class="container">
    <AssistantSheet
      :visible="assistantVisible"
      page-type="publish"
      :context-path="`/pages/teammates/index?assistantTarget=${assistantTargetPostId}`"
      context-target-type="team_post"
      :context-target-id="assistantTargetPostId"
      @close="assistantVisible = false"
    />

    <view class="section hero">
      <text class="eyebrow">CampusClaw 组队匹配</text>
      <view style="height: 18rpx" />
      <text class="title">把目标和需求说清楚，更容易找到合适队友。</text>
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
          <text class="section-desc">先搜索你感兴趣的方向，再决定是加入别人，还是自己发起一条招募。下拉页面可以更新内容。</text>
        </view>
      </view>

      <view style="height: 20rpx" />

      <view class="field">
        <text class="label">搜索招募</text>
        <input
          v-model="query"
          class="input"
          type="text"
          placeholder="搜索项目方向、关键词或你想加入的团队"
          @confirm="searchPosts"
        />
      </view>

      <view style="height: 18rpx" />

      <view class="action-row">
        <button class="btn btn-secondary" :disabled="loadingList" @tap="searchPosts">
          {{ loadingList ? '搜索中...' : '搜索招募' }}
        </button>
        <button v-if="!hasToken" class="btn btn-primary" @tap="goLogin">去登录</button>
        <button v-else-if="!profileComplete" class="btn btn-primary" @tap="goProfile">完善资料</button>
        <button v-else class="btn btn-primary action-button" @tap="openComposer">
          <text class="action-button-text primary-button-text">发起组队</text>
        </button>
        <button class="btn btn-ghost action-button" @tap="focusMyPosts">
          <text class="action-button-text ghost-button-text">看我的招募</text>
        </button>
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
          <view style="height: 18rpx" />
          <view class="action-row">
            <button class="btn btn-secondary" @tap="editPost(post)">编辑</button>
            <button class="btn btn-ghost" :disabled="closingPostId === post.id" @tap="togglePostStatus(post)">
              {{ closingPostId === post.id ? '处理中...' : post.status === 'closed' ? '重新开放' : '关闭招募' }}
            </button>
            <button class="btn btn-ghost" :disabled="deletingPostId === post.id" @tap="handleDeletePost(post.id)">
              {{ deletingPostId === post.id ? '删除中...' : '删除' }}
            </button>
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
            <button class="btn btn-secondary" :disabled="reviewingId === application.id" @tap="handleReview(application.id, 'accepted')">
              {{ reviewingId === application.id ? '处理中...' : '通过' }}
            </button>
            <button class="btn btn-ghost" :disabled="reviewingId === application.id" @tap="handleReview(application.id, 'rejected')">
              {{ reviewingId === application.id ? '处理中...' : '拒绝' }}
            </button>
          </view>
        </view>
      </view>
    </view>

    <view class="section">
      <view class="result-head">
        <view>
          <text class="section-title">{{ query.trim() ? '搜索结果' : '最新招募' }}</text>
          <view style="height: 8rpx" />
          <text class="section-desc">
            {{ query.trim() ? `已为你找到 ${posts.length} 条相关招募` : `当前广场共有 ${posts.length} 条招募` }}
          </text>
        </view>
        <text v-if="loadingList" class="helper">加载中...</text>
      </view>
      <view style="height: 18rpx" />

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
          <view class="author-row">
            <text class="helper">发起人：{{ getPostAuthorName(post) }}</text>
            <button class="link-button" @tap="startChatToAuthor(post)">联系Ta</button>
          </view>
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

          <view v-if="canApply(post)" style="height: 14rpx" />
          <view v-if="canApply(post)" class="action-row compact-row">
            <button class="btn btn-ghost" @tap="openPostAssistant(post.id)">让 AI 帮我申请</button>
          </view>

          <view v-if="canApply(post)" style="height: 18rpx" />
          <view v-if="canApply(post)" class="apply-box">
            <textarea
              v-model="applyMessages[post.id]"
              class="textarea apply-textarea"
              placeholder="简单介绍一下你为什么适合加入，选填"
            />
            <button class="btn btn-primary" :disabled="applyingPostId === post.id" @tap="handleApply(post.id)">
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

  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'

import AssistantSheet from '../../components/assistant/AssistantSheet.vue'
import type { TeamApplication, TeamPost } from '../../types/api'
import { currentUser, ensureAuthenticated, isAuthenticated, profileOnboarded, redirectToLogin } from '../../utils/auth'
import {
  applyToTeammatePost,
  deleteTeammatePost,
  fetchMyTeammatePosts,
  fetchMyTeammateApplications,
  fetchReceivedTeammateApplications,
  fetchTeammatePosts,
  reviewTeammateApplication,
  updateTeammatePost,
} from '../../services/teammates'
import { navigateTo } from '../../utils/navigation'
import { showToast } from '../../utils/ui'

const hasToken = ref(isAuthenticated.value)
const profileComplete = computed(() => profileOnboarded.value)
const query = ref('')
const assistantVisible = ref(false)
const assistantTargetPostId = ref('')
const loadingList = ref(false)
const applyingPostId = ref('')
const reviewingId = ref('')
const closingPostId = ref('')
const deletingPostId = ref('')
const pageError = ref('')
const posts = ref<TeamPost[]>([])
const myPosts = ref<TeamPost[]>([])
const myApplications = ref<TeamApplication[]>([])
const receivedApplications = ref<TeamApplication[]>([])

const applyMessages = reactive<Record<string, string>>({})

const pendingReceivedCount = computed(() => receivedApplications.value.filter((application) => application.status === 'pending').length)

onMounted(() => {
  refreshAll()
})

onShow(() => {
  hasToken.value = isAuthenticated.value
  refreshAll()
})

onPullDownRefresh(async () => {
  await refreshAll()
  uni.stopPullDownRefresh()
})

async function refreshAll() {
  loadingList.value = true
  pageError.value = ''

  try {
    posts.value = await fetchTeammatePosts(query.value)
    if (hasToken.value) {
      const [ownPosts, mine, received] = await Promise.all([
        fetchMyTeammatePosts(),
        fetchMyTeammateApplications(),
        fetchReceivedTeammateApplications(),
      ])
      myPosts.value = ownPosts
      myApplications.value = mine
      receivedApplications.value = received
    } else {
      myPosts.value = []
      myApplications.value = []
      receivedApplications.value = []
    }
  } catch (error) {
    pageError.value = error instanceof Error ? error.message : '加载组队数据失败'
  } finally {
    loadingList.value = false
  }
}

function searchPosts() {
  void refreshAll()
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
  if (getOpenSeats(post) <= 0) {
    return false
  }
  return !myApplications.value.some((application) => application.post.id === post.id)
}

function openComposer() {
  if (!ensureAuthenticated('/pages/teammates/index')) {
    return
  }
  navigateTo('/pages/teammates/create')
}

function openPostAssistant(postId: string) {
  if (!ensureAuthenticated('/pages/teammates/index')) {
    return
  }
  assistantTargetPostId.value = postId
  assistantVisible.value = true
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

function editPost(post: TeamPost) {
  navigateTo(`/pages/teammates/create?id=${post.id}`)
}

async function togglePostStatus(post: TeamPost) {
  closingPostId.value = post.id
  try {
    await updateTeammatePost(post.id, { status: post.status === 'closed' ? 'open' : 'closed' })
    showToast(post.status === 'closed' ? '招募已重新开放' : '招募已关闭', 'success')
    await refreshAll()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '更新招募状态失败')
  } finally {
    closingPostId.value = ''
  }
}

async function handleDeletePost(postId: string) {
  deletingPostId.value = postId
  try {
    await deleteTeammatePost(postId)
    showToast('招募已删除', 'success')
    await refreshAll()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '删除招募失败')
  } finally {
    deletingPostId.value = ''
  }
}

function goLogin() {
  redirectToLogin('/pages/teammates/index')
}

function goProfile() {
  navigateTo('/pages/profile/index')
}

function startChatToAuthor(post: TeamPost) {
  if (!ensureAuthenticated(`/pages/chat/index?targetUserId=${post.author.id}`)) {
    return
  }
  if (!post.author.id) {
    showToast('暂时无法联系该发起人')
    return
  }
  if (post.author.id === currentUser.value?.id) {
    showToast('这是你自己发起的招募')
    return
  }
  navigateTo(`/pages/chat/index?targetUserId=${post.author.id}&sourceType=team_post&sourceId=${post.id}`)
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
  color: #2f2a24;
  font-size: 24rpx;
  font-weight: 600;
}

.status-chip.active {
  background: rgba(241, 107, 79, 0.14);
  color: #c15f3c;
}

.status-chip.complete {
  background: rgba(77, 166, 106, 0.18);
  color: #557a5d;
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
  color: #2f2a24;
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

.result-head,
.author-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16rpx;
}

.link-button {
  flex-shrink: 0;
  min-height: 52rpx;
  padding: 0 20rpx;
  margin: 0;
  border: 0;
  border-radius: 999rpx;
  background: rgba(241, 107, 79, 0.12);
  color: #c15f3c;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.link-button::after {
  border: 0;
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
  color: #c15f3c;
  font-size: 22rpx;
  font-weight: 700;
}

.skill-tag {
  padding: 10rpx 20rpx;
  border-radius: 999rpx;
  background: rgba(16, 33, 51, 0.08);
  font-size: 22rpx;
  color: #2f2a24;
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
  color: #557a5d;
}

.tag.rejected {
  background: rgba(220, 38, 38, 0.12);
  color: #b75347;
}

.tag.pending {
  background: rgba(241, 107, 79, 0.12);
  color: #c15f3c;
}
</style>
