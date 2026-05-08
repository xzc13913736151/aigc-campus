<template>
  <view class="container">
    <view class="card section">
      <text class="eyebrow">CampusClaw Chat</text>
      <view style="height: 16rpx" />
      <text class="section-title">{{ threadTitle }}</text>
      <view style="height: 8rpx" />
      <text class="section-desc">{{ socketStatusText }}</text>
      <view v-if="typingText" style="height: 8rpx" />
      <text v-if="typingText" class="helper">{{ typingText }}</text>
      <view style="height: 18rpx" />
      <view class="status-row">
        <view class="status-chip">
          <text>消息 {{ messages.length }}</text>
        </view>
        <view class="status-chip" :class="{ active: socketConnected }">
          <text>{{ socketConnected ? '实时连接中' : '连接未就绪' }}</text>
        </view>
        <view class="status-chip" :class="{ complete: peerOnline }">
          <text>{{ peerOnline ? '对方在线' : '对方离线' }}</text>
        </view>
      </view>
      <view v-if="threadId" style="height: 16rpx" />
      <button v-if="threadId" class="btn btn-ghost" size="mini" :disabled="hidingThread" @tap="handleHideThread">
        {{ hidingThread ? '隐藏中...' : '隐藏会话' }}
      </button>
    </view>

    <view v-if="messages.length" class="message-list section">
      <view
        v-for="message in messages"
        :key="message.id"
        class="message-bubble"
        :class="{ mine: isMine(message.sender.id) }"
      >
        <text class="helper">{{ getSenderName(message.sender) }}</text>
        <view style="height: 8rpx" />
        <text class="bubble-text" :class="{ withdrawn: message.is_withdrawn }">
          {{ getMessageBody(message) }}
        </text>
        <view style="height: 8rpx" />
        <view class="meta-row">
          <text class="helper">{{ formatDate(message.created_at) }}</text>
          <text v-if="isMine(message.sender.id)" class="helper">{{ message.is_read ? '已读' : '未读' }}</text>
        </view>
        <view v-if="isMine(message.sender.id) && !message.is_withdrawn" style="height: 10rpx" />
        <button
          v-if="isMine(message.sender.id) && !message.is_withdrawn"
          class="btn btn-ghost"
          size="mini"
          :disabled="withdrawingId === message.id"
          @tap="handleWithdrawMessage(message.id)"
        >
          {{ withdrawingId === message.id ? '撤回中...' : '撤回消息' }}
        </button>
      </view>
    </view>

    <view v-else class="card empty section">
      <text class="section-title" style="font-size: 32rpx">还没有聊天内容</text>
      <view style="height: 10rpx" />
      <text class="section-desc">发出第一条消息，开启这段新的连接。</text>
    </view>

    <view class="card composer">
      <view class="field">
        <text class="label">消息内容</text>
        <textarea
          v-model="messageBody"
          class="textarea"
          placeholder="输入你想发送的内容"
          maxlength="500"
          @input="handleTypingStart"
          @blur="handleTypingStop"
        />
      </view>
      <text v-if="errorMessage" class="error">{{ errorMessage }}</text>
      <button class="btn btn-primary" :disabled="sending || !threadId" @tap="handleSend">
        {{ sending ? '发送中...' : '发送消息' }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onHide, onLoad, onShow, onUnload } from '@dcloudio/uni-app'

import type { ChatMessage, ChatThread, UserSummary } from '../../types/api'
import {
  createChatThread,
  fetchChatMessages,
  hideChatThread,
  markChatThreadRead,
  sendChatMessage,
  withdrawChatMessage,
} from '../../services/chat'
import { currentUser, ensureAuthenticated } from '../../utils/auth'
import { switchTab } from '../../utils/navigation'
import { showToast } from '../../utils/ui'
import { connectAuthedSocket } from '../../utils/websocket'

type ChatSocketPayload =
  | { type: 'chat.ready'; thread_id: string }
  | { type: 'chat.error'; message: string }
  | { type: 'chat.message'; thread_id: string; message: ChatMessage }
  | { type: 'chat.read'; thread_id: string; message_ids: string[]; read_at: string }
  | { type: 'chat.presence'; thread_id: string; user_id: string; online: boolean }
  | { type: 'chat.typing'; thread_id: string; user_id: string; is_typing: boolean }

