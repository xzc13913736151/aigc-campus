<template>
  <view class="container">
    <view class="section hero">
      <text class="eyebrow">CampusClaw 消息</text>
      <view style="height: 18rpx" />
      <text class="title">聊天、通知和新的连接，都在这里汇合。</text>
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
            <text class="section-title">搜索联系人</text>
            <view style="height: 8rpx" />
            <text class="section-desc">输入 CampusClaw ID 或昵称，找到同学后可以直接发起聊天。</text>
          </view>
        </view>
        <view style="height: 20rpx" />

        <view class="contact-search-row">
          <input
            v-model="contactKeyword"
            class="input contact-search-input"
            type="text"
            placeholder="例如 CC8K3P2A 或昵称"
            confirm-type="search"
            @confirm="handleContactSearch"
          />
          <button class="btn btn-primary contact-search-button" :disabled="searchingContacts" @tap="handleContactSearch">
            {{ searchingContacts ? '搜索中...' : '搜索' }}
          </button>
        </view>

        <view v-if="contactResults.length" style="height: 20rpx" />
        <view v-if="contactResults.length" class="contact-result-list">
          <view v-for="contact in contactResults" :key="contact.id" class="contact-card">
            <view class="contact-main">
              <view v-if="contact.avatar_url" class="contact-avatar">
                <CachedImage :src="contact.avatar_url" mode="aspectFill" />
              </view>
              <view v-else class="contact-avatar fallback">
                <text>{{ getContactInitial(contact) }}</text>
              </view>
              <view class="contact-copy">
                <text class="section-title contact-name">{{ getContactName(contact) }}</text>
                <view style="height: 6rpx" />
                <text class="helper">CampusClaw ID：{{ contact.claw_id }}</text>
                <view v-if="contact.headline" style="height: 6rpx" />
                <text v-if="contact.headline" class="section-desc">{{ contact.headline }}</text>
              </view>
            </view>
            <button
              class="btn btn-secondary"
              :disabled="startingContactId === contact.id"
              @tap="startContactChat(contact)"
            >
              {{ startingContactId === contact.id ? '处理中...' : '联系TA' }}
            </button>
          </view>
        </view>

        <view v-else-if="contactSearchDone" class="empty small-empty">
          <text class="section-desc">没有找到匹配联系人，可以确认一下 CampusClaw ID 是否输入完整。</text>
        </view>
      </view>

      <view class="card section">
        <view class="section-head">
          <view>
            <text class="section-title">聊天会话</text>
            <view style="height: 8rpx" />
            <text class="section-desc">优先显示最近活跃的聊天，支持在线状态、输入状态和隐藏会话。</text>
          </view>
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
              <button class="btn btn-ghost" @tap="openThread(thread.id)">进入聊天</button>
              <button class="btn btn-ghost" :disabled="hidingThreadId === thread.id" @tap="handleHideThread(thread.id)">
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
          <button class="mark-all-read-button" :disabled="!notifications.length || unreadCount === 0" @tap="handleMarkAllRead">
            全部已读
          </button>
        </view>
        <view style="height: 20rpx" />

        <scroll-view scroll-x class="notification-tabs" :show-scrollbar="false">
          <view class="notification-tab-row">
            <button
              v-for="tab in notificationTabs"
              :key="tab.value"
              class="notification-tab"
              :class="{ active: activeNotificationTab === tab.value }"
              @tap="activeNotificationTab = tab.value"
            >
              {{ tab.label }}
            </button>
          </view>
        </scroll-view>
        <view style="height: 20rpx" />

        <view v-if="filteredNotifications.length" class="grid">
          <view v-for="item in filteredNotifications" :key="item.id" class="card message-card" :class="{ unread: !item.is_read }">
            <view class="message-head">
              <view style="flex: 1">
                <text class="notification-kind">{{ getNotificationKindLabel(item) }}</text>
                <view style="height: 8rpx" />
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
              <button class="btn btn-ghost" @tap="openNotification(item)">查看</button>
              <button
                v-if="!item.is_read"
                class="btn btn-ghost"
                :disabled="markingId === item.id"
                @tap="handleMarkRead(item.id)"
              >
                {{ markingId === item.id ? '处理中...' : '标记已读' }}
              </button>
            </view>
          </view>
        </view>

        <view v-else class="empty">
          <text class="section-desc">{{ activeNotificationTab === 'agent' ? 'Agent 操作记录接口尚未提供；后续可在这里展示草稿、已执行、过期和已取消状态。' : '这个分类暂时没有新消息。' }}</text>
        </view>
      </view>
    </view>

    <BottomTabBar />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onHide, onPullDownRefresh, onReachBottom, onShow, onUnload } from '@dcloudio/uni-app'

import BottomTabBar from '../../components/BottomTabBar.vue'
import CachedImage from '../../components/CachedImage.vue'
import type { ChatThread, ContactSearchUser, NotificationItem } from '../../types/api'
import { createChatThread, fetchChatThreads, hideChatThread } from '../../services/chat'
import { searchContacts } from '../../services/auth'
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
const activeNotificationTab = ref<'all' | 'team' | 'interaction' | 'trade' | 'agent'>('all')
const contactKeyword = ref('')
const contactResults = ref<ContactSearchUser[]>([])
const searchingContacts = ref(false)
const contactSearchDone = ref(false)
const startingContactId = ref('')
const threadPresence = ref<Record<string, boolean>>({})
const threadTyping = ref<Record<string, boolean>>({})
let notificationSocket: UniApp.SocketTask | null = null
let inboxSocket: UniApp.SocketTask | null = null

