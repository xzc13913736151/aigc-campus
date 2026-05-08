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
        <text class="assistant-label">{{ assistantVisible ? '收起助手' : 'AI 助手' }}</text>
        <text class="assistant-sub-label">{{ assistantHint }}</text>
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
import AssistantSheet from '../components/assistant/AssistantSheet.vue'
import { switchTab } from '../utils/navigation'

type TabItem = {
  path: '/pages/forum/index' | '/pages/publish/index' | '/pages/messages/index' | '/pages/me/index'
  label: string
  iconClass: string
}

const leftItems: TabItem[] = [
  { path: '/pages/forum/index', label: '论坛', iconClass: 'icon-forum' },
  { path: '/pages/publish/index', label: '发布', iconClass: 'icon-publish' },
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
.tab-shell {
  position: relative;
  z-index: 9999;
}

.tab-bar {
  position: fixed;
  left: 18rpx;
  right: 18rpx;
  bottom: calc(env(safe-area-inset-bottom) + 18rpx);
  height: 136rpx;
  padding: 14rpx 18rpx 16rpx;
  border-radius: 999rpx;
  background:
    radial-gradient(circle at top, rgba(241, 107, 79, 0.18), transparent 42%),
    rgba(255, 250, 245, 0.995);
  border: 1rpx solid rgba(16, 33, 51, 0.16);
  box-shadow: 0 20rpx 56rpx rgba(16, 33, 51, 0.2);
  display: flex;
  align-items: flex-end;
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
  background: rgba(16, 33, 51, 0.18);
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
  color: #7a7f87;
}

.tab-item.active .tab-icon {
  background: #f16b4f;
}

.tab-item.active .tab-label {
  color: #f16b4f;
}

.assistant-entry {
  flex: 0 0 182rpx;
  transform: translateY(-22rpx);
  gap: 6rpx;
}

.assistant-entry.active .assistant-label {
  color: #f16b4f;
}

.assistant-orb {
  position: relative;
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  padding: 6rpx;
  background:
    radial-gradient(circle at 35% 30%, rgba(255, 255, 255, 0.72), transparent 30%),
    linear-gradient(135deg, #f16b4f, #f5a44c);
  box-shadow: 0 18rpx 36rpx rgba(241, 107, 79, 0.24);
}

.assistant-orb::after {
  content: '';
  position: absolute;
  top: 10rpx;
  right: 12rpx;
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #fff3d9;
}

.assistant-orb-core {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 28rpx;
  font-weight: 800;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(6px);
}

.assistant-label {
  font-size: 24rpx;
  font-weight: 700;
  color: #102133;
}

.assistant-sub-label {
  font-size: 20rpx;
  color: #8a929c;
  line-height: 1;
}
</style>
