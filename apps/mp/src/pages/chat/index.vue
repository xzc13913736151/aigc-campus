<template>
  <view class="container">
    <view class="chat-header">
      <view class="header-copy">
        <text class="chat-title">{{ threadTitle }}</text>
        <view style="height: 6rpx" />
        <text class="chat-subtitle">{{ typingText || compactSocketStatusText }}</text>
      </view>
      <button v-if="threadId" class="header-action" :disabled="hidingThread" @tap="handleHideThread">
        {{ hidingThread ? '处理中' : '隐藏' }}
      </button>
    </view>

    <scroll-view
      v-if="messages.length"
      class="message-list"
      scroll-y
      enhanced
      :show-scrollbar="false"
      :scroll-top="scrollTop"
    >
      <block v-for="item in messageItems" :key="item.key">
        <view v-if="item.type === 'time'" class="time-divider">
          <text>{{ item.label }}</text>
        </view>
        <view
          v-else
          :id="`message-${item.message.id}`"
          class="message-row"
          :class="{ mine: isMine(item.message.sender.id) }"
        >
          <view class="avatar">
            <text>{{ getSenderInitial(item.message.sender) }}</text>
          </view>
          <view class="message-stack">
            <view class="message-bubble" :class="{ image: isImageMessage(item.message), withdrawn: item.message.is_withdrawn }">
              <image
                v-if="isImageMessage(item.message) && !item.message.is_withdrawn && !imageLoadFailed[item.message.id]"
                class="message-image"
                :src="getDisplayImageUrl(item.message)"
                mode="aspectFill"
                @error="handleMessageImageError(item.message)"
                @tap="previewMessageImage(item.message)"
              />
              <view
                v-else-if="isImageMessage(item.message) && !item.message.is_withdrawn"
                class="image-fallback"
                @tap="previewMessageImage(item.message)"
              >
                <text>点击查看图片</text>
              </view>
              <text v-else class="bubble-text" :class="{ withdrawn: item.message.is_withdrawn }">
                {{ getMessageBody(item.message) }}
              </text>
            </view>
            <view class="message-meta">
              <text v-if="isMine(item.message.sender.id)" :class="{ failed: item.message.local_status === 'failed' }">
                {{ getMessageStatusText(item.message) }}
              </text>
            </view>
          </view>
        </view>
      </block>
      <view id="chat-bottom-anchor" class="chat-bottom-anchor" />
    </scroll-view>

    <view v-else class="empty-chat">
      <text class="section-title" style="font-size: 32rpx">还没有聊天内容</text>
      <view style="height: 10rpx" />
      <text class="section-desc">发出第一条消息，开启这段新的连接。</text>
    </view>

    <view class="composer">
      <button class="image-button" :disabled="sendingImage || !threadId" @tap="chooseAndSendImage">
        {{ sendingImage ? '...' : '+' }}
      </button>
      <textarea
        v-model="messageBody"
        class="chat-input"
        auto-height
        confirm-type="send"
        cursor-color="#f16b4f"
        :show-confirm-bar="false"
        placeholder="输入消息"
        maxlength="500"
        @input="handleTypingStart"
        @blur="handleTypingStop"
        @confirm="handleSend"
      />
      <button class="send-button" :class="{ disabled: !canSendText }" :disabled="!canSendText" @tap="handleSend">
        {{ sending ? '...' : '发送' }}
      </button>
      <text v-if="errorMessage" class="error composer-error">{{ errorMessage }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { onHide, onLoad, onShow, onUnload } from '@dcloudio/uni-app'

import { BASE_URL } from '../../constants'
import type { ChatMessage, ChatThread, UserSummary } from '../../types/api'
import {
  createChatThread,
  fetchChatMessages,
  hideChatThread,
  markChatThreadRead,
  sendChatMessage,
  uploadChatImage,
} from '../../services/chat'
import { currentUser, ensureAuthenticated } from '../../utils/auth'
import { consumeAssistantDraft } from '../../utils/assistantDraft'
import { switchTab } from '../../utils/navigation'
import { showToast } from '../../utils/ui'
import { connectAuthedSocket } from '../../utils/websocket'

type LocalChatMessage = ChatMessage & {
  local_status?: 'sending' | 'failed'
}

type ChatSocketPayload =
  | { type: 'chat.ready'; thread_id: string }
  | { type: 'chat.error'; message: string }
  | { type: 'chat.message'; thread_id: string; message: ChatMessage }
  | { type: 'chat.read'; thread_id: string; message_ids: string[]; read_at: string }
  | { type: 'chat.presence'; thread_id: string; user_id: string; online: boolean }
  | { type: 'chat.typing'; thread_id: string; user_id: string; is_typing: boolean }

const threadId = ref('')
const targetUserId = ref('')
const sourceType = ref('')
const sourceId = ref('')
const thread = ref<ChatThread | null>(null)
const messages = ref<LocalChatMessage[]>([])
const messageBody = ref('')
const errorMessage = ref('')
const sending = ref(false)
const sendingImage = ref(false)
const socketConnected = ref(false)
const reconnecting = ref(false)
const peerOnline = ref(false)
const peerTyping = ref(false)
const hidingThread = ref(false)
const scrollTop = ref(0)
const scrollBottomSeed = ref(100000)
const localImageUrls = ref<Record<string, string>>({})
const imageLoadFailed = ref<Record<string, boolean>>({})

let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let peerTypingTimer: ReturnType<typeof setTimeout> | null = null
let selfTypingTimer: ReturnType<typeof setTimeout> | null = null
let chatSocket: UniApp.SocketTask | null = null

const threadTitle = computed(
  () => thread.value?.counterpart?.nickname || thread.value?.counterpart?.full_name || thread.value?.counterpart?.claw_id || '聊天对象',
)
const typingText = computed(() => (peerTyping.value ? `${threadTitle.value} 正在输入...` : ''))
const compactSocketStatusText = computed(() => {
  if (socketConnected.value) {
    return peerOnline.value ? '对方在线' : '已连接'
  }
  return reconnecting.value ? '正在重连' : '未连接'
})
const canSendText = computed(() => Boolean(messageBody.value.trim()) && !sending.value && Boolean(threadId.value))
const messageItems = computed(() => {
  const items: Array<
    | { type: 'time'; key: string; label: string }
    | { type: 'message'; key: string; message: LocalChatMessage }
  > = []
  let lastTimestamp = 0
  messages.value.forEach((message) => {
    const timestamp = new Date(message.created_at).getTime()
    if (!lastTimestamp || timestamp - lastTimestamp > 5 * 60 * 1000) {
      items.push({
        type: 'time',
        key: `time-${message.id}`,
        label: formatDate(message.created_at),
      })
    }
    items.push({ type: 'message', key: message.id, message })
    lastTimestamp = timestamp
  })
  return items
})

watch(
  () => messages.value.length,
  () => {
    void scrollToBottom()
  },
)

watch(
  () => messages.value.map((message) => `${message.id}:${message.image_url}`).join('|'),
  () => {
    void cacheMessageImages()
  },
)

onLoad(async (options) => {
  const incomingThreadId = typeof options?.threadId === 'string' ? options.threadId : ''
  const incomingTargetUserId = typeof options?.targetUserId === 'string' ? options.targetUserId : ''
  const incomingSourceType = typeof options?.sourceType === 'string' ? options.sourceType : ''
  const incomingSourceId = typeof options?.sourceId === 'string' ? options.sourceId : ''
  const targetPath = incomingThreadId
    ? `/pages/chat/index?threadId=${incomingThreadId}`
    : `/pages/chat/index?targetUserId=${incomingTargetUserId}`

  if (!ensureAuthenticated(targetPath)) {
    return
  }

  threadId.value = incomingThreadId
  targetUserId.value = incomingTargetUserId
  sourceType.value = incomingSourceType
  sourceId.value = incomingSourceId

  if (!threadId.value && targetUserId.value) {
    await bootstrapThread()
    return
  }

  await loadMessages()
})

onShow(() => {
  applyAssistantDraft()
  if (!threadId.value) {
    return
  }
  void loadMessages()
  connectChatSocket()
})

onHide(() => {
  teardownSocket()
})

onUnload(() => {
  teardownSocket()
})

function applyAssistantDraft() {
  const draft = consumeAssistantDraft('/pages/chat/index', ['chat_message_send'])
  if (!draft) {
    return
  }
  const payload = draft.fill_payload
  const targetThreadId = typeof payload.thread_id === 'string' ? payload.thread_id : ''
  if (targetThreadId && threadId.value && targetThreadId !== threadId.value) {
    return
  }
  messageBody.value = typeof payload.body === 'string' ? payload.body : messageBody.value
  showToast('AI 已填入聊天草稿', 'success')
}

async function bootstrapThread() {
  try {
    const created = await createChatThread({
      target_user_id: targetUserId.value,
      source_type: sourceType.value || 'direct',
      source_id: sourceId.value,
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
    void scrollToBottom()
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
  if (reconnectTimer) clearTimeout(reconnectTimer)
  if (peerTypingTimer) clearTimeout(peerTypingTimer)
  if (selfTypingTimer) clearTimeout(selfTypingTimer)
  reconnectTimer = null
  peerTypingTimer = null
  selfTypingTimer = null
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
  chatSocket.send({ data: JSON.stringify({ type }) })
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

function upsertMessage(incoming: LocalChatMessage) {
  const exists = messages.value.some((item) => item.id === incoming.id)
  if (exists) {
    messages.value = messages.value.map((item) => (item.id === incoming.id ? incoming : item))
    return
  }
  messages.value = [...messages.value, incoming].sort((first, second) => first.created_at.localeCompare(second.created_at))
  void scrollToBottom()
  void cacheMessageImages()
}

function createLocalTextMessage(body: string): LocalChatMessage {
  const now = new Date().toISOString()
  return {
    id: `local-${Date.now()}`,
    sender: currentUser.value as UserSummary,
    body,
    image_url: '',
    is_read: false,
    read_at: null,
    is_withdrawn: false,
    withdrawn_at: null,
    created_at: now,
    updated_at: now,
    local_status: 'sending',
  }
}

function replaceLocalMessage(localId: string, realMessage: ChatMessage) {
  messages.value = messages.value.map((message) => (message.id === localId ? realMessage : message))
  void scrollToBottom()
}

function markLocalMessageFailed(localId: string) {
  messages.value = messages.value.map((message) =>
    message.id === localId
      ? {
          ...message,
          local_status: 'failed',
        }
      : message,
  )
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

  const localMessage = createLocalTextMessage(body)
  messages.value = [...messages.value, localMessage]
  messageBody.value = ''
  handleTypingStop()
  void scrollToBottom()

  sending.value = true
  try {
    const message = await sendChatMessage(threadId.value, { body })
    replaceLocalMessage(localMessage.id, message)
  } catch (error) {
    markLocalMessageFailed(localMessage.id)
    errorMessage.value = error instanceof Error ? error.message : '发送消息失败'
  } finally {
    sending.value = false
  }
}

async function chooseAndSendImage() {
  if (!threadId.value || sendingImage.value) {
    return
  }

  sendingImage.value = true
  errorMessage.value = ''
  try {
    const media = (await uni.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sizeType: ['compressed'],
      sourceType: ['album'],
    })) as unknown as UniApp.ChooseMediaSuccessCallbackResult
    const filePath = media.tempFiles?.[0]?.tempFilePath
    if (!filePath) {
      return
    }
    const message = await uploadChatImage(threadId.value, filePath)
    upsertMessage(message)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '图片发送失败'
  } finally {
    sendingImage.value = false
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

function getMessageStatusText(message: LocalChatMessage) {
  if (message.local_status === 'sending') {
    return '发送中'
  }
  if (message.local_status === 'failed') {
    return '发送失败'
  }
  return message.is_read ? '已读' : '未读'
}

function getSenderName(sender: UserSummary) {
  return sender.nickname || sender.full_name || sender.claw_id || '校园用户'
}

function getSenderInitial(sender: UserSummary) {
  return getSenderName(sender).slice(0, 1)
}

function isImageMessage(message: ChatMessage) {
  return Boolean(message.image_url)
}

async function cacheMessageImages() {
  const imageMessages = messages.value.filter((message) => isImageMessage(message) && !localImageUrls.value[message.id])
  for (const message of imageMessages) {
    const remoteUrl = getImageUrl(message.image_url)
    if (!remoteUrl || !/^https?:\/\//i.test(remoteUrl)) {
      continue
    }
    try {
      const result = await uni.downloadFile({ url: remoteUrl })
      if (result.statusCode && result.statusCode >= 200 && result.statusCode < 300 && result.tempFilePath) {
        localImageUrls.value = {
          ...localImageUrls.value,
          [message.id]: result.tempFilePath,
        }
        imageLoadFailed.value = {
          ...imageLoadFailed.value,
          [message.id]: false,
        }
      }
    } catch (error) {
      console.warn('chat image download failed', remoteUrl, error)
      continue
    }
  }
}

function getMessageBody(message: ChatMessage) {
  if (!message.is_withdrawn) {
    return message.body || '[图片]'
  }
  return isMine(message.sender.id) ? '你撤回了一条消息' : '对方撤回了一条消息'
}

function getImageUrl(url: string) {
  if (!url || /^https?:\/\//i.test(url)) {
    return url
  }
  return `${BASE_URL.replace(/\/api\/v1\/?$/, '')}${url}`
}

function getDisplayImageUrl(message: ChatMessage) {
  return localImageUrls.value[message.id] || getImageUrl(message.image_url)
}

function handleMessageImageError(message: ChatMessage) {
  const remoteUrl = getImageUrl(message.image_url)
  console.warn('chat image render failed', {
    messageId: message.id,
    remoteUrl,
    localUrl: localImageUrls.value[message.id] || '',
  })
  imageLoadFailed.value = {
    ...imageLoadFailed.value,
    [message.id]: true,
  }
}

function previewMessageImage(message: ChatMessage) {
  const imageUrl = localImageUrls.value[message.id] || getImageUrl(message.image_url)
  if (!imageUrl) {
    return
  }
  uni.previewImage({ urls: [imageUrl], current: imageUrl })
}

async function scrollToBottom() {
  await nextTick()
  scrollBottomSeed.value += 100000
  scrollTop.value = scrollBottomSeed.value
}

function formatDate(value: string) {
  return value.replace('T', ' ').slice(0, 16)
}
</script>

<style scoped lang="scss">
.container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f3eee6;
  padding: 0 0 calc(116rpx + env(safe-area-inset-bottom));
}

.chat-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  padding: calc(20rpx + env(safe-area-inset-top)) 28rpx 20rpx;
  background: rgba(255, 250, 245, 0.96);
  border-bottom: 1rpx solid rgba(16, 33, 51, 0.08);
}

.header-copy {
  min-width: 0;
}

.chat-title {
  display: block;
  color: #102133;
  font-size: 34rpx;
  font-weight: 800;
}

.chat-subtitle {
  color: #7a7f87;
  font-size: 22rpx;
}

.header-action {
  flex-shrink: 0;
  height: 56rpx;
  min-height: 56rpx;
  padding: 0 22rpx;
  margin: 0;
  border: 0;
  border-radius: 999rpx;
  background: rgba(16, 33, 51, 0.08);
  color: #44515f;
  font-size: 23rpx;
  line-height: 1;
}

.header-action::after {
  border: 0;
}

.message-list {
  flex: 1;
  min-height: 0;
  padding: 26rpx 24rpx;
  box-sizing: border-box;
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
  margin-bottom: 24rpx;
}

.time-divider {
  display: flex;
  justify-content: center;
  margin: 8rpx 0 22rpx;
}

.time-divider text {
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(16, 33, 51, 0.07);
  color: #8b929a;
  font-size: 20rpx;
}

.message-row.mine {
  flex-direction: row-reverse;
}

.avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 18rpx;
  background: rgba(16, 33, 51, 0.1);
  color: #102133;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 800;
  flex-shrink: 0;
}

.message-row.mine .avatar {
  background: rgba(241, 107, 79, 0.16);
  color: #f16b4f;
}

.message-stack {
  max-width: 72%;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.message-row.mine .message-stack {
  align-items: flex-end;
}

.message-bubble {
  padding: 18rpx 22rpx;
  border-radius: 8rpx 24rpx 24rpx 24rpx;
  background: #fff;
  border: 1rpx solid rgba(16, 33, 51, 0.06);
}

.message-row.mine .message-bubble {
  border-radius: 24rpx 8rpx 24rpx 24rpx;
  background: #f16b4f;
  border-color: #f16b4f;
}

.message-bubble.image {
  padding: 6rpx;
  background: transparent;
  border: 0;
}

.message-bubble.withdrawn {
  background: rgba(255, 255, 255, 0.65);
  border-color: rgba(16, 33, 51, 0.08);
}

.bubble-text {
  font-size: 29rpx;
  line-height: 1.6;
  color: #102133;
  white-space: pre-wrap;
}

.message-row.mine .bubble-text {
  color: #fff;
}

.bubble-text.withdrawn {
  color: #7a7f87;
  font-style: italic;
}

.message-image {
  width: 320rpx;
  height: 320rpx;
  border-radius: 18rpx;
  background: rgba(16, 33, 51, 0.08);
  display: block;
}

.image-fallback {
  width: 320rpx;
  height: 220rpx;
  border-radius: 18rpx;
  background: rgba(16, 33, 51, 0.08);
  border: 1rpx dashed rgba(16, 33, 51, 0.18);
  color: #6b7280;
  font-size: 26rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-meta {
  display: flex;
  gap: 12rpx;
  color: #9aa1aa;
  font-size: 20rpx;
  min-height: 24rpx;
}

.message-meta .failed {
  color: #ef4444;
}

.empty-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80rpx 36rpx;
  text-align: center;
}

.composer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: flex-end;
  gap: 14rpx;
  padding: 14rpx 20rpx calc(14rpx + env(safe-area-inset-bottom));
  background: rgba(255, 250, 245, 0.98);
  border-top: 1rpx solid rgba(16, 33, 51, 0.08);
  box-shadow: 0 -16rpx 42rpx rgba(16, 33, 51, 0.08);
  box-sizing: border-box;
}

.image-button,
.send-button {
  flex-shrink: 0;
  height: 68rpx;
  min-height: 68rpx;
  margin: 0;
  border: 0;
  border-radius: 999rpx;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-button {
  width: 68rpx;
  padding: 0;
  background: rgba(16, 33, 51, 0.1);
  color: #102133;
  font-size: 42rpx;
  font-weight: 500;
}

.send-button {
  min-width: 104rpx;
  padding: 0 24rpx;
  background: #f16b4f;
  color: #fff;
  font-size: 25rpx;
  font-weight: 800;
}

.send-button.disabled {
  background: rgba(16, 33, 51, 0.12);
  color: #8a929c;
}

.image-button::after,
.send-button::after {
  border: 0;
}

.chat-input {
  flex: 1;
  min-height: 44rpx;
  max-height: 168rpx;
  padding: 13rpx 18rpx;
  border-radius: 24rpx;
  background: #fff;
  border: 1rpx solid rgba(16, 33, 51, 0.08);
  color: #102133;
  font-size: 28rpx;
  line-height: 40rpx;
  caret-color: #f16b4f;
  cursor-color: #f16b4f;
  overflow-y: auto;
}

.composer-error {
  position: absolute;
  left: 24rpx;
  bottom: calc(94rpx + env(safe-area-inset-bottom));
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(239, 68, 68, 0.1);
}

.chat-bottom-anchor {
  height: 18rpx;
}
</style>
