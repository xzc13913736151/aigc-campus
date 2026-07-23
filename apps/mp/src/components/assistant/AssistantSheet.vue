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
          <text class="assistant-kicker">CampusClaw 协作助手</text>
          <view style="height: 8rpx" />
          <text class="assistant-title">一起把事情理清楚</text>
          <view style="height: 8rpx" />
          <text class="assistant-subtitle">我会保留当前页面上下文，先给建议，涉及发布或发送时再请你确认。</text>
        </view>
        <button class="assistant-close" @tap="emit('close')">
          <text class="button-label">收起</text>
        </button>
      </view>

      <view class="assistant-meta">
        <view class="meta-pill accent">
          <text>{{ contextLabel }}</text>
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
        <button class="btn btn-primary" @tap="goLogin">去登录</button>
      </view>

      <view v-else class="assistant-body">
        <scroll-view scroll-y class="assistant-messages" :scroll-top="scrollTop" enhanced show-scrollbar="false">
          <view v-if="bootstrapping" class="assistant-loading">
            <view class="loading-bubble">
              <text class="assistant-role">AI 助手</text>
              <view style="height: 8rpx" />
              <text class="assistant-copy">正在准备当前页面的上下文，请稍等。</text>
            </view>
          </view>

          <view v-else-if="messages.length || visiblePendingUserBody || sending || actions.length" class="assistant-message-list">
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
              <text v-if="message.role === 'user'" class="assistant-copy">{{ message.body }}</text>
              <AssistantMarkdown v-else :content="message.body" />
            </view>

            <view v-if="visiblePendingUserBody" id="assistant-pending-user" class="assistant-message mine">
              <view class="assistant-message-head">
                <text class="assistant-role">我</text>
                <text class="assistant-time">刚刚</text>
              </view>
              <view style="height: 8rpx" />
              <text class="assistant-copy">{{ visiblePendingUserBody }}</text>
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

            <view v-if="actions.length" id="assistant-action-list" class="assistant-action-list">
              <AssistantActionCard
                v-for="action in actions"
                :key="action.id"
                :action="action"
                :busy="actionBusyId === action.id"
                @execute="handleExecuteAction"
                @fill="handleFillAction"
                @generate="handleGenerateOnly"
                @recommend="handleRecommendationAction"
              />
            </view>

            <view class="assistant-bottom-anchor" />
          </view>

          <view v-else class="assistant-empty inline-empty">
            <text class="section-desc">直接输入你现在想解决的事情，我会帮你一起梳理。</text>
          </view>
        </scroll-view>

        <view class="assistant-actions">
          <button class="restart-button" :disabled="sending || bootstrapping" @tap="handleRestartSession">
            <text class="button-label">开启新对话</text>
          </button>
        </view>

        <view class="assistant-composer">
          <view class="composer-row">
            <textarea
              v-model="draft"
              class="assistant-textarea"
              auto-height
              confirm-type="send"
              cursor-color="#c15f3c"
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

    <view v-if="confirmationAction" class="action-confirm-layer">
      <view class="action-confirm-mask" @tap="cancelExecuteAction" />
      <view class="action-confirm-card" @tap.stop>
        <text class="action-confirm-kicker">需要你的确认</text>
        <text class="action-confirm-title">确认执行这项操作？</text>
        <text class="action-confirm-desc">CampusClaw 助手只会在你确认后执行，发布内容仍由你负责最终决定。</text>

        <view class="action-confirm-summary">
          <text class="action-confirm-summary-label">即将执行</text>
          <text class="action-confirm-summary-title">{{ confirmationAction.title }}</text>
          <text v-if="confirmationPreview" class="action-confirm-summary-desc">{{ confirmationPreview }}</text>
        </view>
        <text v-if="confirmationError" class="action-confirm-error">{{ confirmationError }}</text>

        <view class="action-confirm-buttons">
          <button class="action-confirm-button secondary" :disabled="Boolean(actionBusyId)" @tap="cancelExecuteAction">
            <text class="button-label">返回修改</text>
          </button>
          <button class="action-confirm-button primary" :disabled="Boolean(actionBusyId)" @tap="confirmExecuteAction">
            <text class="button-label">{{ actionBusyId ? '执行中…' : '确认执行' }}</text>
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

