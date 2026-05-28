<template>
  <view class="container">
    <view class="header">
      <view class="header-left">
        <text class="header-title">AI 助手</text>
        <text class="header-desc">CampusClaw 智能对话</text>
      </view>
      <button class="btn-new" @tap="reloadSession">
        <text>新对话</text>
      </button>
    </view>

    <scroll-view
      class="message-list"
      scroll-y
      :scroll-top="scrollTop"
      enhanced
      :show-scrollbar="false"
    >
      <view v-if="!messages.length && !loading" class="empty-state">
        <text class="empty-title">你好，我是 AI 助手</text>
        <view style="height: 16rpx" />
        <text class="empty-desc">有什么我可以帮助你的吗？</text>
        <view style="height: 24rpx" />
        <view class="quick-replies">
          <view
            v-for="(reply, index) in quickReplies"
            :key="index"
            class="quick-reply-item"
            @tap="handleQuickReply(reply)"
          >
            <text>{{ reply }}</text>
          </view>
        </view>
      </view>

      <view
        v-for="(message) in messages"
        :key="message.id"
        class="message-item"
        :class="{ 'message-assistant': message.role === 'assistant', 'message-user': message.role === 'user' }"
      >
        <view v-if="message.role === 'assistant'" class="avatar avatar-assistant">
          <text>AI</text>
        </view>
        <view v-else class="avatar avatar-user">
          <text>我</text>
        </view>
        <view class="message-content">
          <text class="message-text">{{ message.body }}</text>
          <text class="message-time">{{ formatTime(message.created_at) }}</text>
        </view>
      </view>

      <view v-if="loading" class="message-item message-assistant">
        <view class="avatar avatar-assistant">
          <text>AI</text>
        </view>
        <view class="message-content">
          <text class="message-text loading-text">思考中...</text>
        </view>
      </view>
    </scroll-view>

    <view v-if="actions.length" class="action-list">
      <AssistantActionCard
        v-for="action in actions"
        :key="action.id"
        :action="action"
        :busy="actionBusyId === action.id"
        @execute="handleExecuteAction"
        @fill="handleFillAction"
        @generate="handleGenerateOnly"
      />
    </view>

    <view class="input-area">
      <textarea
        v-model="inputText"
        class="input-field"
        placeholder="输入你的问题..."
        :maxlength="500"
        :auto-height="true"
        confirm-type="send"
        cursor-color="#f16b4f"
        :show-confirm-bar="false"
        @confirm="handleSend"
      />
      <button
        class="send-btn"
        :class="{ active: canSend }"
        :disabled="!canSend"
        @tap="handleSend"
      >
        <text class="send-icon">↑</text>
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

import AssistantActionCard from '../../components/assistant/AssistantActionCard.vue'
import type { AssistantActionProposal, AssistantMessage } from '../../types/api'
import { createAssistantSession, executeAssistantAction, fetchAssistantActions, fetchAssistantMessages, fetchAssistantSessions, sendAssistantMessage } from '../../services/assistant'
import { ensureAuthenticated } from '../../utils/auth'
import { saveAssistantDraft } from '../../utils/assistantDraft'
import { showToast } from '../../utils/ui'

const sessionId = ref<string | null>(null)
const messages = ref<AssistantMessage[]>([])
const actions = ref<AssistantActionProposal[]>([])
const inputText = ref('')
const loading = ref(false)
const actionBusyId = ref('')
const scrollTop = ref(0)

const quickReplies = [
  '帮我推荐一个比赛',
  '如何发布组队帖子？',
  '论坛使用帮助',
  '恋爱匹配说明',
]

const canSend = computed(() => inputText.value.trim().length > 0 && !loading.value)

onLoad(async () => {
  if (!ensureAuthenticated('/pages/assistant/index')) {
    return
  }
  await loadOrCreateSession()
})

async function loadOrCreateSession() {
  try {
    const sessions = await fetchAssistantSessions()
    if (sessions.length > 0) {
      sessionId.value = sessions[0].id
      await refreshSessionState()
    } else {
      const newSession = await createAssistantSession({
        page_type: 'general',
        title: '新对话',
      })
      sessionId.value = newSession.id
      actions.value = []
    }
  } catch {
    showToast('加载会话失败')
  }
  scrollToBottom()
}

async function refreshSessionState() {
  if (!sessionId.value) {
    return
  }
  const [msgs, nextActions] = await Promise.all([
    fetchAssistantMessages(sessionId.value),
    fetchAssistantActions(sessionId.value),
  ])
  messages.value = msgs
  actions.value = nextActions
}

