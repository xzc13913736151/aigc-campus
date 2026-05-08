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
          <text class="assistant-title">{{ sheetTitle }}</text>
          <view style="height: 8rpx" />
          <text class="assistant-subtitle">{{ sheetSubtitle }}</text>
        </view>
        <button class="assistant-close" @tap="emit('close')">收起</button>
      </view>

      <view class="assistant-meta">
        <view class="meta-pill accent">
          <text>当前场景：{{ contextLabel }}</text>
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
        <view class="guest-tips">
          <view v-for="tip in guestTips" :key="tip.title" class="guest-tip">
            <text class="guest-tip-title">{{ tip.title }}</text>
            <view style="height: 6rpx" />
            <text class="guest-tip-desc">{{ tip.description }}</text>
          </view>
        </view>
        <view style="height: 20rpx" />
        <button class="btn btn-primary" size="mini" @tap="goLogin">去登录</button>
      </view>

      <view v-else class="assistant-body">
        <view v-if="!messages.length && !bootstrapping" class="assistant-starter">
          <view class="starter-copy">
            <text class="section-title" style="font-size: 32rpx">{{ starterTitle }}</text>
            <view style="height: 8rpx" />
            <text class="section-desc">{{ starterDescription }}</text>
          </view>

          <view class="starter-grid">
            <button
              v-for="item in shortcutItems"
              :key="item.prompt"
              class="starter-card"
              :disabled="sending"
              @tap="handleShortcut(item.prompt)"
            >
              <text class="starter-card-title">{{ item.title }}</text>
              <view style="height: 8rpx" />
              <text class="starter-card-desc">{{ item.hint }}</text>
            </button>
          </view>
        </view>

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
            <text class="section-desc">先试试下面的快捷问题，或者直接输入你现在想解决的事情。</text>
          </view>
        </scroll-view>

        <view class="assistant-shortcuts">
          <button
            v-for="item in shortcutItems"
            :key="item.title"
            class="btn btn-ghost assistant-shortcut"
            size="mini"
            :disabled="sending || bootstrapping"
            @tap="handleShortcut(item.prompt)"
          >
            {{ item.title }}
          </button>
        </view>

        <view class="assistant-actions">
          <button class="btn btn-ghost" size="mini" :disabled="sending || bootstrapping" @tap="handleRestartSession">重新开始本页对话</button>
        </view>

        <view class="assistant-composer">
          <textarea
            v-model="draft"
            class="textarea assistant-textarea"
            maxlength="300"
            placeholder="告诉 AI 你想优化什么、想发什么、想怎么回复，或者你现在卡在哪里。"
          />
          <view class="composer-meta">
            <text class="helper">AI 会优先结合当前页面场景给你建议。</text>
            <text class="helper">{{ draft.length }}/300</text>
          </view>
          <text v-if="errorMessage" class="error">{{ errorMessage }}</text>
          <button class="btn btn-primary" size="mini" :disabled="sending || bootstrapping" @tap="handleSend">
            {{ sending ? '思考中...' : bootstrapping ? '准备中...' : '发送给 AI' }}
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

import type { AssistantMessage, AssistantSession } from '../../types/api'
import { createAssistantSession, fetchAssistantMessages, fetchAssistantSessions, sendAssistantMessage } from '../../services/assistant'
import { isAuthenticated, redirectToLogin } from '../../utils/auth'

type ShortcutItem = {
  title: string
  prompt: string
  hint: string
}

