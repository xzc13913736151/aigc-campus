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
      scroll-with-animation
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
        <AssistantPresentationCard
          v-if="message.role === 'assistant' && message.presentation?.type === 'draft'"
          class="message-presentation"
          :presentation="message.presentation"
          @suggest="handleQuickReply"
          @custom="handleCustomField"
        />
        <view v-else class="message-content">
          <text class="message-text">{{ message.body }}</text>
          <text class="message-time">{{ formatTime(message.created_at) }}</text>
        </view>
      </view>

      <view v-if="loading" id="assistant-thinking" class="message-item message-assistant">
        <view class="avatar avatar-assistant">
          <text>AI</text>
        </view>
        <view class="message-content">
          <text class="message-text loading-text">思考中...</text>
        </view>
      </view>
      <view v-if="actions.length" id="assistant-action-list" class="action-list">
        <AssistantActionCard
          v-for="action in actions"
          :key="action.id"
          :action="action"
          :busy="actionBusyId === action.id"
          @fill="handleFillAction"
          @revise="handleReviseAction"
          @recommend="handleRecommendationAction"
        />
      </view>

      <view class="bottom-anchor" />
    </scroll-view>

    <view class="input-area">
      <textarea
        v-model="inputText"
        class="input-field"
        placeholder="输入你的问题..."
        :maxlength="500"
        :auto-height="true"
        confirm-type="send"
        cursor-color="#c15f3c"
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
import { computed, nextTick, ref, watch } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

import AssistantActionCard from '../../components/assistant/AssistantActionCard.vue'
import AssistantPresentationCard from '../../components/assistant/AssistantPresentationCard.vue'
import type { AssistantActionProposal, AssistantMessage } from '../../types/api'
import { createAssistantSession, executeAssistantAction, fetchAssistantActions, fetchAssistantMessages, fetchAssistantSessions, sendAssistantMessage } from '../../services/assistant'
import { sendDatingSignal } from '../../services/dating'
import { favoriteTradePost } from '../../services/trade'
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
const scrollBottomSeed = ref(100000)
const refreshVersion = ref(0)
const lastLocalMutationAt = ref(0)
const recoveryTimers = ref<ReturnType<typeof setTimeout>[]>([])
const ASSISTANT_UI_DEBUG = false

const quickReplies = ['帮我写一条校园帖子', '帮我整理闲置发布', '推荐适合我的组队', '帮我写一句自然的开场白']

const canSend = computed(() => inputText.value.trim().length > 0 && !loading.value)

function assistantUiDebug(event: string, payload: Record<string, unknown> = {}) {
  if (!ASSISTANT_UI_DEBUG) {
    return
  }
  try {
    console.log('assistant_ui_debug', event, JSON.stringify(payload))
  } catch {
    console.log('assistant_ui_debug', event, payload)
  }
}

function getMessageTime(message: AssistantMessage) {
  return new Date(message.created_at).getTime() || 0
}

function mergeMessages(localMessages: AssistantMessage[], serverMessages: AssistantMessage[]) {
  const serverRoleBodies = new Set(serverMessages.map((message) => `${message.role}::${message.body}`))
  const byId = new Map<string, AssistantMessage>()
  ;[...serverMessages, ...localMessages].forEach((message) => {
    if (message.id.startsWith('temp-') && serverRoleBodies.has(`${message.role}::${message.body}`)) {
      return
    }
    byId.set(message.id, message)
  })
  return Array.from(byId.values()).sort((first, second) => getMessageTime(first) - getMessageTime(second))
}

function hasAssistantAfter(messagesToCheck: AssistantMessage[], sentAt: number) {
  return messagesToCheck.some((message) => message.role === 'assistant' && getMessageTime(message) >= sentAt - 1000)
}

function getActionTime(action: AssistantActionProposal) {
  return new Date(action.created_at).getTime() || 0
}

function hasActionAfter(actionsToCheck: AssistantActionProposal[], sentAt: number) {
  return actionsToCheck.some((action) => getActionTime(action) >= sentAt - 1000)
}

function hasResponseForTurn(sentAt: number) {
  return hasAssistantAfter(messages.value, sentAt) || hasActionAfter(actions.value, sentAt)
}

function clearLateResponseRecovery() {
  recoveryTimers.value.forEach((timer) => clearTimeout(timer))
  recoveryTimers.value = []
}

onLoad(async () => {
  if (!ensureAuthenticated('/pages/assistant/index')) {
    return
  }
  await loadOrCreateSession()
})

