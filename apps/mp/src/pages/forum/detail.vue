<template>
  <view class="container">
    <view v-if="loading" class="card empty">
      <text class="section-desc">帖子详情加载中...</text>
    </view>

    <view v-else-if="post" class="section">
      <view class="card section">
        <text class="eyebrow">Forum Detail</text>
        <view style="height: 18rpx" />
        <text class="section-title">{{ post.title }}</text>
        <view style="height: 12rpx" />
        <view class="meta-row">
          <text class="helper">{{ getAuthorName(post.author) }}</text>
          <text class="helper">{{ formatDate(post.created_at) }}</text>
        </view>
        <view style="height: 16rpx" />
        <text class="section-desc">{{ post.summary || '这条帖子没有单独摘要，下面直接展示正文。' }}</text>
        <view style="height: 16rpx" />
        <text class="body-text">{{ post.body }}</text>
        <view style="height: 18rpx" />
        <view class="tag-row">
          <text class="tag">{{ post.category || '未分类' }}</text>
          <text v-for="tag in post.tags" :key="tag" class="tag">#{{ tag }}</text>
        </view>
        <view v-if="post.image_urls.length" style="height: 18rpx" />
        <view v-if="post.image_urls.length" class="detail-image-grid">
          <image
            v-for="url in post.image_urls"
            :key="url"
            class="detail-image"
            :src="url"
            mode="aspectFill"
            @tap="previewImages(post.image_urls, url)"
          />
        </view>
        <view style="height: 18rpx" />
        <view class="stat-row">
          <text class="helper">点赞 {{ post.like_count }}</text>
          <text class="helper">评论 {{ post.comment_count }}</text>
        </view>
        <view style="height: 20rpx" />
        <view class="action-row">
          <button class="btn btn-ghost" size="mini" :disabled="liking" @tap="handleLike">
            {{ post.is_liked ? `已点赞 ${post.like_count}` : `点赞 ${post.like_count}` }}
          </button>
          <button v-if="!isAuthor" class="btn btn-ghost" size="mini" @tap="handleReportPost">举报帖子</button>
          <button v-if="isAuthor" class="btn btn-secondary" size="mini" @tap="goEdit">编辑帖子</button>
          <button v-if="isAuthor" class="btn btn-ghost" size="mini" :disabled="deleting" @tap="handleDelete">
            {{ deleting ? '删除中...' : '删除帖子' }}
          </button>
        </view>
      </view>

      <view class="card section">
        <text class="section-title">评论区</text>
        <view style="height: 10rpx" />
        <text class="section-desc">当前共有 {{ post.comment_count }} 条评论。登录后可以发表评论、回复评论，或者举报不当内容。</text>
        <view style="height: 24rpx" />

        <view v-if="!hasToken" class="empty">
          <text class="section-desc">登录后就能参与评论互动，也能保存你的发言记录。</text>
          <view style="height: 24rpx" />
          <button class="btn btn-primary" @tap="goLogin">去登录</button>
        </view>

        <view v-else class="form">
          <view class="field">
            <text class="label">发表评论</text>
            <textarea v-model="commentBody" class="textarea" placeholder="写下你的想法、建议或补充信息" />
          </view>
          <text v-if="commentError" class="error">{{ commentError }}</text>
          <button class="btn btn-primary" :disabled="submittingComment" @tap="submitComment()">
            {{ submittingComment ? '提交中...' : '发布评论' }}
          </button>
        </view>

        <view style="height: 28rpx" />

        <view v-if="post.comments.length" class="comment-list">
          <view v-for="comment in post.comments" :key="comment.id" class="comment-card">
            <text class="section-title comment-author">{{ getAuthorName(comment.author) }}</text>
            <view style="height: 8rpx" />
            <text class="section-desc">{{ comment.body }}</text>
            <view style="height: 8rpx" />
            <text class="helper">{{ formatDate(comment.created_at) }}</text>
            <view v-if="hasToken" style="height: 14rpx" />
            <view v-if="hasToken" class="action-row">
              <button class="btn btn-ghost" size="mini" @tap="toggleReply(comment.id)">
                {{ replyingTo === comment.id ? '收起回复框' : '回复评论' }}
              </button>
              <button v-if="!isMyComment(comment.author.email)" class="btn btn-ghost" size="mini" @tap="handleReportComment(comment.id)">
                举报评论
              </button>
            </view>

            <view v-if="replyingTo === comment.id" class="reply-box">
              <textarea v-model="replyBody" class="textarea" placeholder="补充你的回复内容" />
              <text v-if="commentError" class="error">{{ commentError }}</text>
              <button class="btn btn-primary" :disabled="submittingComment" @tap="submitComment(comment.id)">
                {{ submittingComment ? '提交中...' : '发送回复' }}
              </button>
            </view>

            <view v-if="comment.replies.length" class="reply-list">
              <view v-for="reply in comment.replies" :key="reply.id" class="reply-card">
                <text class="section-title reply-author">{{ getAuthorName(reply.author) }}</text>
                <view style="height: 8rpx" />
                <text class="section-desc">{{ reply.body }}</text>
                <view style="height: 8rpx" />
                <text class="helper">{{ formatDate(reply.created_at) }}</text>
                <view v-if="hasToken && !isMyComment(reply.author.email)" style="height: 12rpx" />
                <button v-if="hasToken && !isMyComment(reply.author.email)" class="btn btn-ghost" size="mini" @tap="handleReportComment(reply.id)">
                  举报评论
                </button>
              </view>
            </view>
          </view>
        </view>

        <view v-else class="empty">
          <text class="section-desc">还没有人评论，这里很适合作为第一条互动的开始。</text>
        </view>
      </view>
    </view>

    <view v-else class="card empty">
      <text class="section-desc">没有找到这条帖子，可能已经被删除或链接失效。</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'

