<template>
  <view class="container">
    <view class="section">
      <text class="eyebrow">CampusClaw Chat</text>
      <view style="height: 18rpx" />
      <text class="title">聊天放前面，通知放后面，先把真正需要回复的人找到。</text>
      <view style="height: 18rpx" />
      <text class="subtitle">
        这里优先展示你的聊天会话，方便你快速继续沟通。帖子互动和系统提醒会收进下方通知区。
      </text>
      <view style="height: 26rpx" />

      <view class="status-row">
        <view class="status-chip" :class="{ active: hasToken }">
          <text>{{ hasToken ? '已登录' : '未登录' }}</text>
        </view>
        <view class="status-chip" :class="{ complete: profileComplete }">
          <text>{{ hasToken ? `未读通知 ${unreadCount}` : '登录后查看聊天与通知' }}</text>
        </view>
      </view>
    </view>

    <view v-if="!hasToken" class="card empty">
      <text class="section-desc">登录后才能查看聊天列表、系统通知和实时互动状态。</text>
      <view style="height: 24rpx" />
      <button class="btn btn-primary" @tap="goLogin">去登录</button>
    </view>

    <view v-else-if="!profileComplete" class="card empty">
      <text class="section-desc">请先完成个人资料补全，这样系统才能准确展示聊天对象和匹配入口。</text>
      <view style="height: 24rpx" />
      <button class="btn btn-primary" @tap="goProfile">完善资料</button>
    </view>

    <view v-else class="section">
      <view class="grid summary-grid">
        <view class="card summary-card">
          <text class="summary-value">{{ threads.length }}</text>
          <view style="height: 8rpx" />
          <text class="section-desc">会话数量</text>
        </view>
        <view class="card summary-card">
          <text class="summary-value">{{ unreadThreadCount }}</text>
          <view style="height: 8rpx" />
          <text class="section-desc">未读会话</text>
        </view>
        <view class="card summary-card">
          <text class="summary-value">{{ unreadCount }}</text>
          <view style="height: 8rpx" />
          <text class="section-desc">未读通知</text>
        </view>
      </view>

      <view class="card section">
        <view class="section-head">
          <view>
            <text class="section-title">聊天会话</text>
            <view style="height: 8rpx" />
            <text class="section-desc">优先显示最近活跃的聊天，支持在线状态、输入状态和隐藏会话。</text>
          </view>
          <button class="btn btn-ghost" size="mini" :disabled="loadingThreads" @tap="loadThreads">
            {{ loadingThreads ? '刷新中...' : '刷新会话' }}
          </button>
        </view>
        <view style="height: 20rpx" />

        <view v-if="threads.length" class="grid">
          <view
            v-for="thread in threads"
            :key="thread.id"
            class="thread-card"
            :class="{ unread: thread.unread_count > 0 }"
          >
            <view class="thread-head">
              <view style="flex: 1" @tap="openThread(thread.id)">
                <view class="thread-title-row">
                  <text class="section-title thread-name">{{ getCounterpartName(thread) }}</text>
                  <text class="thread-state">{{ getThreadStateText(thread.id) }}</text>
                </view>
                <view style="height: 8rpx" />
                <text class="section-desc">{{ getLastMessageText(thread) }}</text>
                <view style="height: 10rpx" />
                <text class="helper">{{ thread.last_message ? formatDate(thread.last_message.created_at) : formatDate(thread.created_at) }}</text>
              </view>
              <view class="thread-meta">
                <text v-if="thread.unread_count" class="thread-badge">{{ thread.unread_count }}</text>
              </view>
            </view>
            <view style="height: 16rpx" />
            <view class="action-row">
              <button class="btn btn-ghost" size="mini" @tap="openThread(thread.id)">进入聊天</button>
              <button class="btn btn-ghost" size="mini" :disabled="hidingThreadId === thread.id" @tap="handleHideThread(thread.id)">
                {{ hidingThreadId === thread.id ? '隐藏中...' : '隐藏会话' }}
              </button>
            </view>
          </view>
        </view>

        <view v-else class="empty">
          <text class="section-desc">你还没有聊天会话，可以先去论坛、组队或匹配页认识新同学。</text>
          <view style="height: 20rpx" />
          <view class="btn-row compact-row">
            <button class="btn btn-ghost" @tap="goForum">去论坛</button>
            <button class="btn btn-ghost" @tap="goDating">去匹配</button>
          </view>
        </view>
      </view>

      <view class="card">
        <view class="section-head">
          <view>
            <text class="section-title">通知提醒</text>
            <view style="height: 8rpx" />
            <text class="section-desc">帖子互动、聊天提醒和系统消息都会集中在这里，避免打断你主线聊天。</text>
          </view>
          <view class="action-row">
            <button class="btn btn-ghost" size="mini" :disabled="loadingNotifications" @tap="loadNotifications">
              {{ loadingNotifications ? '刷新中...' : '刷新通知' }}
            </button>
            <button class="btn btn-primary" size="mini" :disabled="!notifications.length || unreadCount === 0" @tap="handleMarkAllRead">
              全部已读
            </button>
          </view>
        </view>
        <view style="height: 20rpx" />

        <view v-if="notifications.length" class="grid">
          <view v-for="item in notifications" :key="item.id" class="card message-card" :class="{ unread: !item.is_read }">
            <view class="message-head">
              <view style="flex: 1">
                <text class="section-title thread-name">{{ item.title }}</text>
                <view style="height: 8rpx" />
                <text class="helper">{{ getActorName(item) }} · {{ formatDate(item.created_at) }}</text>
              </view>
              <text class="message-badge" :class="{ read: item.is_read }">{{ item.is_read ? '已读' : '未读' }}</text>
            </view>
            <view style="height: 12rpx" />
            <text class="section-desc">{{ item.body }}</text>
            <view style="height: 18rpx" />
            <view class="action-row">
              <button class="btn btn-ghost" size="mini" @tap="openNotification(item)">查看</button>
              <button
                v-if="!item.is_read"
                class="btn btn-ghost"
                size="mini"
                :disabled="markingId === item.id"
                @tap="handleMarkRead(item.id)"
              >
                {{ markingId === item.id ? '处理中...' : '标记已读' }}
              </button>
            </view>
          </view>
        </view>

        <view v-else class="empty">
          <text class="section-desc">当前还没有通知提醒，等有新的互动时会出现在这里。</text>
        </view>
      </view>
    </view>

    <BottomTabBar />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onHide, onShow, onUnload } from '@dcloudio/uni-app'