watch(
  [() => messages.value.length, () => loading.value, () => actions.value.length],
  () => {
    void scrollToBottom()
  },
)

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

async function refreshSessionState(force = false) {
  if (!sessionId.value) {
    return
  }
  const targetSessionId = sessionId.value
  const requestVersion = ++refreshVersion.value
  assistantUiDebug('page_refresh_start', {
    requestVersion,
    targetSessionId,
    messages: messages.value.length,
  })
  const [msgs, nextActions] = await Promise.all([
    fetchAssistantMessages(targetSessionId),
    fetchAssistantActions(targetSessionId),
  ])
  if (requestVersion !== refreshVersion.value || (!force && loading.value) || targetSessionId !== sessionId.value) {
    assistantUiDebug('page_refresh_skip_stale_or_loading', {
      requestVersion,
      currentVersion: refreshVersion.value,
      loading: loading.value,
      force,
      targetSessionId,
      currentSessionId: sessionId.value,
      nextMessages: msgs.length,
      currentMessages: messages.value.length,
    })
    return
  }
  if (Date.now() - lastLocalMutationAt.value < 8000 && msgs.length < messages.value.length) {
    assistantUiDebug('page_refresh_skip_recent_smaller', {
      requestVersion,
      nextMessages: msgs.length,
      currentMessages: messages.value.length,
    })
    return
  }
  assistantUiDebug('page_refresh_apply', {
    requestVersion,
    nextMessages: msgs.length,
    currentMessages: messages.value.length,
    nextActions: nextActions.length,
  })
  messages.value = mergeMessages(messages.value, msgs)
  actions.value = nextActions
  scrollToBottom()
}

function scheduleLateResponseRecovery(targetSessionId: string | null, sentAt = Date.now()) {
  if (!targetSessionId) {
    return
  }
  clearLateResponseRecovery()
  ;[3000, 6000, 10000, 15000, 30000, 60000, 120000].forEach((delay) => {
    const timer = setTimeout(async () => {
      if (sessionId.value === targetSessionId) {
        await refreshSessionState(true)
        if (hasResponseForTurn(sentAt)) {
          loading.value = false
          clearLateResponseRecovery()
          scrollToBottom()
        }
      }
    }, delay)
    recoveryTimers.value.push(timer)
  })
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
  const sentAt = getMessageTime(tempUserMessage)
  const previousRealMessageCount = messages.value.filter((message) => !message.id.startsWith('temp-')).length
  scrollToBottom()
  scheduleLateResponseRecovery(sessionId.value, sentAt)

  let keepLoadingForRecovery = false
  let hasTurnResponse = false
  try {
    const response = await sendAssistantMessage(sessionId.value, { body: text })
    refreshVersion.value++
    clearLateResponseRecovery()
    lastLocalMutationAt.value = Date.now()
    messages.value = mergeMessages(messages.value, [response.user_message, response.assistant_message])
    actions.value = response.actions ?? []
    hasTurnResponse = hasResponseForTurn(sentAt)
    assistantUiDebug('page_send_success_apply_response', {
      sessionId: sessionId.value,
      messages: messages.value.length,
      actions: actions.value.length,
      hasTurnResponse,
      userMessageId: response.user_message.id,
      assistantMessageId: response.assistant_message.id,
    })
  } catch (error) {
    const failedSessionId = sessionId.value
    try {
      await refreshSessionState(true)
      hasTurnResponse = hasResponseForTurn(sentAt)
      keepLoadingForRecovery = !hasTurnResponse
      if (messages.value.length <= previousRealMessageCount && !keepLoadingForRecovery) {
        showToast(error instanceof Error ? error.message : '发送失败')
      }
    } catch {
      showToast(error instanceof Error ? error.message : '发送失败')
      keepLoadingForRecovery = true
    } finally {
      scheduleLateResponseRecovery(failedSessionId, sentAt)
    }
  } finally {
    if (hasTurnResponse || !keepLoadingForRecovery) {
      loading.value = false
      clearLateResponseRecovery()
    }
    assistantUiDebug('page_send_finally', {
      sessionId: sessionId.value,
      messages: messages.value.length,
      actions: actions.value.length,
    })
    scrollToBottom()
  }
}

function handleQuickReply(text: string) {
  inputText.value = text
  handleSend()
}

function handleCustomField(prompt: string) {
  inputText.value = prompt
}

