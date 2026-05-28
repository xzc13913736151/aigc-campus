<template>
  <view v-if="visible" class="assistant-root">
    <view class="assistant-mask" @tap="emit('close')" />

    <view class="assistant-sheet" :style="{ height: `${sheetHeight}vh` }">
      <view
        class="assistant-handle"
        @touchstart="handleDragStart"
        @touchmove.stop.prevent="handleDragMove"
      />

      <view class="assistant-header">
        <view class="assistant-header-copy">
          <text class="assistant-kicker">CampusClaw AI</text>
          <view style="height: 8rpx" />
          <text class="assistant-title">AI 助手</text>
          <view style="height: 8rpx" />
          <text class="assistant-subtitle">直接输入你想问的内容，AI 会根据当前页面给出建议。</text>
        </view>
        <button class="assistant-close" @tap="emit('close')">收起</button>
      </view>

      <view class="assistant-meta">
        <view class="meta-pill accent">
          <text>CampusClaw 对话助手</text>
        </view>
        <view class="meta-pill">
          <text>{{ messages.length ? `已沉淀 ${messageTurns} 轮对话` : '这是一个新的对话' }}</text>
        </view>
      </view>

      <view v-if="!hasToken" class="assistant-empty card-like">
        <text class="section-title" style="font-size: 32rpx">登录后即可使用 AI 助手</text>
        <view style="height: 10rpx" />
        <text class="section-desc">它会结合你当前所在页面，帮你想标题、润色文案、整理表达和梳理下一步行动。</text>
        <view style="height: 20rpx" />
        <button class="btn btn-primary" size="mini" @tap="goLogin">去登录</button>
      </view>

      <view v-else class="assistant-body">
        <scroll-view scroll-y class="assistant-messages" :scroll-into-view="scrollIntoView" enhanced show-scrollbar="false">
          <view v-if="bootstrapping" class="assistant-loading">
            <view class="loading-bubble">
              <text class="assistant-role">AI 助手</text>
              <view style="height: 8rpx" />
              <text class="assistant-copy">正在准备当前页面的上下文，请稍等。</text>
            </view>
          </view>

          <view v-else-if="messages.length || pendingUserBody || sending" class="assistant-message-list">
            <view
              v-for="message in messages"
              :id="`assistant-message-${message.id}`"
              :key="message.id"
              class="assistant-message"
              :class="{ mine: message.role === 'user' }"
            >
              <view class="assistant-message-head">
                <text class="assistant-role">{{ message.role === 'user' ? '我' : 'AI 助手' }}</text>
                <text class="assistant-time">{{ formatDate(message.created_at) }}</text>
              </view>
              <view style="height: 8rpx" />
              <text class="assistant-copy">{{ message.body }}</text>
            </view>

            <view v-if="pendingUserBody" id="assistant-pending-user" class="assistant-message mine">
              <view class="assistant-message-head">
                <text class="assistant-role">我</text>
                <text class="assistant-time">刚刚</text>
              </view>
              <view style="height: 8rpx" />
              <text class="assistant-copy">{{ pendingUserBody }}</text>
            </view>

            <view v-if="sending" id="assistant-thinking" class="assistant-message">
              <view class="assistant-message-head">
                <text class="assistant-role">AI 助手</text>
                <text class="assistant-time">思考中</text>
              </view>
              <view style="height: 10rpx" />
              <view class="thinking-row">
                <view class="thinking-dot" />
                <view class="thinking-dot" />
                <view class="thinking-dot" />
              </view>
            </view>

            <view id="assistant-bottom-anchor" class="assistant-bottom-anchor" />
          </view>

          <view v-else class="assistant-empty inline-empty">
            <text class="section-desc">直接输入你现在想解决的事情，我会帮你一起梳理。</text>
          </view>
        </scroll-view>

        <view v-if="actions.length" class="assistant-action-list">
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

        <view class="assistant-actions">
          <button class="restart-link" :disabled="sending || bootstrapping" @tap="handleRestartSession">重新开始</button>
        </view>

        <view class="assistant-composer">
          <view class="composer-row">
            <textarea
              v-model="draft"
              class="assistant-textarea"
              auto-height
              confirm-type="send"
              cursor-color="#f16b4f"
              :show-confirm-bar="false"
              maxlength="500"
              placeholder="问点什么..."
              @confirm="handleSend"
            />
            <button class="send-button" :class="{ disabled: sending || bootstrapping || !draft.trim() }" :disabled="sending || bootstrapping || !draft.trim()" @tap="handleSend">
              {{ sending ? '...' : '发送' }}
            </button>
          </view>
          <text v-if="errorMessage" class="error">{{ errorMessage }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

import AssistantActionCard from './AssistantActionCard.vue'
import type { AssistantActionProposal, AssistantMessage, AssistantSession } from '../../types/api'
import { createAssistantSession, executeAssistantAction, fetchAssistantActions, fetchAssistantMessages, fetchAssistantSessions, sendAssistantMessage } from '../../services/assistant'
import { isAuthenticated, redirectToLogin } from '../../utils/auth'
import { saveAssistantDraft } from '../../utils/assistantDraft'

type SessionCacheEntry = {
  sessionId: string
  messages: AssistantMessage[]
  actions: AssistantActionProposal[]
}

const props = defineProps<{
  visible: boolean
  pageType: AssistantSession['page_type']
  contextPath: string
}>()

const emit = defineEmits<{
  close: []
}>()

const hasToken = computed(() => isAuthenticated.value)
const sessionId = ref('')
const messages = ref<AssistantMessage[]>([])
const draft = ref('')
const bootstrapping = ref(false)
const sending = ref(false)
const pendingUserBody = ref('')
const errorMessage = ref('')
const actions = ref<AssistantActionProposal[]>([])
const actionBusyId = ref('')
const scrollIntoView = ref('')
const sessionCache = ref<Record<string, SessionCacheEntry>>({})
const sheetHeight = ref(64)
const dragStartY = ref(0)
const dragStartHeight = ref(64)

const sessionKey = computed(() => `${props.pageType}::${props.contextPath || ''}`)

const messageTurns = computed(() => Math.max(1, Math.ceil(messages.value.length / 2)))

watch(
  () => sessionKey.value,
  () => {
    draft.value = ''
    errorMessage.value = ''
    pendingUserBody.value = ''
    restoreCachedSession()
    if (props.visible && hasToken.value) {
      void ensureSessionReady()
    }
  },
  { immediate: true },
)

watch(
  () => props.visible,
  async (value) => {
    if (!value || !hasToken.value) {
      return
    }
    restoreCachedSession()
    await ensureSessionReady()
    void scrollToBottom()
  },
)

watch(
  () => hasToken.value,
  (value) => {
    if (!value) {
      sessionId.value = ''
      messages.value = []
    }
  },
)

watch(
  [() => messages.value.length, () => pendingUserBody.value, () => sending.value],
  () => {
    if (props.visible) {
      void scrollToBottom()
    }
  },
)

function clampSheetHeight(value: number) {
  return Math.min(88, Math.max(42, value))
}

function handleDragStart(event: TouchEvent) {
  dragStartY.value = event.touches[0]?.clientY ?? 0
  dragStartHeight.value = sheetHeight.value
}

function handleDragMove(event: TouchEvent) {
  const currentY = event.touches[0]?.clientY ?? dragStartY.value
  const deltaY = dragStartY.value - currentY
  const windowHeight = uni.getWindowInfo().windowHeight || 1
  sheetHeight.value = clampSheetHeight(dragStartHeight.value + (deltaY / windowHeight) * 100)
}

function restoreCachedSession() {
  const cached = sessionCache.value[sessionKey.value]
  if (!cached) {
    sessionId.value = ''
    messages.value = []
    actions.value = []
    return
  }
  sessionId.value = cached.sessionId
  messages.value = [...cached.messages]
  actions.value = [...cached.actions]
}

function persistCurrentSession() {
  if (!sessionId.value) {
    return
  }
  sessionCache.value = {
    ...sessionCache.value,
    [sessionKey.value]: {
      sessionId: sessionId.value,
      messages: [...messages.value],
      actions: [...actions.value],
    },
  }
}

async function ensureSessionReady() {
  if (sessionId.value || bootstrapping.value) {
    return
  }

  bootstrapping.value = true
  errorMessage.value = ''
  try {
    const existingSession = await resolveExistingSession()
    if (existingSession) {
      sessionId.value = existingSession.id
      await refreshSessionState(existingSession.id)
      persistCurrentSession()
      return
    }

    const session = await createAssistantSession({
      page_type: props.pageType,
      context_path: props.contextPath,
    })
    sessionId.value = session.id
    await refreshSessionState(session.id)
    persistCurrentSession()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'AI 助手暂时不可用'
  } finally {
    bootstrapping.value = false
  }
}

async function refreshSessionState(targetSessionId = sessionId.value) {
  if (!targetSessionId) {
    return
  }
  const [nextMessages, nextActions] = await Promise.all([
    fetchAssistantMessages(targetSessionId),
    fetchAssistantActions(targetSessionId),
  ])
  messages.value = nextMessages
  actions.value = nextActions
}

async function resolveExistingSession() {
  const sessions = await fetchAssistantSessions()
  const matched = sessions
    .filter((item) => item.page_type === props.pageType && (item.context_path || '') === (props.contextPath || ''))
    .sort((first, second) => second.updated_at.localeCompare(first.updated_at))[0]
  return matched ?? null
}

async function handleSend() {
  if (sending.value || bootstrapping.value) {
    return
  }
  errorMessage.value = ''
  const body = draft.value.trim()

  if (!body) {
    errorMessage.value = '请输入你想问 AI 的内容'
    return
  }

  await ensureSessionReady()
  if (!sessionId.value) {
    return
  }

  sending.value = true
  pendingUserBody.value = body
  draft.value = ''
  const previousMessageCount = messages.value.length
  try {
    const response = await sendAssistantMessage(sessionId.value, { body })
    messages.value = [...messages.value, response.user_message, response.assistant_message]
    actions.value = response.actions ?? []
    persistCurrentSession()
  } catch (error) {
    try {
      await refreshSessionState()
      if (messages.value.length <= previousMessageCount) {
        draft.value = body
        errorMessage.value = error instanceof Error ? error.message : '发送失败'
      }
    } catch {
      draft.value = body
      errorMessage.value = error instanceof Error ? error.message : '发送失败'
    }
  } finally {
    pendingUserBody.value = ''
    sending.value = false
  }
}

async function handleRestartSession() {
  sessionId.value = ''
  messages.value = []
  actions.value = []
  pendingUserBody.value = ''
  errorMessage.value = ''

  const nextCache = { ...sessionCache.value }
  delete nextCache[sessionKey.value]
  sessionCache.value = nextCache

  await ensureSessionReady()
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
  uni.showToast({ title: '已填入草稿', icon: 'success' })
  openTargetPage(action.target_page)
}

function handleGenerateOnly(action: AssistantActionProposal) {
  actions.value = actions.value.filter((item) => item.id !== action.id)
  persistCurrentSession()
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
        persistCurrentSession()
        uni.showToast({ title: response.result.message || '执行成功', icon: 'success' })
        if (response.result.target_page) {
          openTargetPage(String(response.result.target_page))
        }
      } catch (error) {
        uni.showToast({ title: error instanceof Error ? error.message : '执行失败', icon: 'none' })
      } finally {
        actionBusyId.value = ''
      }
    },
  })
}

