<template>
  <view class="container">
    <view class="section hero">
      <text class="eyebrow">CampusClaw 组队招募</text>
      <view style="height: 18rpx" />
      <text class="title">{{ postId ? '修改组队信息，让队友更快理解当前进度。' : '把目标、人数和需求写清楚，合适的队友才更容易出现。' }}</text>
    </view>

    <TeamComposer
      :has-token="hasToken"
      :profile-complete="profileComplete"
      :editing-post="editingPost"
      :assistant-draft="assistantTeamDraft"
      @login="goLogin"
      @profile="goProfile"
      @saved="handleSaved"
      @cancel="goBack"
    />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'

import TeamComposer from '../../components/teammates/TeamComposer.vue'
import type { TeamPost } from '../../types/api'
import { fetchTeammatePost } from '../../services/teammates'
import { ensureAuthenticated, isAuthenticated, profileOnboarded, redirectToLogin } from '../../utils/auth'
import { consumeAssistantDraft } from '../../utils/assistantDraft'
import { navigateTo } from '../../utils/navigation'
import { showToast } from '../../utils/ui'

const hasToken = ref(isAuthenticated.value)
const profileComplete = computed(() => profileOnboarded.value)
const postId = ref('')
const editingPost = ref<TeamPost | null>(null)
const assistantTeamDraft = ref<Record<string, unknown> | null>(null)

onLoad(async (options) => {
  postId.value = typeof options?.id === 'string' ? options.id : ''
  if (postId.value) {
    await loadPost()
  }
})

onShow(() => {
  hasToken.value = isAuthenticated.value
  if (!ensureAuthenticated('/pages/teammates/create')) {
    return
  }
  applyAssistantDraft()
})

async function loadPost() {
  try {
    editingPost.value = await fetchTeammatePost(postId.value)
  } catch (error) {
    showToast(error instanceof Error ? error.message : '加载组队招募失败')
  }
}

function applyAssistantDraft() {
  const draft = consumeAssistantDraft('/pages/teammates/create', ['team_post_create'])
  if (!draft) {
    return
  }
  assistantTeamDraft.value = draft.fill_payload
  showToast('AI 已填入组队草稿', 'success')
}

function handleSaved() {
  uni.navigateBack({
    fail: () => {
      uni.redirectTo({ url: '/pages/teammates/index' })
    },
  })
}

function goLogin() {
  redirectToLogin('/pages/teammates/create')
}

function goProfile() {
  navigateTo('/pages/profile/index')
}

function goBack() {
  uni.navigateBack({
    fail: () => {
      uni.redirectTo({ url: '/pages/teammates/index' })
    },
  })
}
</script>

<style scoped lang="scss">
.hero {
  padding-top: 4rpx;
}
</style>