import AssistantActionCard from './AssistantActionCard.vue'
import AssistantMarkdown from './AssistantMarkdown.vue'
import type { AssistantActionProposal, AssistantMessage, AssistantSession } from '../../types/api'
import { createAssistantSession, executeAssistantAction, fetchAssistantActions, fetchAssistantMessages, fetchAssistantSessions, sendAssistantMessage } from '../../services/assistant'
import { sendDatingSignal } from '../../services/dating'
import { favoriteTradePost } from '../../services/trade'
import { isAuthenticated, redirectToLogin } from '../../utils/auth'
import { saveAssistantDraft } from '../../utils/assistantDraft'

type SessionCacheEntry = {
  sessionId: string
  session: AssistantSession | null
  messages: AssistantMessage[]
  actions: AssistantActionProposal[]
}

const props = defineProps<{
  visible: boolean
  pageType: AssistantSession['page_type']
  contextPath: string
  contextTargetType?: string
  contextTargetId?: string
}>()

const emit = defineEmits<{
  close: []
}>()

const hasToken = computed(() => isAuthenticated.value)
const session = ref<AssistantSession | null>(null)
const sessionId = ref('')
const messages = ref<AssistantMessage[]>([])
const draft = ref('')
const bootstrapping = ref(false)
const sending = ref(false)
const pendingUserBody = ref('')
const pendingBaseMessageCount = ref(0)
const errorMessage = ref('')
const actions = ref<AssistantActionProposal[]>([])
const actionBusyId = ref('')
const confirmationAction = ref<AssistantActionProposal | null>(null)
const confirmationError = ref('')
const scrollTop = ref(0)
const scrollBottomSeed = ref(100000)
const sessionCache = ref<Record<string, SessionCacheEntry>>({})
const refreshVersion = ref(0)
const lastLocalMutationAt = ref(0)
const recoveryTimers = ref<ReturnType<typeof setTimeout>[]>([])
const sheetHeight = ref(64)
const dragStartY = ref(0)
const dragStartHeight = ref(64)
const ASSISTANT_UI_DEBUG = false

const sessionKey = computed(
  () => `${props.pageType}::${props.contextPath || ''}::${props.contextTargetType || ''}::${props.contextTargetId || ''}`,
)

const messageTurns = computed(() => Math.max(1, Math.ceil(messages.value.length / 2)))
const visiblePendingUserBody = computed(() => {
  if (!pendingUserBody.value.trim() || messages.value.length > pendingBaseMessageCount.value) {
    return ''
  }
  return pendingUserBody.value
})
const confirmationPreview = computed(() => {
  const preview = confirmationAction.value?.preview || {}
  return String(preview.body || preview.title || preview.action || '')
})
const contextLabel = computed(() => {
  const labels: Record<AssistantSession['page_type'], string> = {
    forum: '正在协助：校园论坛',
    publish: '正在协助：校园匹配',
    messages: '正在协助：消息沟通',
    me: '正在协助：个人资料',
    general: '通用校园协作',
  }
  return labels[props.pageType] || labels.general
})

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
  const byId = new Map<string, AssistantMessage>()
  ;[...serverMessages, ...localMessages].forEach((message) => {
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
    if (!value) {
      confirmationAction.value = null
      confirmationError.value = ''
      return
    }
    if (!hasToken.value) {
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
      session.value = null
      sessionId.value = ''
      messages.value = []
      actions.value = []
    }
  },
)