async function reloadSession() {
  try {
    clearLateResponseRecovery()
    loading.value = false
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

function handleReviseAction() {
  inputText.value = '我想修改这版草稿：'
}

function handleGenerateOnly(action: AssistantActionProposal) {
  actions.value = actions.value.filter((item) => item.id !== action.id)
}

function makeDraftAction(action: AssistantActionProposal, item: Record<string, unknown>) {
  const draft = item.draft
  if (!draft || typeof draft !== 'object') {
    return action
  }
  const draftValue = draft as Record<string, unknown>
  return {
    ...action,
    kind: String(draftValue.kind || action.kind) as AssistantActionProposal['kind'],
    target_page: String(draftValue.target_page || action.target_page),
    fill_payload: (draftValue.fill_payload && typeof draftValue.fill_payload === 'object' ? draftValue.fill_payload : {}) as Record<string, unknown>,
  }
}

async function handleRecommendationAction(
  action: AssistantActionProposal,
  item: Record<string, unknown>,
  mode: 'open' | 'contact' | 'fill' | 'interested' | 'skip' | 'favorite',
) {
  if (mode === 'contact') {
    openTargetPage(String(item.contact_page || item.target_page || action.target_page))
    return
  }
  if (mode === 'fill') {
    saveAssistantDraft(makeDraftAction(action, item))
    showToast('已填入建议', 'success')
    openTargetPage(String((item.draft as Record<string, unknown> | undefined)?.target_page || item.contact_page || item.target_page || action.target_page))
    return
  }
  if (mode === 'interested' || mode === 'skip') {
    const targetUserId = String(item.target_user_id || '')
    if (!targetUserId) return
    const result = await sendDatingSignal({ target_user_id: targetUserId, signal: mode === 'interested' ? 'interested' : 'not_interested' })
    showToast(result.matched ? '匹配成功' : mode === 'interested' ? '已表达感兴趣' : '已跳过', 'success')
    return
  }
  if (mode === 'favorite') {
    const postId = String(item.post_id || '')
    if (!postId) return
    await favoriteTradePost(postId)
    showToast('已收藏', 'success')
    return
  }
  openTargetPage(String(item.target_page || action.target_page))
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

async function scrollToBottom() {
  await nextTick()
  const delays = [30, 120, 280]
  delays.forEach((delay) => {
    setTimeout(() => {
      void nextTick().then(() => {
        scrollBottomSeed.value += 100000
        scrollTop.value = scrollBottomSeed.value
      })
    }, delay)
  })
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
  height: 100vh;
  min-height: 0;
  background: #f5f1e8;
  padding-bottom: calc(112rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 32rpx;
  padding-top: calc(20rpx + env(safe-area-inset-top));
  background: #fffcf7;
  border-bottom: 1rpx solid rgba(16, 33, 51, 0.08);
}

.header-left {
  display: flex;
  flex-direction: column;
}

.header-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #2f2a24;
}

.header-desc {
  font-size: 22rpx;
  color: #6f675d;
  margin-top: 4rpx;
}

.btn-new {
  padding: 12rpx 24rpx;
  background: rgba(241, 107, 79, 0.1);
  border: 1rpx solid rgba(241, 107, 79, 0.3);
  border-radius: 24rpx;
  font-size: 24rpx;
  color: #c15f3c;
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
  box-sizing: border-box;
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
  color: #2f2a24;
}

.empty-desc {
  font-size: 28rpx;
  color: #6f675d;
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
  color: #2f2a24;
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
  background: linear-gradient(135deg, #c15f3c, #ff8a6b);
  color: #fff;
  font-size: 22rpx;
  font-weight: 700;
}

.avatar-user {
  background: rgba(241, 107, 79, 0.18);
  color: #c15f3c;
  font-size: 22rpx;
  font-weight: 700;
}

.message-content {
  max-width: 70%;
  margin: 0 16rpx;
  padding: 18rpx 22rpx;
  border-radius: 24rpx;
}

.message-presentation {
  width: calc(100% - 96rpx);
  max-width: 620rpx;
  margin: 0 16rpx;
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
  color: #2f2a24;
  white-space: pre-wrap;
}

.message-time {
  display: block;
  font-size: 20rpx;
  color: #6f675d;
  margin-top: 8rpx;
  text-align: right;
}

.loading-text {
  color: #6f675d;
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
  background: #fffcf7;
  border-top: 1rpx solid rgba(16, 33, 51, 0.08);
  gap: 16rpx;
}

.action-list {
  flex-shrink: 0;
  padding: 8rpx 0 16rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.bottom-anchor {
  height: 176rpx;
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
  color: #2f2a24;
  line-height: 38rpx;
  caret-color: #c15f3c;
  cursor-color: #c15f3c;
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
  background: #c15f3c;
}
</style>