async function scrollToBottom() {
  await nextTick()
  scrollIntoView.value = ''
  await nextTick()
  if (sending.value) {
    scrollIntoView.value = pendingUserBody.value ? 'assistant-thinking' : 'assistant-bottom-anchor'
    return
  }
  scrollIntoView.value = 'assistant-bottom-anchor'
}

function formatDate(value: string) {
  return value.replace('T', ' ').slice(11, 16)
}

function goLogin() {
  redirectToLogin(props.contextPath || '/pages/forum/index')
}
</script>

<style scoped lang="scss">
.assistant-root {
  position: fixed;
  inset: 0;
  z-index: 10001;
}

.assistant-mask {
  position: absolute;
  inset: 0;
  background: transparent;
}

.assistant-sheet {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 64vh;
  min-height: 42vh;
  max-height: 88vh;
  padding: 20rpx 24rpx calc(env(safe-area-inset-bottom) + 92rpx);
  border-radius: 36rpx 36rpx 0 0;
  background:
    radial-gradient(circle at top right, rgba(241, 107, 79, 0.14), transparent 28%),
    radial-gradient(circle at top left, rgba(255, 196, 120, 0.14), transparent 26%),
    rgba(255, 250, 245, 0.985);
  border-top: 1rpx solid rgba(16, 33, 51, 0.08);
  box-shadow: 0 -28rpx 72rpx rgba(16, 33, 51, 0.16);
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.assistant-handle {
  width: 92rpx;
  height: 8rpx;
  border-radius: 999rpx;
  background: rgba(16, 33, 51, 0.16);
  align-self: center;
  flex-shrink: 0;
}

.assistant-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
}

