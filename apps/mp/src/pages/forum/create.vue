<template>
  <view class="container">
    <view class="card">
      <view class="section">
        <text class="eyebrow">{{ isEditing ? 'Edit Post' : 'Create Post' }}</text>
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
          <text class="helper">帖子创建成功后即可继续上传图片，当前支持多张图片追加上传。</text>
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
          <button class="btn btn-ghost" :disabled="!postId || uploadingImages" @tap="chooseImages">
            {{ uploadingImages ? '上传中...' : postId ? '选择并上传图片' : '先发布帖子后上传图片' }}
          </button>
        </view>

        <text v-if="errorMessage" class="error">{{ errorMessage }}</text>

        <view class="btn-row">
          <button class="btn btn-primary" :disabled="submitting || loading" @tap="handleSubmit">
            {{ submitting ? (isEditing ? '保存中...' : '发布中...') : isEditing ? '保存修改' : '发布帖子' }}
          </button>
          <button class="btn btn-ghost" @tap="backToForum">返回论坛</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'

import { createForumPost, fetchForumPostDetail, updateForumPost, uploadForumPostImage } from '../../services/forum'
import { currentUser, ensureAuthenticated, isAuthenticated, redirectToLogin } from '../../utils/auth'
import { navigateTo } from '../../utils/navigation'
import { showToast } from '../../utils/ui'

const categories = ['校园日常', '学习交流', '活动组局', '实习求职', '项目合作', '组队招募', '情绪树洞']
const hasToken = ref(isAuthenticated.value)
const submitting = ref(false)
const loading = ref(false)
const uploadingImages = ref(false)
const errorMessage = ref('')
const postId = ref('')
const imageUrls = ref<string[]>([])

const form = reactive({
  title: '',
  category: '',
  body: '',
  tagsText: '',
})

const isEditing = computed(() => Boolean(postId.value))

onLoad(async (options) => {
  postId.value = typeof options?.id === 'string' ? options.id : ''
  if (postId.value) {
    await loadPostForEdit()
  }
})

onShow(() => {
  hasToken.value = isAuthenticated.value
  if (!hasToken.value) {
    ensureAuthenticated(postId.value ? `/pages/forum/create?id=${postId.value}` : '/pages/forum/create')
  }
})

async function loadPostForEdit() {
  if (!postId.value) {
    return
  }

  loading.value = true
  try {
    const post = await fetchForumPostDetail(postId.value)
    if (post.author.email !== (currentUser.value?.email ?? '')) {
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
    errorMessage.value = error instanceof Error ? error.message : '加载帖子失败'
  } finally {
    loading.value = false
  }
}

async function chooseImages() {
  if (!postId.value) {
    showToast('请先发布帖子，再继续上传图片')
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

    for (const filePath of files) {
      await uploadForumPostImage(postId.value, filePath)
    }

    const updated = await fetchForumPostDetail(postId.value)
    imageUrls.value = updated.image_urls ?? []
    showToast('图片上传成功', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '图片上传失败')
  } finally {
    uploadingImages.value = false
  }
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

function handleCategoryChange(event: { detail?: { value?: string | number } }) {
  form.category = categories[Number(event.detail?.value ?? 0)] ?? ''
}

async function handleSubmit() {
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
  if (!ensureAuthenticated(targetUrl)) {
    return
  }

  submitting.value = true
  try {
    const payload = {
      title: form.title.trim(),
      body: form.body.trim(),
      category: form.category.trim(),
      tags: form.tagsText
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean),
    }

    const wasEditing = Boolean(postId.value)
    const post = postId.value ? await updateForumPost(postId.value, payload) : await createForumPost(payload)

    postId.value = post.id
    imageUrls.value = post.image_urls ?? []

    showToast(wasEditing ? '帖子已更新' : '帖子发布成功', 'success')
    if (!wasEditing) {
      showToast('现在可以继续上传图片', 'none')
    } else {
      navigateTo(`/pages/forum/detail?id=${post.id}`)
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : isEditing.value ? '保存失败' : '发帖失败'
  } finally {
    submitting.value = false
  }
}

function goLogin() {
  redirectToLogin(postId.value ? `/pages/forum/create?id=${postId.value}` : '/pages/forum/create')
}

function backToForum() {
  uni.switchTab({ url: '/pages/forum/index' })
}
</script>

<style scoped lang="scss">
.image-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16rpx;
}

.post-image {
  width: 100%;
  height: 180rpx;
  border-radius: 20rpx;
  background: rgba(16, 33, 51, 0.08);
}
</style>