import BottomTabBar from '../../components/BottomTabBar.vue'
import type { ChatThread, NotificationItem } from '../../types/api'
import { fetchChatThreads, hideChatThread } from '../../services/chat'
import {
  fetchNotificationUnreadCount,
  fetchNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '../../services/notifications'
import { isAuthenticated, profileOnboarded, redirectToLogin } from '../../utils/auth'
import { navigateTo } from '../../utils/navigation'
import { showToast } from '../../utils/ui'
import { connectAuthedSocket } from '../../utils/websocket'

type ChatInboxPayload =
  | { type: 'chat.inbox.ready' }
  | { type: 'chat.thread'; thread: ChatThread }
  | { type: 'chat.thread_state'; thread_id: string; user_id: string; online?: boolean; is_typing?: boolean }

const hasToken = computed(() => isAuthenticated.value)
const profileComplete = computed(() => profileOnboarded.value)
const notifications = ref<NotificationItem[]>([])
const threads = ref<ChatThread[]>([])
const unreadCount = ref(0)
const loadingNotifications = ref(false)
const loadingThreads = ref(false)
const hidingThreadId = ref('')
const markingId = ref('')
const threadPresence = ref<Record<string, boolean>>({})
const threadTyping = ref<Record<string, boolean>>({})
let notificationSocket: UniApp.SocketTask | null = null
let inboxSocket: UniApp.SocketTask | null = null

const unreadThreadCount = computed(() => threads.value.filter((thread) => thread.unread_count > 0).length)

onShow(() => {
  if (hasToken.value) {
    loadAll()
    connectNotificationSocket()
    connectInboxSocket()
    return
  }

  teardownSockets()
  notifications.value = []
  threads.value = []
  unreadCount.value = 0
})

onHide(() => {
  teardownSockets()
})

onUnload(() => {
  teardownSockets()
})

async function loadAll() {
  await Promise.all([loadNotifications(), loadThreads()])
}

async function loadNotifications() {
  loadingNotifications.value = true
  try {
    const [list, unread] = await Promise.all([fetchNotifications(), fetchNotificationUnreadCount()])
    notifications.value = list
    unreadCount.value = unread.unread_count
  } catch (error) {
    showToast(error instanceof Error ? error.message : '加载通知失败')
  } finally {
    loadingNotifications.value = false
  }
}

async function loadThreads() {
  loadingThreads.value = true
  try {
    threads.value = (await fetchChatThreads()).sort(compareThreadOrder)
  } catch (error) {
    showToast(error instanceof Error ? error.message : '加载会话失败')
  } finally {
    loadingThreads.value = false
  }
}

async function handleHideThread(threadId: string) {
  hidingThreadId.value = threadId
  try {
    await hideChatThread(threadId)
    threads.value = threads.value.filter((thread) => thread.id !== threadId)
    showToast('会话已隐藏', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '隐藏会话失败')
  } finally {
    hidingThreadId.value = ''
  }
}

function connectNotificationSocket() {
  if (notificationSocket || !hasToken.value) {
    return
  }

  notificationSocket = connectAuthedSocket('/ws/notifications/', {
    onMessage(data) {
      if (!data || typeof data !== 'object') {
        return
      }

      const payload = data as Partial<NotificationItem> & { type?: string }
      if (payload.type === 'notifications.ready') {
        return
      }
      if (!payload.id || !payload.title) {
        return
      }

      const incoming = payload as NotificationItem
      notifications.value = [incoming, ...notifications.value.filter((item) => item.id !== incoming.id)]
      unreadCount.value += incoming.is_read ? 0 : 1
    },
  })
}

function connectInboxSocket() {
  if (inboxSocket || !hasToken.value) {
    return
  }

  inboxSocket = connectAuthedSocket('/ws/chat/inbox/', {
    onMessage(data) {
      handleInboxPayload(data as ChatInboxPayload)
    },
  })
}

function handleInboxPayload(payload: ChatInboxPayload) {
  if (payload.type === 'chat.thread') {
    const incoming = payload.thread
    const existing = threads.value.find((thread) => thread.id === incoming.id)
    const nextThreads = existing
      ? threads.value.map((thread) => (thread.id === incoming.id ? incoming : thread))
      : [incoming, ...threads.value]
    threads.value = nextThreads.sort(compareThreadOrder)
    return
  }

  if (payload.type === 'chat.thread_state') {
    if (typeof payload.online === 'boolean') {
      threadPresence.value = { ...threadPresence.value, [payload.thread_id]: payload.online }
    }
    if (typeof payload.is_typing === 'boolean') {
      threadTyping.value = { ...threadTyping.value, [payload.thread_id]: payload.is_typing }
    }
  }
}

function compareThreadOrder(first: ChatThread, second: ChatThread) {
  const firstTime = first.last_message?.created_at || first.updated_at
  const secondTime = second.last_message?.created_at || second.updated_at
  return secondTime.localeCompare(firstTime)
}

function teardownSockets() {
  notificationSocket?.close({})
  inboxSocket?.close({})
  notificationSocket = null
  inboxSocket = null
  threadPresence.value = {}
  threadTyping.value = {}
}

function getActorName(item: NotificationItem) {
  return item.actor?.nickname || item.actor?.full_name || item.actor?.email || '系统'
}

function getCounterpartName(thread: ChatThread) {
  return thread.counterpart?.nickname || thread.counterpart?.full_name || thread.counterpart?.email || '校园用户'
}

function getThreadStateText(threadId: string) {
  if (threadTyping.value[threadId]) {
    return '对方正在输入...'
  }
  return threadPresence.value[threadId] ? '对方在线' : '对方离线'
}

function getLastMessageText(thread: ChatThread) {
  if (!thread.last_message) {
    return '还没有消息，点进去开始聊天吧。'
  }
  if (thread.last_message.is_withdrawn) {
    return thread.last_message.sender.id === thread.counterpart?.id ? '对方撤回了一条消息' : '你撤回了一条消息'
  }
  return thread.last_message.body
}

async function handleMarkRead(notificationId: string) {
  markingId.value = notificationId
  try {
    await markNotificationRead(notificationId)
    await loadNotifications()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '标记已读失败')
  } finally {
    markingId.value = ''
  }
}

