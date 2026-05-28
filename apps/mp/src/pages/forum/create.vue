<template>
  <view class="container">
    <view class="card">
      <view class="section">
        <text class="eyebrow">{{ isEditing ? 'CampusClaw 编辑帖子' : 'CampusClaw 发布帖子' }}</text>
        <view style="height: 18rpx" />
        <text class="title">
          {{ isEditing ? '继续完善你的帖子内容，让表达更清楚、互动更顺畅。' : '把你的想法、求助、经验或招募内容发到论坛里。' }}
        </text>
        <view style="height: 18rpx" />
        <text class="subtitle">
          {{ isEditing
            ? '这里是帖子编辑页。你可以修改标题、分类、正文和标签，保存后会直接回到帖子详情。'
            : '你可以在这里发布校园话题、经验分享、活动信息、项目招募或临时求助。当前已经接入真实发帖接口。' }}
        </text>
      </view>

      <view v-if="!hasToken" class="empty">
        <text class="section-desc">发帖前需要先完成微信登录，系统才能记录作者身份并支持后续互动。</text>
        <view style="height: 24rpx" />
        <button class="btn btn-primary" @tap="goLogin">去登录</button>
      </view>

      <view v-else class="form">
        <view class="field">
          <text class="label">帖子标题</text>
          <input v-model="form.title" class="input" type="text" placeholder="用一句话说清你想讨论什么" />
        </view>

        <view class="field">
          <text class="label">帖子分类</text>
          <picker :range="categories" @change="handleCategoryChange">
            <view class="input">{{ form.category || '请选择帖子分类' }}</view>
          </picker>
        </view>

        <view class="field">
          <text class="label">正文内容</text>
          <textarea
            v-model="form.body"
            class="textarea"
            placeholder="写清背景、问题、目标，或者你希望大家如何参与"
          />
        </view>

        <view class="field">
          <text class="label">标签</text>
          <input v-model="form.tagsText" class="input" type="text" placeholder="例如：AI, 校园活动, 组队, 实习" />
          <text class="helper">多个标签请用英文逗号分隔，方便后续搜索和筛选。</text>
        </view>

        <view class="field">
          <text class="label">帖子图片</text>
          <text class="helper">
            最多一次选择 6 张图片。新帖子会在发布成功后自动上传，编辑帖子时可继续追加图片。
          </text>
          <view v-if="pendingImagePaths.length" class="image-section">
            <view class="section-head">
              <text class="helper">待上传图片 {{ pendingImagePaths.length }} 张</text>
              <button class="mini-action" size="mini" @tap="clearPendingImages">
                <text>清空</text>
              </button>
            </view>
            <view class="image-grid">
              <view v-for="path in pendingImagePaths" :key="path" class="image-tile">
                <image class="post-image" :src="path" mode="aspectFill" @tap="previewPendingImages(path)" />
                <button class="remove-image" size="mini" @tap="removePendingImage(path)">
                  <text>移除</text>
                </button>
              </view>
            </view>
          </view>
          <view v-if="imageUrls.length" class="image-grid">
            <image
              v-for="url in imageUrls"
              :key="url"
              class="post-image"
              :src="url"
              mode="aspectFill"
              @tap="previewImages(url)"
            />
          </view>
          <view
            class="editor-button image-picker-button"
            :class="{ disabled: uploadingImages }"
            @tap="chooseImages"
          >
            <text v-if="uploadingImages" class="editor-button-text">上传中...</text>
            <text v-else-if="postId" class="editor-button-text">选择并上传图片</text>
            <text v-else class="editor-button-text">选择帖子图片</text>
          </view>
        </view>

        <text v-if="errorMessage" class="error">{{ normalizedErrorMessage }}</text>

        <view class="editor-actions">
          <view
            class="editor-button primary-action"
            :class="{ disabled: submitting || loading }"
            @tap="handleSubmit"
          >
            <text v-if="submitting && isEditing" class="editor-button-text primary-text">保存中...</text>
            <text v-else-if="submitting" class="editor-button-text primary-text">发布中...</text>
            <text v-else-if="isEditing" class="editor-button-text primary-text">保存修改</text>
            <text v-else class="editor-button-text primary-text">发布帖子</text>
          </view>
          <view class="editor-button secondary-action" @tap="backToForum">
            <text class="editor-button-text secondary-text">返回论坛</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'

import { createForumPost, fetchForumPostDetail, updateForumPost, uploadForumPostImage } from '../../services/forum'
import { consumeAssistantDraft } from '../../utils/assistantDraft'
import { navigateTo } from '../../utils/navigation'
import { showToast } from '../../utils/ui'