type SessionCacheEntry = {
  sessionId: string
  messages: AssistantMessage[]
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
const scrollIntoView = ref('')
const sessionCache = ref<Record<string, SessionCacheEntry>>({})
const sheetHeight = ref(64)
const dragStartY = ref(0)
const dragStartHeight = ref(64)

const sessionKey = computed(() => `${props.pageType}::${props.contextPath || ''}`)

const contextLabel = computed(() => {
  const mapping: Record<AssistantSession['page_type'], string> = {
    forum: '论坛首页',
    publish: '发布页',
    messages: '消息页',
    me: '我的主页',
    general: '通用场景',
  }
  return mapping[props.pageType]
})

const sheetTitle = computed(() => {
  const mapping: Record<AssistantSession['page_type'], string> = {
    forum: '论坛灵感助手',
    publish: '发布策划助手',
    messages: '聊天回复助手',
    me: '资料优化助手',
    general: 'CampusClaw AI 助手',
  }
  return mapping[props.pageType]
})

const sheetSubtitle = computed(() => {
  if (props.pageType === 'forum') {
    return '帮你想标题、改文案、判断内容是否适合发到论坛。'
  }
  if (props.pageType === 'publish') {
    return '帮你确定发布方向，整理帖子、组队或匹配文案。'
  }
  if (props.pageType === 'messages') {
    return '帮你润色回复语气，总结聊天重点，减少尴尬和卡壳。'
  }
  if (props.pageType === 'me') {
    return '帮你优化个人资料、自我介绍和标签表达。'
  }
  return '随时提供校园社交、内容发布和沟通表达建议。'
})

const starterTitle = computed(() => {
  if (props.pageType === 'forum') {
    return '先把论坛发帖这件事做顺'
  }
  if (props.pageType === 'publish') {
    return '先帮你理顺发布动作'
  }
  if (props.pageType === 'messages') {
    return '先把这段对话说自然'
  }
  if (props.pageType === 'me') {
    return '先把你的个人展示感拉起来'
  }
  return '先把当前问题说清楚'
})

const starterDescription = computed(() => {
  if (props.pageType === 'forum') {
    return '你可以让 AI 帮你起标题、润色正文，或者判断这条内容更适合什么发法。'
  }
  if (props.pageType === 'publish') {
    return '如果你不确定应该发帖子、组队还是恋爱匹配，这里可以先帮你拆解。'
  }
  if (props.pageType === 'messages') {
    return '把你想说的话丢进来，AI 可以帮你改成更礼貌、更自然或更有边界感的表达。'
  }
  if (props.pageType === 'me') {
    return '无论是昵称、介绍还是兴趣标签，都可以先让 AI 帮你组织成更自然的版本。'
  }
  return '先给 AI 一点上下文，它就能更像你的随身搭子。'
})

const shortcutItems = computed<ShortcutItem[]>(() => {
  if (props.pageType === 'forum') {
    return [
      { title: '想帖子标题', prompt: '帮我想 3 个适合校园论坛发布的帖子标题。', hint: '更吸引人，也更像真实同学会发的内容。' },
      { title: '润色正文', prompt: '帮我把下面这段论坛文案润色得更自然一点。', hint: '适合先把草稿扔进来再让 AI 改。' },
      { title: '判断适配', prompt: '这条内容适合发论坛吗？如果不适合，应该怎么改？', hint: '避免发错场景，降低违和感。' },
    ]
  }
  if (props.pageType === 'publish') {
    return [
      { title: '选发布方向', prompt: '我这段内容更适合发帖子、发组队，还是发恋爱匹配？', hint: '先定场景，再写文案会更顺。' },
      { title: '整理招募文案', prompt: '帮我整理一段组队招募文案，让目标和需求更清楚。', hint: '适合活动、项目、比赛招募。' },
      { title: '优化匹配介绍', prompt: '帮我把恋爱匹配资料写得更自然一点。', hint: '避免太模板化，也别太空。' },
    ]
  }
  if (props.pageType === 'messages') {
    return [
      { title: '礼貌回复', prompt: '帮我想一句礼貌但不过分热情的回复。', hint: '适合刚开始聊天或不想太冒进时。' },
      { title: '自然一点', prompt: '把我这句话改得更自然一点，不要太像模板。', hint: '保留你的语气，但更顺口。' },
      { title: '总结重点', prompt: '帮我总结一下这段聊天里最重要的点。', hint: '适合理清接下来怎么继续聊。' },
    ]
  }
  if (props.pageType === 'me') {
    return [
      { title: '写自我介绍', prompt: '帮我写一段自然一点的个人自我介绍。', hint: '适合资料页、组队和匹配展示。' },
      { title: '整理标签', prompt: '帮我整理一组更像真人的兴趣标签。', hint: '避免过于空泛或堆关键词。' },
      { title: '优化展示感', prompt: '我现在的头像、昵称、资料要怎么更有记忆点？', hint: '帮助你建立更清晰的第一印象。' },
    ]
  }
  return [
    { title: '给我个主意', prompt: '帮我出一个比较靠谱的下一步建议。', hint: '适合现在有点卡住的时候。' },
    { title: '整理思路', prompt: '帮我把现在的想法整理得清楚一点。', hint: '把杂乱内容变成可执行动作。' },
    { title: '下一步做什么', prompt: '我接下来最值得先做什么？', hint: '让 AI 直接帮你排序优先级。' },
  ]
})

const guestTips = [
  { title: '想标题', description: '帮你把论坛或发布文案起得更有点击欲。' },
  { title: '改表达', description: '帮你把组队、匹配和聊天里的语气改得更自然。' },
  { title: '理步骤', description: '帮你判断下一步更应该发什么、说什么、怎么推进。' },
]

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
    return
  }
  sessionId.value = cached.sessionId
  messages.value = [...cached.messages]
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
      messages.value = await fetchAssistantMessages(existingSession.id)
      persistCurrentSession()
      return
    }

    const session = await createAssistantSession({
      page_type: props.pageType,
      context_path: props.contextPath,
    })
    sessionId.value = session.id
    messages.value = await fetchAssistantMessages(session.id)
    persistCurrentSession()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'AI 助手暂时不可用'
  } finally {
    bootstrapping.value = false
  }
}