async function handleSend() {
  if (!canSend.value || !sessionId.value) {
    return
  }

  const text = inputText.value.trim()
  inputText.value = ''
  loading.value = true

  const tempUserMessage: AssistantMessage = {
    id: 'temp-' + Date.now(),
    role: 'user',
    body: text,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
  messages.value.push(tempUserMessage)
  const previousRealMessageCount = messages.value.filter((message) => !message.id.startsWith('temp-')).length
  scrollToBottom()

  try {
    const response = await sendAssistantMessage(sessionId.value, { body: text })
    messages.value = messages.value.filter((m) => m.id !== tempUserMessage.id)
    messages.value.push(response.user_message)
    messages.value.push(response.assistant_message)
    actions.value = response.actions ?? []
  } catch (error) {
    try {
      await refreshSessionState()
      if (messages.value.length <= previousRealMessageCount) {
        showToast(error instanceof Error ? error.message : '发送失败')
      }
    } catch {
      showToast(error instanceof Error ? error.message : '发送失败')
      messages.value = messages.value.filter((m) => m.id !== tempUserMessage.id)
    }
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function handleQuickReply(text: string) {
  inputText.value = text
  handleSend()
}

async function reloadSession() {
  try {
    const newSession = await createAssistantSession({
      page_type: 'general',
      title: '新对话',
    })
    sessionId.value = newSession.id
    messages.value = []
    actions.value = []
  } catch {
    showToast('创建新对话失败')
  }
}

function openTargetPage(targetPage: string) {
  if (!targetPage) {
    return
  }
  if (['/pages/forum/index', '/pages/publish/index', '/pages/messages/index', '/pages/me/index'].includes(targetPage)) {
    uni.switchTab({ url: targetPage })
    return
  }
  uni.navigateTo({ url: targetPage })
}

function handleFillAction(action: AssistantActionProposal) {
  saveAssistantDraft(action)
  showToast('已填入草稿', 'success')
  openTargetPage(action.target_page)
}

function handleGenerateOnly(action: AssistantActionProposal) {
  actions.value = actions.value.filter((item) => item.id !== action.id)
}

function handleExecuteAction(action: AssistantActionProposal) {
  uni.showModal({
    title: '确认执行 AI 动作',
    content: `将执行：${action.title}。请确认内容无误后继续。`,
    confirmText: '确认执行',
    success: async (result) => {
      if (!result.confirm) {
        return
      }
      actionBusyId.value = action.id
      try {
        const response = await executeAssistantAction(action.id)
        actions.value = actions.value.map((item) => (item.id === action.id ? response.action : item))
        showToast(response.result.message || '执行成功', 'success')
        if (response.result.target_page) {
          openTargetPage(String(response.result.target_page))
        }
      } catch (error) {
        showToast(error instanceof Error ? error.message : '执行失败')
      } finally {
        actionBusyId.value = ''
      }
    },
  })
}

function scrollToBottom() {
  setTimeout(() => {
    scrollTop.value = 0
  }, 50)
}

function formatTime(value: string) {
  const date = new Date(value)
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}
</script>

<style scoped lang="scss">
.container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: #f7f1e8;
  padding-bottom: calc(112rpx + env(safe-area-inset-bottom));
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 32rpx;
  padding-top: calc(20rpx + env(safe-area-inset-top));
  background: #fffaf5;
  border-bottom: 1rpx solid rgba(16, 33, 51, 0.08);
}

.header-left {
  display: flex;
  flex-direction: column;
}

.header-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #102133;
}

.header-desc {
  font-size: 22rpx;
  color: #7a7f87;
  margin-top: 4rpx;
}

.btn-new {
  padding: 12rpx 24rpx;
  background: rgba(241, 107, 79, 0.1);
  border: 1rpx solid rgba(241, 107, 79, 0.3);
  border-radius: 24rpx;
  font-size: 24rpx;
  color: #f16b4f;
  font-weight: 600;
}

.btn-new::after {
  border: 0;
}

.message-list {
  flex: 1;
  padding: 24rpx;
  min-height: 0;
  padding-bottom: 156rpx;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60rpx 32rpx;
}

.empty-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #102133;
}

.empty-desc {
  font-size: 28rpx;
  color: #7a7f87;
}

.quick-replies {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 16rpx;
}

.quick-reply-item {
  padding: 14rpx 22rpx;
  background: rgba(255, 255, 255, 0.88);
  border: 1rpx solid rgba(16, 33, 51, 0.12);
  border-radius: 999rpx;
  font-size: 24rpx;
  color: #102133;
}

.message-item {
  display: flex;
  margin-bottom: 24rpx;
  align-items: flex-start;
}

.message-assistant {
  flex-direction: row;
}

.message-user {
  flex-direction: row-reverse;
}

.avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-assistant {
  background: linear-gradient(135deg, #f16b4f, #ff8a6b);
  color: #fff;
  font-size: 22rpx;
  font-weight: 700;
}

.avatar-user {
  background: rgba(241, 107, 79, 0.18);
  color: #f16b4f;
  font-size: 22rpx;
  font-weight: 700;
}

.message-content {
  max-width: 70%;
  margin: 0 16rpx;
  padding: 18rpx 22rpx;
  border-radius: 24rpx;
}

.message-assistant .message-content {
  background: rgba(255, 255, 255, 0.88);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
}

.message-user .message-content {
  background: rgba(241, 107, 79, 0.12);
}

.message-text {
  font-size: 28rpx;
  line-height: 1.6;
  color: #102133;
  white-space: pre-wrap;
}

.message-time {
  display: block;
  font-size: 20rpx;
  color: #7a7f87;
  margin-top: 8rpx;
  text-align: right;
}

.loading-text {
  color: #7a7f87;
  font-style: italic;
}

.input-area {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: flex-end;
  padding: 12rpx 24rpx calc(12rpx + env(safe-area-inset-bottom));
  background: #fffaf5;
  border-top: 1rpx solid rgba(16, 33, 51, 0.08);
  gap: 16rpx;
}

.action-list {
  flex-shrink: 0;
  max-height: 300rpx;
  padding: 0 24rpx 16rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  overflow: auto;
}

.input-field {
  flex: 1;
  min-height: 44rpx;
  max-height: 168rpx;
  padding: 14rpx 18rpx;
  border-radius: 28rpx;
  background: rgba(255, 250, 245, 0.98);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
  font-size: 27rpx;
  color: #102133;
  line-height: 38rpx;
  caret-color: #f16b4f;
  cursor-color: #f16b4f;
  overflow-y: auto;
}

.send-btn {
  width: 64rpx;
  height: 64rpx;
  padding: 0;
  background: #ccc;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.send-btn::after {
  border: 0;
}

.send-icon {
  font-size: 32rpx;
  color: #fff;
  font-weight: 700;
}

.send-btn.active {
  background: #f16b4f;
}
</style>