async function handleMarkAllRead() {
  try {
    await markAllNotificationsRead()
    await loadNotifications()
    showToast('全部通知已标记为已读', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '全部已读失败')
  }
}

async function openNotification(item: NotificationItem) {
  if (!item.is_read) {
    await handleMarkRead(item.id)
  }

  if (item.target_type === 'forum_post' && item.target_id) {
    navigateTo(`/pages/forum/detail?id=${item.target_id}`)
    return
  }

  if (item.target_type === 'team_post') {
    navigateTo('/pages/teammates/index')
    return
  }

  if (item.target_type === 'chat_thread' && item.target_id) {
    navigateTo(`/pages/chat/index?threadId=${item.target_id}`)
    return
  }

  uni.switchTab({ url: '/pages/forum/index' })
}

function openThread(threadId: string) {
  navigateTo(`/pages/chat/index?threadId=${threadId}`)
}

function formatDate(value: string) {
  return value.replace('T', ' ').slice(0, 16)
}

function goLogin() {
  redirectToLogin('/pages/messages/index')
}

function goProfile() {
  navigateTo('/pages/profile/index')
}

function goDating() {
  navigateTo('/pages/dating/index')
}

function goForum() {
  uni.switchTab({ url: '/pages/forum/index' })
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

.status-chip.active {
  background: rgba(241, 107, 79, 0.14);
  color: #f16b4f;
}

.status-chip.complete {
  background: rgba(77, 166, 106, 0.18);
  color: #2e7d49;
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

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16rpx;
}

.thread-card {
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.76);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
}

