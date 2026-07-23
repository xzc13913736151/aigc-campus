<template>
  <view v-if="showShell" class="tab-shell">
    <AssistantSheet
      :visible="assistantVisible"
      :page-type="assistantPageType"
      :context-path="currentPath"
      @close="assistantVisible = false"
    />

    <view class="tab-bar">
      <button
        v-for="item in leftItems"
        :key="item.path"
        class="tab-item"
        :class="{ active: currentPath === item.path }"
        @tap="handleSwitch(item.path)"
      >
        <view class="tab-icon" :class="item.iconClass" />
        <text class="tab-label">{{ item.label }}</text>
      </button>

      <button class="assistant-entry" :class="{ active: assistantVisible }" @tap="toggleAssistant">
        <view class="assistant-orb">
          <view class="assistant-orb-core">AI</view>
        </view>
      </button>

      <button
        v-for="item in rightItems"
        :key="item.path"
        class="tab-item"
        :class="{ active: currentPath === item.path }"
        @tap="handleSwitch(item.path)"
      >
        <view class="tab-icon" :class="item.iconClass" />
        <text class="tab-label">{{ item.label }}</text>
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import type { AssistantSession } from '../types/api'
import AssistantSheet from './assistant/AssistantSheet.vue'
import { switchTab } from '../utils/navigation'

type TabItem = {
  path: '/pages/forum/index' | '/pages/publish/index' | '/pages/messages/index' | '/pages/me/index'
  label: string
  iconClass: string
}

const leftItems: TabItem[] = [
  { path: '/pages/forum/index', label: '论坛', iconClass: 'icon-forum' },
  { path: '/pages/publish/index', label: '匹配', iconClass: 'icon-publish' },
]

const rightItems: TabItem[] = [
  { path: '/pages/messages/index', label: '消息', iconClass: 'icon-messages' },
  { path: '/pages/me/index', label: '我的', iconClass: 'icon-me' },
]

const currentPath = ref('/pages/forum/index')
const assistantVisible = ref(false)
let syncTimer: ReturnType<typeof setInterval> | null = null

const tabPaths = new Set([
  '/pages/forum/index',
  '/pages/publish/index',
  '/pages/messages/index',
  '/pages/me/index',
])

const showShell = computed(() => tabPaths.has(currentPath.value))

const assistantPageType = computed<AssistantSession['page_type']>(() => {
  if (currentPath.value.startsWith('/pages/forum')) {
    return 'forum'
  }
  if (currentPath.value.startsWith('/pages/publish')) {
    return 'publish'
  }
  if (currentPath.value.startsWith('/pages/messages')) {
    return 'messages'
  }
  if (currentPath.value.startsWith('/pages/me')) {
    return 'me'
  }
  return 'general'
})

const assistantHint = computed(() => {
  if (assistantPageType.value === 'forum') {
    return '发帖灵感'
  }
  if (assistantPageType.value === 'publish') {
    return '文案策划'
  }
  if (assistantPageType.value === 'messages') {
    return '聊天建议'
  }
  if (assistantPageType.value === 'me') {
    return '资料优化'
  }
  return '随时帮忙'
})

onMounted(() => {
  syncCurrentPath()
  syncTimer = setInterval(syncCurrentPath, 300)
})

onBeforeUnmount(() => {
  if (syncTimer) {
    clearInterval(syncTimer)
    syncTimer = null
  }
})

function syncCurrentPath() {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1] as { route?: string } | undefined
  if (!current?.route) {
    return
  }
  currentPath.value = `/${current.route}` as typeof currentPath.value
}

function handleSwitch(path: TabItem['path']) {
  assistantVisible.value = false
  if (currentPath.value === path) {
    return
  }
  currentPath.value = path
  switchTab(path)
}

function toggleAssistant() {
  syncCurrentPath()
  assistantVisible.value = !assistantVisible.value
}
</script>

<style scoped lang="scss">
@use '../styles/tokens' as t;

.tab-shell {
  position: relative;
  z-index: 9999;
}

.tab-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  min-height: 116rpx;
  padding: 10rpx 18rpx calc(env(safe-area-inset-bottom) + 10rpx);
  background: rgba(255, 252, 247, 0.98);
  border-top: 1rpx solid t.$color-line;
  box-shadow: 0 -8rpx 28rpx rgba(67, 50, 38, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 10000;
}

.tab-item,
.assistant-entry {
  background: transparent;
  border: 0;
  padding: 0;
  margin: 0;
  min-width: 0;
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.tab-item::after,
.assistant-entry::after {
  border: 0;
}

.tab-icon {
  position: relative;
  width: 28rpx;
  height: 28rpx;
  border-radius: 10rpx;
  background: t.$color-line;
}

.icon-forum {
  border-radius: 50%;
}

.icon-publish::before,
.icon-messages::before,
.icon-me::before {
  content: '';
  position: absolute;
  inset: 6rpx;
  border-radius: 6rpx;
  background: rgba(255, 255, 255, 0.45);
}

.icon-me {
  border-radius: 50%;
}

.tab-label {
  font-size: 24rpx;
  font-weight: 600;
  color: t.$color-ink-muted;
}

.tab-item.active .tab-icon {
  background: t.$color-brand;
}

.tab-item.active .tab-label {
  color: t.$color-brand-deep;
}

.assistant-entry {
  flex: 0 0 112rpx;
  height: 112rpx;
  margin-top: -18rpx;
  gap: 0;
}

.assistant-orb {
  position: relative;
  width: 88rpx;
  height: 88rpx;
  border-radius: 28rpx;
  padding: 5rpx;
  background: t.$color-ai;
  box-shadow: 0 10rpx 24rpx rgba(67, 50, 38, 0.16);
}

.assistant-orb-core {
  width: 100%;
  height: 100%;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: t.$color-inverse;
  font-size: 25rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
  background: rgba(255, 255, 255, 0.06);
}

.assistant-label {
  font-size: 24rpx;
  font-weight: 700;
  color: t.$color-ink;
}

.assistant-sub-label {
  font-size: 20rpx;
  color: t.$color-ink-muted;
  line-height: 1;
}
</style>