watch(
  [() => messages.value.length, () => visiblePendingUserBody.value, () => sending.value, () => actions.value.length],
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
  if (sending.value || pendingUserBody.value) {
    assistantUiDebug('restore_skip_sending', {
      sessionKey: sessionKey.value,
      messages: messages.value.length,
    })
    return
  }
  if (Date.now() - lastLocalMutationAt.value < 8000 && messages.value.length) {
    assistantUiDebug('restore_skip_recent_local', {
      sessionKey: sessionKey.value,
      messages: messages.value.length,
    })
    return
  }
  const cached = sessionCache.value[sessionKey.value]
  if (!cached) {
    assistantUiDebug('restore_clear_no_cache', {
      sessionKey: sessionKey.value,
      messages: messages.value.length,
    })
    session.value = null
    sessionId.value = ''
    messages.value = []
    actions.value = []
    return
  }
  assistantUiDebug('restore_apply_cache', {
    sessionKey: sessionKey.value,
    cachedMessages: cached.messages.length,
    currentMessages: messages.value.length,
  })
  session.value = cached.session
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
      session: session.value,
      messages: [...messages.value],
      actions: [...actions.value],
    },
  }
}

async function createFreshSession() {
  const createdSession = await createAssistantSession({
    page_type: props.pageType,
    context_path: props.contextPath,
    context_target_type: props.contextTargetType,
    context_target_id: props.contextTargetId,
  })
  session.value = createdSession
  sessionId.value = createdSession.id
  await refreshSessionState(createdSession.id)
  persistCurrentSession()
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
      session.value = existingSession
      sessionId.value = existingSession.id
      await refreshSessionState(existingSession.id)
      persistCurrentSession()
      return
    }

    await createFreshSession()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'AI 助手暂时不可用，请稍后再试'
  } finally {
    bootstrapping.value = false
  }
}

async function refreshSessionState(targetSessionId = sessionId.value, force = false) {
  if (!targetSessionId) {
    return
  }
  const requestVersion = ++refreshVersion.value
  assistantUiDebug('refresh_start', {
    requestVersion,
    targetSessionId,
    messages: messages.value.length,
  })
  const [nextMessages, nextActions, sessions] = await Promise.all([
    fetchAssistantMessages(targetSessionId),
    fetchAssistantActions(targetSessionId),
    fetchAssistantSessions(),
  ])
  if (requestVersion !== refreshVersion.value || (!force && (sending.value || pendingUserBody.value)) || targetSessionId !== sessionId.value) {
    assistantUiDebug('refresh_skip_stale_or_sending', {
      requestVersion,
      currentVersion: refreshVersion.value,
      targetSessionId,
      currentSessionId: sessionId.value,
      sending: sending.value,
      pending: Boolean(pendingUserBody.value),
      force,
      nextMessages: nextMessages.length,
      currentMessages: messages.value.length,
    })
    return
  }
  if (Date.now() - lastLocalMutationAt.value < 8000 && nextMessages.length < messages.value.length) {
    assistantUiDebug('refresh_skip_recent_smaller', {
      requestVersion,
      nextMessages: nextMessages.length,
      currentMessages: messages.value.length,
    })
    return
  }
  assistantUiDebug('refresh_apply', {
    requestVersion,
    nextMessages: nextMessages.length,
    currentMessages: messages.value.length,
    nextActions: nextActions.length,
  })
  session.value = sessions.find((item) => item.id === targetSessionId) ?? session.value
  messages.value = mergeMessages(messages.value, nextMessages)
  actions.value = nextActions
  void scrollToBottom()
}

function scheduleLateResponseRecovery(targetSessionId: string, sentAt = Date.now()) {
  if (!targetSessionId) {
    return
  }
  clearLateResponseRecovery()
  ;[3000, 6000, 10000, 15000, 30000, 60000, 120000].forEach((delay) => {
    const timer = setTimeout(async () => {
      if (sessionId.value === targetSessionId) {
        await refreshSessionState(targetSessionId, true)
        if (hasResponseForTurn(sentAt)) {
          pendingUserBody.value = ''
          sending.value = false
          clearLateResponseRecovery()
          persistCurrentSession()
          void scrollToBottom()
        }
      }
    }, delay)
    recoveryTimers.value.push(timer)
  })
}