const threadId = ref('')
const targetUserId = ref('')
const thread = ref<ChatThread | null>(null)
const messages = ref<ChatMessage[]>([])
const messageBody = ref('')
const errorMessage = ref('')
const sending = ref(false)
const socketConnected = ref(false)
const reconnecting = ref(false)
const peerOnline = ref(false)
const peerTyping = ref(false)
const withdrawingId = ref('')
const hidingThread = ref(false)
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let peerTypingTimer: ReturnType<typeof setTimeout> | null = null
let selfTypingTimer: ReturnType<typeof setTimeout> | null = null
let chatSocket: UniApp.SocketTask | null = null

const threadTitle = computed(
  () => thread.value?.counterpart?.nickname || thread.value?.counterpart?.full_name || thread.value?.counterpart?.email || '聊天对象',
)

const socketStatusText = computed(() => {
  if (socketConnected.value) {
    return peerOnline.value ? '连接正常，对方当前在线。' : '连接正常，对方当前暂时离线。'
  }
  if (reconnecting.value) {
    return '正在重新连接聊天服务，请稍等。'
  }
  return '聊天服务暂未连接，页面会自动重试。'
})

const typingText = computed(() => (peerTyping.value ? `${threadTitle.value} 正在输入...` : ''))

onLoad(async (options) => {
  const incomingThreadId = typeof options?.threadId === 'string' ? options.threadId : ''
  const incomingTargetUserId = typeof options?.targetUserId === 'string' ? options.targetUserId : ''
  const targetPath = incomingThreadId
    ? `/pages/chat/index?threadId=${incomingThreadId}`
    : `/pages/chat/index?targetUserId=${incomingTargetUserId}`

  if (!ensureAuthenticated(targetPath)) {
    return
  }

  threadId.value = incomingThreadId
  targetUserId.value = incomingTargetUserId

  if (!threadId.value && targetUserId.value) {
    await bootstrapThread()
    return
  }

  await loadMessages()
})

onShow(() => {
  if (!threadId.value) {
    return
  }
  loadMessages()
  connectChatSocket()
})

onHide(() => {
  teardownSocket()
})

onUnload(() => {
  teardownSocket()
})

async function bootstrapThread() {
  try {
    const created = await createChatThread({
      target_user_id: targetUserId.value,
      source_type: 'dating_match',
    })
    threadId.value = created.id
    thread.value = created
    await loadMessages()
    connectChatSocket()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '创建聊天失败')
  }
}

async function loadMessages() {
  if (!threadId.value) {
    return
  }
  try {
    const response = await fetchChatMessages(threadId.value)
    thread.value = response.thread
    messages.value = response.messages
    await markChatThreadRead(threadId.value)
  } catch (error) {
    showToast(error instanceof Error ? error.message : '加载聊天记录失败')
  }
}

function connectChatSocket() {
  if (chatSocket || !threadId.value) {
    return
  }

  reconnecting.value = false
  chatSocket = connectAuthedSocket(`/ws/chat/${threadId.value}/`, {
    onOpen() {
      socketConnected.value = true
      reconnecting.value = false
    },
    onClose() {
      chatSocket = null
      socketConnected.value = false
      scheduleReconnect()
    },
    onError() {
      socketConnected.value = false
    },
    onMessage(data) {
      handleSocketPayload(data as ChatSocketPayload)
    },
  })
}

function handleSocketPayload(payload: ChatSocketPayload) {
  if (payload.type === 'chat.ready') {
    return
  }

  if (payload.type === 'chat.error') {
    showToast(payload.message || '聊天连接异常')
    return
  }

  if (payload.type === 'chat.message') {
    upsertMessage(payload.message)
    if (!isMine(payload.message.sender.id)) {
      markChatThreadRead(threadId.value).catch(() => undefined)
    }
    return
  }

  if (payload.type === 'chat.read') {
    const readIds = new Set(payload.message_ids)
    messages.value = messages.value.map((message) =>
      readIds.has(message.id)
        ? {
            ...message,
            is_read: true,
            read_at: payload.read_at,
          }
        : message,
    )
    return
  }

  if (payload.type === 'chat.presence' && payload.user_id !== currentUser.value?.id) {
    peerOnline.value = payload.online
    return
  }

  if (payload.type === 'chat.typing' && payload.user_id !== currentUser.value?.id) {
    peerTyping.value = payload.is_typing
    if (peerTypingTimer) {
      clearTimeout(peerTypingTimer)
      peerTypingTimer = null
    }
    if (payload.is_typing) {
      peerTypingTimer = setTimeout(() => {
        peerTyping.value = false
      }, 2500)
    }
  }
}