.thread-card.unread {
  border-color: rgba(241, 107, 79, 0.2);
  box-shadow: 0 16rpx 48rpx rgba(241, 107, 79, 0.08);
}

.thread-head {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
}

.thread-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.thread-name {
  margin-bottom: 0;
  font-size: 30rpx;
}

.thread-state {
  flex-shrink: 0;
  font-size: 22rpx;
  color: #6b7280;
}

.thread-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8rpx;
}

.thread-badge {
  min-width: 38rpx;
  height: 38rpx;
  padding: 0 10rpx;
  border-radius: 999rpx;
  background: #f16b4f;
  color: #fff;
  font-size: 22rpx;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.message-card {
  display: flex;
  flex-direction: column;
}

.message-card.unread {
  border-color: rgba(241, 107, 79, 0.2);
  box-shadow: 0 16rpx 48rpx rgba(241, 107, 79, 0.08);
}

.message-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.message-badge {
  flex-shrink: 0;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(241, 107, 79, 0.12);
  color: #f16b4f;
  font-size: 22rpx;
  font-weight: 700;
}

.message-badge.read {
  background: rgba(16, 33, 51, 0.08);
  color: #6b7280;
}

.action-row,
.compact-row {
  display: flex;
  gap: 20rpx;
  flex-wrap: wrap;
}
</style>