.assistant-header-copy {
  flex: 1;
}

.assistant-kicker {
  display: inline-flex;
  align-items: center;
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(241, 107, 79, 0.12);
  color: #f16b4f;
  font-size: 20rpx;
  font-weight: 800;
  letter-spacing: 3rpx;
}

.assistant-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #102133;
}

.assistant-subtitle {
  font-size: 24rpx;
  line-height: 1.7;
  color: #6b7280;
}

.assistant-close {
  flex-shrink: 0;
  min-width: 104rpx;
  height: 56rpx;
  min-height: 56rpx;
  padding: 0 24rpx;
  margin: 0;
  border: 0;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.82);
  color: #102133;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 1;
  text-align: center;
}

.assistant-close::after {
  border: 0;
}

.assistant-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.meta-pill {
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.78);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
  font-size: 22rpx;
  color: #44515f;
}

.meta-pill.accent {
  background: rgba(241, 107, 79, 0.12);
  color: #f16b4f;
}

.assistant-body {
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
  gap: 10rpx;
}

.assistant-messages {
  flex: 1;
  min-height: 220rpx;
  padding-right: 4rpx;
}

.assistant-action-list {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  max-height: 260rpx;
  overflow: auto;
}

.assistant-message-list,
.assistant-loading {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.assistant-message,
.loading-bubble {
  max-width: 92%;
  padding: 20rpx 22rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.94);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
  box-shadow: 0 10rpx 28rpx rgba(16, 33, 51, 0.04);
}