import type { ForumPost, UserSummary } from '../../types/api'
import { createForumComment, deleteForumPost, fetchForumPostDetail, toggleForumPostLike } from '../../services/forum'
import { createModerationReport } from '../../services/moderation'
import { currentUser, ensureAuthenticated, isAuthenticated, redirectToLogin } from '../../utils/auth'
import { navigateTo } from '../../utils/navigation'
import { showToast } from '../../utils/ui'

const postId = ref('')
const post = ref<ForumPost | null>(null)
const loading = ref(false)
const liking = ref(false)
const deleting = ref(false)
const submittingComment = ref(false)
const commentBody = ref('')
const replyBody = ref('')
const replyingTo = ref('')
const commentError = ref('')
const hasToken = ref(isAuthenticated.value)

const isAuthor = computed(() =>
  Boolean(post.value && currentUser.value?.email && post.value.author.email === currentUser.value.email),
)

onLoad(async (options) => {
  postId.value = typeof options?.id === 'string' ? options.id : ''
  if (!postId.value) {
    showToast('缺少帖子 id')
    return
  }

  await loadDetail()
})

onShow(() => {
  hasToken.value = isAuthenticated.value
})

async function loadDetail() {
  loading.value = true
  try {
    post.value = await fetchForumPostDetail(postId.value)
  } catch (error) {
    showToast(error instanceof Error ? error.message : '加载帖子详情失败')
  } finally {
    loading.value = false
    hasToken.value = isAuthenticated.value
  }
}

function getAuthorName(author: UserSummary) {
  return author.nickname || author.full_name || author.email
}

function isMyComment(authorEmail: string) {
  return authorEmail === (currentUser.value?.email ?? '')
}

async function handleLike() {
  if (!ensureAuthenticated(`/pages/forum/detail?id=${postId.value}`)) {
    return
  }
  if (!post.value) {
    return
  }

  liking.value = true
  try {
    const result = await toggleForumPostLike(post.value.id)
    post.value = { ...post.value, is_liked: result.liked, like_count: result.like_count }
  } catch (error) {
    showToast(error instanceof Error ? error.message : '点赞失败')
  } finally {
    liking.value = false
  }
}