async function resolveExistingSession() {
  const sessions = await fetchAssistantSessions()
  const matched = sessions
    .filter(
      (item) =>
        item.page_type === props.pageType &&
        (item.context_path || '') === (props.contextPath || '') &&
        (item.context_target_type || '') === (props.contextTargetType || '') &&
        (item.context_target_id || '') === (props.contextTargetId || ''),
    )
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
    errorMessage.value = '请输入你想让 AI 帮忙的内容'
    return
  }

  await ensureSessionReady()
  if (!sessionId.value) {
    return
  }

  sending.value = true
  pendingBaseMessageCount.value = messages.value.length
  pendingUserBody.value = body
  draft.value = ''
  const sentAt = Date.now()
  const previousMessageCount = messages.value.length
  scheduleLateResponseRecovery(sessionId.value, sentAt)
  let keepLoadingForRecovery = false
  let hasTurnResponse = false
  try {
    const response = await sendAssistantMessage(sessionId.value, { body })
    refreshVersion.value++
    clearLateResponseRecovery()
    lastLocalMutationAt.value = Date.now()
    session.value = response.session
    pendingUserBody.value = ''
    messages.value = mergeMessages(messages.value, [response.user_message, response.assistant_message])
    actions.value = response.actions ?? []
    hasTurnResponse = hasResponseForTurn(sentAt)
    assistantUiDebug('send_success_apply_response', {
      sessionId: sessionId.value,
      messages: messages.value.length,
      actions: actions.value.length,
      hasTurnResponse,
      userMessageId: response.user_message.id,
      assistantMessageId: response.assistant_message.id,
    })
    persistCurrentSession()
  } catch (error) {
    const failedSessionId = sessionId.value
    try {
      await refreshSessionState(sessionId.value, true)
      hasTurnResponse = hasResponseForTurn(sentAt)
      keepLoadingForRecovery = !hasTurnResponse
      if (messages.value.length <= previousMessageCount && !keepLoadingForRecovery) {
        draft.value = body
        errorMessage.value = error instanceof Error ? error.message : '发送失败，请稍后再试'
      }
    } catch {
      keepLoadingForRecovery = true
      errorMessage.value = error instanceof Error ? error.message : '发送失败，请稍后再试'
    } finally {
      if (keepLoadingForRecovery) {
        errorMessage.value = ''
      }
      scheduleLateResponseRecovery(failedSessionId, sentAt)
    }
  } finally {
    if (hasTurnResponse || !keepLoadingForRecovery) {
      pendingUserBody.value = ''
      sending.value = false
      clearLateResponseRecovery()
    }
    assistantUiDebug('send_finally', {
      sessionId: sessionId.value,
      messages: messages.value.length,
      actions: actions.value.length,
    })
    void scrollToBottom()
  }
}

async function handleRestartSession() {
  clearLateResponseRecovery()
  bootstrapping.value = true
  session.value = null
  sessionId.value = ''
  messages.value = []
  actions.value = []
  pendingUserBody.value = ''
  pendingBaseMessageCount.value = 0
  sending.value = false
  errorMessage.value = ''

  const nextCache = { ...sessionCache.value }
  delete nextCache[sessionKey.value]
  sessionCache.value = nextCache

  try {
    await createFreshSession()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'AI 助手暂时不可用，请稍后再试'
  } finally {
    bootstrapping.value = false
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
  uni.showToast({ title: '已填入草稿', icon: 'success' })
  openTargetPage(action.target_page)
}

function handleGenerateOnly(action: AssistantActionProposal) {
  actions.value = actions.value.filter((item) => item.id !== action.id)
  persistCurrentSession()
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
    uni.showToast({ title: '已填入建议', icon: 'success' })
    openTargetPage(String((item.draft as Record<string, unknown> | undefined)?.target_page || item.contact_page || item.target_page || action.target_page))
    return
  }
  if (mode === 'interested' || mode === 'skip') {
    const targetUserId = String(item.target_user_id || '')
    if (!targetUserId) return
    await sendDatingSignal({ target_user_id: targetUserId, signal: mode === 'interested' ? 'interested' : 'not_interested' })
    uni.showToast({ title: mode === 'interested' ? '已表达感兴趣' : '已跳过', icon: 'success' })
    return
  }
  if (mode === 'favorite') {
    const postId = String(item.post_id || '')
    if (!postId) return
    await favoriteTradePost(postId)
    uni.showToast({ title: '已收藏', icon: 'success' })
    return
  }
  openTargetPage(String(item.target_page || action.target_page))
}