const unreadThreadCount = computed(() => threads.value.filter((thread) => thread.unread_count > 0).length)
const notificationTabs = [
  { value: 'all' as const, label: '全部' },
  { value: 'team' as const, label: '组队申请' },
  { value: 'interaction' as const, label: '互动通知' },
  { value: 'trade' as const, label: '交易消息' },
  { value: 'agent' as const, label: 'Agent 记录' },
]
const filteredNotifications = computed(() => {
  if (activeNotificationTab.value === 'all') return notifications.value
  if (activeNotificationTab.value === 'agent') return []
  return notifications.value.filter((item) => getNotificationKind(item) === activeNotificationTab.value)
})

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

onPullDownRefresh(async () => {
  await loadAll()
  uni.stopPullDownRefresh()
})

onReachBottom(() => {
  void loadAll()
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

async function handleContactSearch() {
  const keyword = contactKeyword.value.trim()
  contactSearchDone.value = false
  contactResults.value = []
  if (keyword.length < 2) {
    showToast('请输入至少 2 个字符')
    return
  }

  searchingContacts.value = true
  try {
    contactResults.value = await searchContacts(keyword)
    contactSearchDone.value = true
  } catch (error) {
    showToast(error instanceof Error ? error.message : '搜索联系人失败')
  } finally {
    searchingContacts.value = false
  }
}

async function startContactChat(contact: ContactSearchUser) {
  startingContactId.value = contact.id
  try {
    const thread = await createChatThread({
      target_user_id: contact.id,
      source_type: 'contact_search',
      source_id: contact.claw_id,
    })
    navigateTo(`/pages/chat/index?threadId=${thread.id}`)
  } catch (error) {
    showToast(error instanceof Error ? error.message : '创建聊天失败')
  } finally {
    startingContactId.value = ''
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

function getNotificationKind(item: NotificationItem) {
  if (item.type.startsWith('team_') || item.target_type === 'team_post') return 'team'
  if (item.target_type === 'trade_post' || item.type.startsWith('trade_')) return 'trade'
  return 'interaction'
}

function getNotificationKindLabel(item: NotificationItem) {
  const labels = {
    team: '组队申请',
    trade: '交易消息',
    interaction: '互动通知',
  }
  return labels[getNotificationKind(item) as keyof typeof labels]
}

function getCounterpartName(thread: ChatThread) {
  return thread.counterpart?.nickname || thread.counterpart?.full_name || thread.counterpart?.email || '校园用户'
}

function getContactName(contact: ContactSearchUser) {
  return contact.nickname || contact.full_name || contact.claw_id || 'CampusClaw 用户'
}

function getContactInitial(contact: ContactSearchUser) {
  return getContactName(contact).slice(0, 1)
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
  return thread.last_message.body || (thread.last_message.image_url ? '[图片]' : '')
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
  uni.switchTab({ url: '/pages/publish/index' })
}

function goForum() {
  uni.switchTab({ url: '/pages/forum/index' })
}
</script>

<style scoped lang="scss">
@use '../../styles/tokens' as t;

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
  color: #2f2a24;
}

.contact-search-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.contact-search-input {
  flex: 1;
  min-width: 0;
}

.contact-search-button {
  flex-shrink: 0;
  min-width: 132rpx;
}

.contact-result-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.contact-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  padding: 20rpx;
  border-radius: 24rpx;
  background: rgba(255, 250, 245, 0.86);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
}

.contact-main {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.contact-avatar {
  width: 76rpx;
  height: 76rpx;
  border-radius: 50%;
  flex-shrink: 0;
  background: rgba(241, 107, 79, 0.14);
}

.contact-avatar.fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c15f3c;
  font-size: 28rpx;
  font-weight: 800;
}

.contact-copy {
  flex: 1;
  min-width: 0;
}

.contact-name {
  margin-bottom: 0;
  font-size: 30rpx;
}

.small-empty {
  padding: 24rpx 0 0;
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
  color: #6f675d;
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
  background: #c15f3c;
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
  color: #c15f3c;
  font-size: 22rpx;
  font-weight: 700;
}

.message-badge.read {
  background: rgba(16, 33, 51, 0.08);
  color: #6f675d;
}

.notification-tabs {
  width: 100%;
  white-space: nowrap;
}

.notification-tab-row {
  display: inline-flex;
  gap: 12rpx;
  padding-bottom: 2rpx;
}

.notification-tab {
  min-height: 72rpx;
  padding: 0 22rpx;
  margin: 0;
  border: 1rpx solid t.$color-line;
  border-radius: t.$radius-sm;
  background: t.$color-surface;
  color: t.$color-ink-secondary;
  font-size: 24rpx;
  font-weight: 600;
}

.notification-tab.active {
  border-color: t.$color-brand;
  background: t.$color-brand-soft;
  color: t.$color-brand-deep;
}

.notification-kind {
  display: inline-flex;
  padding: 6rpx 12rpx;
  border-radius: 10rpx;
  background: t.$color-input;
  color: t.$color-ink-secondary;
  font-size: 20rpx;
  font-weight: 650;
}

.mark-all-read-button {
  flex-shrink: 0;
  min-width: 148rpx;
  height: 58rpx;
  min-height: 58rpx;
  padding: 0 24rpx;
  margin: 0;
  border: 0;
  border-radius: 18rpx;
  background: #c15f3c;
  color: #fff;
  font-size: 24rpx;
  font-weight: 800;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
}

.mark-all-read-button[disabled] {
  background: rgba(16, 33, 51, 0.1);
  color: #999084;
}

.mark-all-read-button::after {
  border: 0;
}

.action-row,
.compact-row {
  display: flex;
  gap: 20rpx;
  flex-wrap: wrap;
}
</style>