function scheduleReconnect() {
  if (reconnectTimer || !threadId.value) {
    return
  }

  reconnecting.value = true
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    connectChatSocket()
  }, 1800)
}

function teardownSocket() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (peerTypingTimer) {
    clearTimeout(peerTypingTimer)
    peerTypingTimer = null
  }
  if (selfTypingTimer) {
    clearTimeout(selfTypingTimer)
    selfTypingTimer = null
  }

  reconnecting.value = false
  socketConnected.value = false
  peerOnline.value = false
  peerTyping.value = false
  chatSocket?.close({})
  chatSocket = null
}

function sendTypingEvent(type: 'typing.start' | 'typing.stop') {
  if (!chatSocket) {
    return
  }
  chatSocket.send({
    data: JSON.stringify({ type }),
  })
}

function handleTypingStart() {
  sendTypingEvent('typing.start')
  if (selfTypingTimer) {
    clearTimeout(selfTypingTimer)
  }
  selfTypingTimer = setTimeout(() => {
    sendTypingEvent('typing.stop')
    selfTypingTimer = null
  }, 1200)
}

function handleTypingStop() {
  if (selfTypingTimer) {
    clearTimeout(selfTypingTimer)
    selfTypingTimer = null
  }
  sendTypingEvent('typing.stop')
}

function upsertMessage(incoming: ChatMessage) {
  const exists = messages.value.some((item) => item.id === incoming.id)
  if (exists) {
    messages.value = messages.value.map((item) => (item.id === incoming.id ? incoming : item))
    return
  }

  messages.value = [...messages.value, incoming].sort((first, second) => first.created_at.localeCompare(second.created_at))
}

async function handleSend() {
  errorMessage.value = ''
  const body = messageBody.value.trim()

  if (!body) {
    errorMessage.value = '请输入消息内容'
    return
  }

  if (!threadId.value) {
    errorMessage.value = '当前会话还没有准备好'
    return
  }

  sending.value = true
  try {
    await sendChatMessage(threadId.value, { body })
    messageBody.value = ''
    handleTypingStop()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '发送消息失败'
  } finally {
    sending.value = false
  }
}

async function handleWithdrawMessage(messageId: string) {
  if (!threadId.value) {
    return
  }
  withdrawingId.value = messageId
  try {
    const updated = await withdrawChatMessage(threadId.value, messageId)
    upsertMessage(updated)
    showToast('消息已撤回', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '撤回失败')
  } finally {
    withdrawingId.value = ''
  }
}

async function handleHideThread() {
  if (!threadId.value) {
    return
  }
  hidingThread.value = true
  try {
    await hideChatThread(threadId.value)
    showToast('会话已隐藏', 'success')
    switchTab('/pages/messages/index')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '隐藏会话失败')
  } finally {
    hidingThread.value = false
  }
}

function isMine(senderId: string) {
  return senderId === (currentUser.value?.id ?? '')
}

function getSenderName(sender: UserSummary) {
  return sender.nickname || sender.full_name || sender.email || '校园用户'
}

function getMessageBody(message: ChatMessage) {
  if (!message.is_withdrawn) {
    return message.body
  }
  return isMine(message.sender.id) ? '你撤回了一条消息' : '对方撤回了一条消息'
}

function formatDate(value: string) {
  return value.replace('T', ' ').slice(0, 16)
}
</script>

<style scoped lang="scss">
.status-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
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

.message-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.message-bubble {
  max-width: 88%;
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.88);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
}

.message-bubble.mine {
  margin-left: auto;
  background: rgba(241, 107, 79, 0.12);
}

.bubble-text {
  font-size: 28rpx;
  line-height: 1.8;
  color: #102133;
  white-space: pre-wrap;
}

.bubble-text.withdrawn {
  color: #6b7280;
  font-style: italic;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.composer {
  position: sticky;
  bottom: 24rpx;
}
</style>