const ACCESS_TOKEN_KEY = 'pairup.access-token'
const CURRENT_USER_KEY = 'pairup.current-user'
const categories = ['校园日常', '学习交流', '活动组局', '实习求职', '项目合作', '组队招募', '情绪树洞']
const hasToken = ref(isLoggedIn())
const submitting = ref(false)
const loading = ref(false)
const uploadingImages = ref(false)
const errorMessage = ref('')
const postId = ref('')
const imageUrls = ref<string[]>([])
const pendingImagePaths = ref<string[]>([])

const form = reactive({
  title: '',
  category: '',
  body: '',
  tagsText: '',
})

const isEditing = computed(() => Boolean(postId.value))
const normalizedErrorMessage = computed(() => normalizeErrorMessage(errorMessage.value))

onLoad(async (options) => {
  resetTransientState()
  postId.value = typeof options?.id === 'string' ? options.id : ''
  if (postId.value) {
    await loadPostForEdit()
  }
})

onShow(() => {
  if (submitting.value || uploadingImages.value) {
    resetTransientState()
  }
  hasToken.value = isLoggedIn()
  applyAssistantDraft()
  if (!hasToken.value) {
    redirectToLogin(getEditorUrl())
  }
})

function applyAssistantDraft() {
  if (postId.value) {
    return
  }
  const draft = consumeAssistantDraft('/pages/forum/create', ['forum_post_create'])
  if (!draft) {
    return
  }
  const payload = draft.fill_payload
  form.title = typeof payload.title === 'string' ? payload.title : form.title
  form.body = typeof payload.body === 'string' ? payload.body : form.body
  form.category = typeof payload.category === 'string' ? payload.category : form.category
  if (Array.isArray(payload.tags)) {
    form.tagsText = payload.tags.map(String).join(', ')
  } else if (typeof payload.tags === 'string') {
    form.tagsText = payload.tags
  }
  showToast('AI 已填入帖子草稿', 'success')
}

function resetTransientState() {
  submitting.value = false
  uploadingImages.value = false
  loading.value = false
}

async function loadPostForEdit() {
  if (!postId.value) {
    return
  }

  loading.value = true
  try {
    const post = await fetchForumPostDetail(postId.value)
    if (post.author.email !== getCurrentUserEmail()) {
      showToast('你只能编辑自己发布的帖子')
      backToForum()
      return
    }
    form.title = post.title
    form.category = post.category
    form.body = post.body
    form.tagsText = post.tags.join(', ')
    imageUrls.value = post.image_urls ?? []
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '加载帖子失败')
  } finally {
    loading.value = false
  }
}

async function chooseImages() {
  if (uploadingImages.value) {
    return
  }

  uploadingImages.value = true
  try {
    const media = (await uni.chooseMedia({
      count: 6,
      mediaType: ['image'],
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
    })) as unknown as UniApp.ChooseMediaSuccessCallbackResult

    const files = media.tempFiles?.map((file) => file.tempFilePath).filter(Boolean) ?? []
    if (!files.length) {
      return
    }

    if (!postId.value) {
      const merged = [...pendingImagePaths.value, ...files]
      pendingImagePaths.value = Array.from(new Set(merged)).slice(0, 6)
      return
    }

    for (const filePath of files) {
      await uploadForumPostImage(postId.value, filePath)
    }

    const updated = await fetchForumPostDetail(postId.value)
    imageUrls.value = updated.image_urls ?? []
    showToast('图片上传成功', 'success')
  } catch (error) {
    showToast(getErrorMessage(error, '图片上传失败'))
  } finally {
    uploadingImages.value = false
  }
}

function removePendingImage(path: string) {
  pendingImagePaths.value = pendingImagePaths.value.filter((item) => item !== path)
}

function clearPendingImages() {
  pendingImagePaths.value = []
}

function previewImages(current?: string) {
  if (!imageUrls.value.length) {
    return
  }
  uni.previewImage({
    current: current ?? imageUrls.value[0],
    urls: imageUrls.value,
  })
}

function previewPendingImages(current?: string) {
  if (!pendingImagePaths.value.length) {
    return
  }
  uni.previewImage({
    current: current ?? pendingImagePaths.value[0],
    urls: pendingImagePaths.value,
  })
}

function handleCategoryChange(event: { detail?: { value?: string | number } }) {
  form.category = categories[Number(event.detail?.value ?? 0)] ?? ''
}