async function resolveExistingSession() {
  const sessions = await fetchAssistantSessions()
  const matched = sessions
    .filter((item) => item.page_type === props.pageType && (item.context_path || '') === (props.contextPath || ''))
    .sort((first, second) => second.updated_at.localeCompare(first.updated_at))[0]
  return matched ?? null
}

async function handleSend() {
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
  try {
    const response = await sendAssistantMessage(sessionId.value, { body })
    messages.value = [...messages.value, response.user_message, response.assistant_message]
    persistCurrentSession()
  } catch (error) {
    draft.value = body
    errorMessage.value = error instanceof Error ? error.message : '发送失败'
  } finally {
    pendingUserBody.value = ''
    sending.value = false
  }
}

function handleShortcut(text: string) {
  draft.value = text
  void handleSend()
}

async function handleRestartSession() {
  sessionId.value = ''
  messages.value = []
  pendingUserBody.value = ''
  errorMessage.value = ''

  const nextCache = { ...sessionCache.value }
  delete nextCache[sessionKey.value]
  sessionCache.value = nextCache

  await ensureSessionReady()
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
  z-index: 998;
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
  padding: 22rpx 24rpx calc(env(safe-area-inset-bottom) + 24rpx);
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
  line-height: 56rpx;
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
  gap: 16rpx;
}

.assistant-starter {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.starter-grid {
  display: grid;
  grid-template-columns: repeat(1, minmax(0, 1fr));
  gap: 14rpx;
}

.starter-card {
  padding: 22rpx;
  border-radius: 24rpx;
  border: 1rpx solid rgba(16, 33, 51, 0.08);
  background: rgba(255, 255, 255, 0.9);
  text-align: left;
}

.starter-card::after {
  border: 0;
}

.starter-card-title {
  font-size: 28rpx;
  font-weight: 700;
  color: #102133;
}

.starter-card-desc {
  font-size: 22rpx;
  line-height: 1.6;
  color: #6b7280;
}

.assistant-messages {
  flex: 1;
  min-height: 220rpx;
  padding-right: 4rpx;
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

.assistant-shortcuts {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.assistant-shortcut {
  min-height: 68rpx;
  padding: 0 24rpx;
  font-size: 22rpx;
}

.assistant-actions {
  display: flex;
  justify-content: flex-end;
}

.assistant-composer {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  padding: 18rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.86);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
}

.assistant-textarea {
  min-height: 128rpx;
  background: rgba(255, 250, 245, 0.98);
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

.guest-tips {
  display: grid;
  gap: 14rpx;
}

.guest-tip {
  padding: 20rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.88);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
  text-align: left;
}

.guest-tip-title {
  font-size: 26rpx;
  font-weight: 700;
  color: #102133;
}

.guest-tip-desc {
  font-size: 22rpx;
  line-height: 1.6;
  color: #6b7280;
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