async function handleDelete() {
  if (!post.value) {
    return
  }

  deleting.value = true
  try {
    await deleteForumPost(post.value.id)
    showToast('帖子已删除', 'success')
    uni.switchTab({ url: '/pages/forum/index' })
  } catch (error) {
    showToast(error instanceof Error ? error.message : '删除帖子失败')
  } finally {
    deleting.value = false
  }
}

async function handleReportPost() {
  if (!post.value) {
    return
  }
  if (!ensureAuthenticated(`/pages/forum/detail?id=${postId.value}`)) {
    return
  }

  const reasons = ['垃圾广告', '不当内容', '骚扰辱骂', '虚假信息', '其他原因']

  try {
    const reasonIndex = await chooseReason(reasons)
    const details = await collectOptionalDetails()
    await createModerationReport({
      target_type: 'forum_post',
      target_id: post.value.id,
      reason: reasons[reasonIndex] ?? '其他原因',
      details,
    })
    showToast('举报已提交，我们会尽快处理', 'success')
  } catch {
    return
  }
}

async function handleReportComment(commentId: string) {
  if (!ensureAuthenticated(`/pages/forum/detail?id=${postId.value}`)) {
    return
  }

  const reasons = ['人身攻击', '骚扰辱骂', '垃圾广告', '不当内容', '其他原因']

  try {
    const reasonIndex = await chooseReason(reasons)
    const details = await collectOptionalDetails()
    await createModerationReport({
      target_type: 'comment',
      target_id: commentId,
      reason: reasons[reasonIndex] ?? '其他原因',
      details,
    })
    showToast('评论举报已提交，我们会尽快处理', 'success')
  } catch {
    return
  }
}

function chooseReason(reasons: string[]) {
  return new Promise<number>((resolve, reject) => {
    uni.showActionSheet({
      itemList: reasons,
      success: ({ tapIndex }) => resolve(tapIndex),
      fail: reject,
    })
  })
}

function collectOptionalDetails() {
  return new Promise<string>((resolve) => {
    uni.showModal({
      title: '补充说明',
      editable: true,
      placeholderText: '可选，简单补充举报原因',
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
}

function goEdit() {
  navigateTo(`/pages/forum/create?id=${postId.value}`)
}

function toggleReply(commentId: string) {
  replyingTo.value = replyingTo.value === commentId ? '' : commentId
  replyBody.value = ''
  commentError.value = ''
}

async function submitComment(parentId?: string) {
  if (!ensureAuthenticated(`/pages/forum/detail?id=${postId.value}`) || !post.value) {
    return
  }

  const body = (parentId ? replyBody.value : commentBody.value).trim()
  if (body.length < 2) {
    commentError.value = '评论内容至少需要 2 个字'
    return
  }

  submittingComment.value = true
  commentError.value = ''
  try {
    await createForumComment(post.value.id, { body, parent: parentId ?? null })
    commentBody.value = ''
    replyBody.value = ''
    replyingTo.value = ''
    await loadDetail()
    showToast('评论已发布', 'success')
  } catch (error) {
    commentError.value = error instanceof Error ? error.message : '评论提交失败'
  } finally {
    submittingComment.value = false
  }
}

function goLogin() {
  redirectToLogin(`/pages/forum/detail?id=${postId.value}`)
}

function formatDate(value: string) {
  return value.replace('T', ' ').slice(0, 16)
}

function previewImages(urls: string[], current: string) {
  uni.previewImage({ current, urls })
}
</script>

<style scoped lang="scss">
.meta-row,
.stat-row,
.action-row {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  flex-wrap: wrap;
}

.body-text {
  font-size: 28rpx;
  line-height: 1.8;
  color: #102133;
  white-space: pre-wrap;
}

.comment-list,
.reply-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.comment-card,
.reply-card,
.reply-box {
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.75);
}

.comment-author {
  font-size: 30rpx;
}

.reply-author {
  font-size: 28rpx;
}

.reply-list {
  margin-top: 16rpx;
  padding-left: 20rpx;
}

.reply-box {
  margin-top: 16rpx;
}

.detail-image-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.detail-image {
  width: 100%;
  height: 240rpx;
  border-radius: 20rpx;
  background: rgba(16, 33, 51, 0.08);
}
</style>