function handleSubmit() {
  if (submitting.value || loading.value) {
    return
  }

  errorMessage.value = ''

  if (form.title.trim().length < 4) {
    errorMessage.value = '标题至少需要 4 个字'
    return
  }

  if (!form.category.trim()) {
    errorMessage.value = '请选择帖子分类'
    return
  }

  if (form.body.trim().length < 10) {
    errorMessage.value = '正文至少需要 10 个字'
    return
  }

  const targetUrl = postId.value ? `/pages/forum/create?id=${postId.value}` : '/pages/forum/create'
  if (!ensureLocalAuthenticated(targetUrl)) {
    return
  }

  void submitPostRequest()
}

async function submitPostRequest() {
  submitting.value = true
  try {
    const editingBeforeSubmit = Boolean(postId.value)
    const savedPost = await saveForumPost()

    postId.value = savedPost.id
    imageUrls.value = savedPost.image_urls ?? []

    if (pendingImagePaths.value.length) {
      uploadingImages.value = true
      await uploadPendingImages(savedPost.id)
      pendingImagePaths.value = []
      const refreshedPost = await fetchForumPostDetail(savedPost.id)
      imageUrls.value = refreshedPost.image_urls ?? []
    }

    showToast(editingBeforeSubmit ? '帖子已更新' : '帖子发布成功', 'success')
    navigateTo(`/pages/forum/detail?id=${savedPost.id}`)
  } catch (error) {
    errorMessage.value = getErrorMessage(error, isEditing.value ? '保存失败' : '发帖失败')
  } finally {
    submitting.value = false
    uploadingImages.value = false
  }
}

function getEditorUrl() {
  return postId.value ? `/pages/forum/create?id=${postId.value}` : '/pages/forum/create'
}

function buildPostPayload() {
  return {
    title: form.title.trim(),
    body: form.body.trim(),
    category: form.category.trim(),
    tags: form.tagsText
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean),
  }
}

function saveForumPost() {
  const payload = buildPostPayload()
  if (postId.value) {
    return updateForumPost(postId.value, payload)
  }
  return createForumPost(payload)
}

async function uploadPendingImages(savedPostId: string) {
  const imagesToUpload = [...pendingImagePaths.value]
  for (const filePath of imagesToUpload) {
    await uploadForumPostImage(savedPostId, filePath)
  }
}

function goLogin() {
  redirectToLogin(getEditorUrl())
}

function backToForum() {
  uni.switchTab({ url: '/pages/forum/index' })
}

function isLoggedIn() {
  const token = uni.getStorageSync(ACCESS_TOKEN_KEY)
  return typeof token === 'string' && Boolean(token)
}

function getCurrentUserEmail() {
  const raw = uni.getStorageSync(CURRENT_USER_KEY)
  if (typeof raw !== 'string' || !raw) {
    return ''
  }
  try {
    return (JSON.parse(raw) as { email?: string }).email ?? ''
  } catch {
    return ''
  }
}

function ensureLocalAuthenticated(targetUrl: string) {
  if (isLoggedIn()) {
    return true
  }
  redirectToLogin(targetUrl)
  return false
}

function redirectToLogin(targetUrl: string) {
  uni.setStorageSync('pairup.login-redirect', targetUrl)
  uni.navigateTo({ url: '/pages/auth/login' })
}

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof Error && error.message) {
    return normalizeErrorMessage(error.message, fallback)
  }
  return fallback
}

function normalizeErrorMessage(message: string, fallback = '操作失败，请稍后重试') {
  const value = String(message || '').trim()
  if (!value || /^e\d+_\d+$/i.test(value)) {
    return fallback
  }
  return value
}
</script>

<style scoped lang="scss">
.image-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16rpx;
}

.image-section {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.image-tile {
  position: relative;
  min-width: 0;
}

.post-image {
  width: 100%;
  height: 180rpx;
  border-radius: 20rpx;
  background: rgba(16, 33, 51, 0.08);
}

.mini-action,
.remove-image {
  min-height: 52rpx;
  padding: 0 18rpx;
  border-radius: 999rpx;
  background: rgba(16, 33, 51, 0.08);
  color: #102133;
  font-size: 22rpx;
}

.mini-action::after,
.remove-image::after {
  border: 0;
}

.remove-image {
  position: absolute;
  right: 8rpx;
  bottom: 8rpx;
  background: rgba(16, 33, 51, 0.72);
  color: #fff;
}

.editor-actions {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.editor-button {
  height: 88rpx;
  min-height: 88rpx;
  padding: 0 32rpx;
  margin: 0;
  border: 0;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.editor-button::after {
  border: 0;
}

.editor-button.disabled {
  opacity: 0.65;
  pointer-events: none;
}

.editor-button-text {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
}

.image-picker-button {
  width: 100%;
  background: rgba(255, 255, 255, 0.86);
  border: 1rpx solid rgba(16, 33, 51, 0.12);
  color: #102133;
}

.primary-action {
  flex: 1;
  min-width: 0;
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