function handleExecuteAction(action: AssistantActionProposal) {
  confirmationError.value = ''
  confirmationAction.value = action
}

function cancelExecuteAction() {
  if (actionBusyId.value) {
    return
  }
  confirmationAction.value = null
  confirmationError.value = ''
}

async function confirmExecuteAction() {
  const action = confirmationAction.value
  if (!action || actionBusyId.value) {
    return
  }

  actionBusyId.value = action.id
  confirmationError.value = ''
  try {
    const response = await executeAssistantAction(action.id)
    actions.value = actions.value.map((item) => (item.id === action.id ? response.action : item))
    persistCurrentSession()
    confirmationAction.value = null
    uni.showToast({ title: response.result.message || '执行成功', icon: 'success' })
    if (response.result.target_page) {
      openTargetPage(String(response.result.target_page))
    }
  } catch (error) {
    confirmationError.value = error instanceof Error ? error.message : '执行失败，请稍后再试'
  } finally {
    actionBusyId.value = ''
  }
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

function formatDate(value: string) {
  return value.replace('T', ' ').slice(11, 16)
}

function goLogin() {
  redirectToLogin(props.contextPath || '/pages/forum/index')
}
</script>

<style scoped lang="scss">
@use '../../styles/tokens' as t;

.assistant-root {
  position: fixed;
  inset: 0;
  z-index: 10001;
}

.action-confirm-layer {
  position: absolute;
  inset: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx 32rpx calc(40rpx + env(safe-area-inset-bottom));
}

.action-confirm-mask {
  position: absolute;
  inset: 0;
  background: rgba(47, 42, 36, 0.42);
}

.action-confirm-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 620rpx;
  padding: 36rpx;
  border: 1rpx solid t.$color-line;
  border-radius: t.$radius-lg;
  background: t.$color-card;
  box-shadow: 0 30rpx 90rpx rgba(47, 42, 36, 0.22);
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.action-confirm-kicker {
  color: t.$color-ai;
  font-size: 22rpx;
  font-weight: 650;
  letter-spacing: 1rpx;
}

.action-confirm-title {
  color: t.$color-ink;
  font-size: 36rpx;
  font-weight: 650;
  line-height: 1.4;
}

.action-confirm-desc,
.action-confirm-summary-desc {
  color: t.$color-ink-secondary;
  font-size: 25rpx;
  line-height: 1.65;
}

.action-confirm-summary {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  padding: 22rpx;
  border-left: 5rpx solid t.$color-ai;
  border-radius: 4rpx t.$radius-sm t.$radius-sm 4rpx;
  background: t.$color-input;
}

.action-confirm-summary-label {
  color: t.$color-ink-muted;
  font-size: 21rpx;
}

.action-confirm-summary-title {
  color: t.$color-ink;
  font-size: 28rpx;
  font-weight: 650;
  line-height: 1.5;
}

.action-confirm-error {
  color: t.$color-danger;
  font-size: 24rpx;
  line-height: 1.5;
}

.action-confirm-buttons {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
  margin-top: 8rpx;
}

.action-confirm-button {
  width: 100%;
  height: 88rpx;
  min-height: 88rpx;
  padding: 0 20rpx;
  margin: 0;
  border-radius: t.$radius-sm;
  font-size: 26rpx;
  font-weight: 650;
}

.action-confirm-button.secondary {
  border: 1rpx solid t.$color-line;
  background: t.$color-surface;
  color: t.$color-ink;
}

.action-confirm-button.primary {
  border: 1rpx solid t.$color-brand;
  background: t.$color-brand;
  color: t.$color-inverse;
}

.assistant-mask {
  position: absolute;
  inset: 0;
  background: rgba(47, 42, 36, 0.22);
}

.assistant-sheet {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 64vh;
  min-height: 42vh;
  max-height: 88vh;
  padding: 18rpx 24rpx calc(env(safe-area-inset-bottom) + 88rpx);
  border-radius: 32rpx 32rpx 0 0;
  background: t.$color-surface;
  border-top: 1rpx solid t.$color-line;
  box-shadow: t.$shadow-float;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.assistant-handle {
  width: 92rpx;
  height: 8rpx;
  border-radius: 999rpx;
  background: t.$color-line;
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
  border-radius: t.$radius-sm;
  background: t.$color-input;
  color: t.$color-ai;
  font-size: 20rpx;
  font-weight: 650;
  letter-spacing: 1rpx;
}

.assistant-title {
  font-size: 36rpx;
  font-weight: 700;
  color: t.$color-ink;
}

.assistant-subtitle {
  font-size: 24rpx;
  line-height: 1.7;
  color: t.$color-ink-secondary;
}

.assistant-close {
  flex-shrink: 0;
  min-width: 104rpx;
  height: 80rpx;
  min-height: 80rpx;
  padding: 0 24rpx;
  margin: 0;
  border: 0;
  border-radius: t.$radius-sm;
  border: 1rpx solid t.$color-line;
  background: t.$color-card;
  color: t.$color-ink;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 80rpx;
  text-align: center;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
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
  border-radius: t.$radius-sm;
  background: t.$color-card;
  border: 1rpx solid t.$color-line;
  font-size: 22rpx;
  color: t.$color-ink-secondary;
}

.meta-pill.accent {
  background: t.$color-input;
  color: t.$color-ai;
}

.assistant-body {
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
  gap: 10rpx;
  box-sizing: border-box;
}

.assistant-messages {
  flex: 1;
  min-height: 220rpx;
  padding-right: 4rpx;
  box-sizing: border-box;
}

.assistant-action-list {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  padding-top: 4rpx;
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
  border-radius: t.$radius-md;
  background: t.$color-card;
  border: 1rpx solid t.$color-line;
}

.assistant-message.mine {
  margin-left: auto;
  background: t.$color-brand-soft;
  border-color: transparent;
}

.assistant-message:not(.mine) {
  max-width: 100%;
  padding-left: 4rpx;
  padding-right: 4rpx;
  border-color: transparent;
  background: transparent;
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
  color: t.$color-ai;
}

.assistant-time {
  font-size: 20rpx;
  color: t.$color-ink-muted;
}

.assistant-copy {
  font-size: 26rpx;
  line-height: 1.75;
  color: t.$color-ink;
  white-space: pre-wrap;
}

.assistant-actions {
  display: flex;
  justify-content: flex-start;
}

.restart-button {
  height: 72rpx;
  min-height: 72rpx;
  padding: 0 24rpx;
  margin: 0;
  border: 1rpx solid t.$color-brand;
  border-radius: t.$radius-sm;
  background: t.$color-card;
  color: t.$color-brand-deep;
  font-size: 24rpx;
  font-weight: 650;
  line-height: 72rpx;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.restart-button::after {
  border: 0;
}

.button-label {
  display: flex;
  height: 100%;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.assistant-composer {
  flex-shrink: 0;
  padding: 10rpx;
  border-radius: t.$radius-md;
  background: t.$color-input;
  border: 1rpx solid t.$color-line;
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
  border-radius: t.$radius-sm;
  background: transparent;
  color: t.$color-ink;
  font-size: 27rpx;
  line-height: 38rpx;
  caret-color: t.$color-brand;
  cursor-color: t.$color-brand;
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
  border-radius: t.$radius-sm;
  background: t.$color-brand;
  color: t.$color-inverse;
  font-size: 25rpx;
  font-weight: 800;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-button.disabled {
  background: t.$color-line;
  color: t.$color-ink-muted;
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
  background: t.$color-card;
  border: 1rpx solid t.$color-line;
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
  background: t.$color-ai;
  opacity: 0.6;
}

.assistant-bottom-anchor {
  height: 148rpx;
}
</style>