.assistant-message.mine {
  margin-left: auto;
  background: rgba(241, 107, 79, 0.12);
}

.assistant-message-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.assistant-role {
  font-size: 22rpx;
  font-weight: 700;
  color: #f16b4f;
}

.assistant-time {
  font-size: 20rpx;
  color: #8a929c;
}

.assistant-copy {
  font-size: 26rpx;
  line-height: 1.75;
  color: #102133;
  white-space: pre-wrap;
}

.assistant-actions {
  display: flex;
  justify-content: flex-end;
}

.restart-link {
  height: 42rpx;
  min-height: 42rpx;
  padding: 0 6rpx;
  margin: 0;
  border: 0;
  background: transparent;
  color: #8a929c;
  font-size: 22rpx;
  line-height: 1;
}

.restart-link::after {
  border: 0;
}

.assistant-composer {
  flex-shrink: 0;
  padding: 10rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
}

.composer-row {
  display: flex;
  align-items: flex-end;
  gap: 12rpx;
}

.assistant-textarea {
  flex: 1;
  min-height: 44rpx;
  max-height: 168rpx;
  padding: 14rpx 18rpx;
  border-radius: 28rpx;
  background: rgba(255, 250, 245, 0.98);
  color: #102133;
  font-size: 27rpx;
  line-height: 38rpx;
  caret-color: #f16b4f;
  cursor-color: #f16b4f;
  overflow-y: auto;
}

.send-button {
  flex-shrink: 0;
  width: 104rpx;
  height: 68rpx;
  min-height: 68rpx;
  padding: 0;
  margin: 0;
  border: 0;
  border-radius: 999rpx;
  background: #f16b4f;
  color: #fff;
  font-size: 25rpx;
  font-weight: 800;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-button.disabled {
  background: rgba(16, 33, 51, 0.12);
  color: #8a929c;
}

.send-button::after {
  border: 0;
}

.composer-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.assistant-empty {
  text-align: center;
  padding: 36rpx 24rpx;
}

.card-like {
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.82);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
}

.inline-empty {
  padding: 24rpx 12rpx;
}

.thinking-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.thinking-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: #f16b4f;
  opacity: 0.6;
}

.assistant-bottom-anchor {
  height: 1rpx;
}
</style>
