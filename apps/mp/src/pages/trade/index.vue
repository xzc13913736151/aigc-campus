<template>
  <view class="container">
    <AssistantSheet
      :visible="assistantVisible"
      page-type="publish"
      :context-path="`/pages/trade/index?assistantTarget=${assistantTargetPostId}`"
      context-target-type="trade_post"
      :context-target-id="assistantTargetPostId"
      @close="assistantVisible = false"
    />

    <view class="section hero">
      <text class="eyebrow">CampusClaw 交易匹配</text>
      <view style="height: 18rpx" />
      <text class="title">让闲置、求购和交换需求更快遇到合适的人。</text>
    </view>

    <view v-if="!hasToken" class="card empty">
      <text class="section-desc">登录后才能查看和发布交易帖子。</text>
      <view style="height: 24rpx" />
      <button class="btn btn-primary" @tap="goLogin">去登录</button>
    </view>

    <view v-else class="section">
      <view class="grid stats-grid">
        <view class="card stat-card">
          <text class="stat-value">{{ posts.length }}</text>
          <view style="height: 8rpx" />
          <text class="section-desc">广场帖子</text>
        </view>
        <view class="card stat-card">
          <text class="stat-value">{{ myPosts.length }}</text>
          <view style="height: 8rpx" />
          <text class="section-desc">我发布的</text>
        </view>
      </view>

      <view v-if="myPosts.length" style="height: 20rpx" />
      <view v-if="myPosts.length" class="card section">
        <view class="toolbar-head">
          <view>
            <text class="section-title">我的交易管理</text>
            <view style="height: 8rpx" />
            <text class="section-desc">可以快速标记预定、完成或关闭。</text>
          </view>
        </view>
        <view style="height: 18rpx" />
        <view class="my-trade-list">
          <view v-for="post in myPosts" :key="post.id" class="my-trade-item">
            <view class="my-trade-main">
              <text class="my-trade-title">{{ post.title }}</text>
              <view style="height: 8rpx" />
              <view class="status-badge" :class="`status-${post.status}`">{{ getStatusLabel(post.status) }}</view>
            </view>
            <scroll-view scroll-x class="status-scroll" enhanced show-scrollbar="false">
              <view class="status-row">
                <button
                  v-for="item in statusOptions"
                  :key="item.value"
                  class="status-chip"
                  :class="{ active: post.status === item.value }"
                  :disabled="statusUpdatingId === post.id || post.status === item.value"
                  @tap="changePostStatus(post, item.value)"
                >
                  {{ statusUpdatingId === post.id && post.status !== item.value ? '处理中' : item.label }}
                </button>
              </view>
            </scroll-view>
          </view>
        </view>
      </view>

      <view class="card section">
        <view class="toolbar-head">
          <view>
            <text class="section-title">交易广场</text>
            <view style="height: 8rpx" />
            <text class="section-desc">下拉页面可以刷新内容。</text>
          </view>
          <button class="btn btn-secondary" @tap="goCreate">发布交易</button>
        </view>

        <view style="height: 20rpx" />

        <view class="field">
          <text class="label">搜索</text>
          <input
            v-model="searchKeyword"
            class="input"
            type="text"
            placeholder="搜索标题或描述"
            @confirm="loadPosts(true)"
          />
        </view>

        <view style="height: 18rpx" />

        <scroll-view scroll-x class="type-scroll" enhanced show-scrollbar="false">
          <view class="type-row">
            <button
              v-for="item in typeFilters"
              :key="item.value"
              class="type-chip"
              :class="{ active: activeType === item.value }"
              @tap="handleTypeFilter(item.value)"
            >
              {{ item.label }}
            </button>
          </view>
        </scroll-view>
      </view>
    </view>

    <view v-if="posts.length" class="section">
      <view class="result-head">
        <text class="section-title">帖子列表</text>
        <text class="helper">{{ loading ? '加载中...' : `共 ${displayPosts.length} 条` }}</text>
      </view>
      <view style="height: 16rpx" />

      <view class="post-grid">
        <view
          v-for="post in displayPosts"
          :key="post.id"
          class="post-card"
        >
          <view class="post-header">
            <view class="post-type-badge" :class="post.post_type">
              <text>{{ getTypeLabel(post.post_type) }}</text>
            </view>
            <view class="status-badge" :class="`status-${post.status}`">{{ getStatusLabel(post.status) }}</view>
            <text class="post-price">
              {{ post.price ? `¥${post.price}` : post.post_type === 'service' ? '免费' : '面议' }}
            </text>
          </view>

          <view style="height: 12rpx" />
          <text class="post-title">{{ post.title }}</text>
          <view style="height: 8rpx" />
          <text class="post-desc">{{ post.description.slice(0, 60) }}{{ post.description.length > 60 ? '...' : '' }}</text>

          <view v-if="post.tags.length" style="height: 12rpx" />
          <view v-if="post.tags.length" class="tag-row">
            <text v-for="tag in post.tags" :key="tag" class="tag">#{{ tag }}</text>
          </view>

          <view style="height: 12rpx" />
          <view class="post-meta">
            <text class="helper">{{ getAuthorName(post) }}</text>
            <text class="helper">{{ post.view_count }}次浏览</text>
          </view>

          <view style="height: 12rpx" />
          <view class="action-row">
            <button
              v-if="!isMine(post)"
              class="btn btn-ghost"
              :disabled="reportingId === post.id"
              @tap="reportTradePost(post)"
            >
              {{ reportingId === post.id ? '提交中...' : '举报' }}
            </button>
            <button
              v-if="!isMine(post)"
              class="btn btn-ghost"
              @tap="openPostAssistant(post.id)"
            >
              让 AI 帮我处理
            </button>
            <button
              v-if="!isMine(post)"
              class="btn btn-ghost"
              :disabled="favoritingId === post.id"
              @tap="toggleFavorite(post)"
            >
              {{ favoritingId === post.id ? '处理中...' : post.is_favorited ? '已收藏' : '收藏' }}
            </button>
            <button
              v-if="!isMine(post)"
              class="btn btn-secondary"
              @tap="contactAuthor(post)"
            >
              联系TA
            </button>
            <button
              v-if="isMine(post)"
              class="btn btn-ghost"
              @tap="deletePost(post.id)"
            >
              删除
            </button>
          </view>
        </view>
      </view>

      <view v-if="loading" class="loading-more">
        <text>加载中...</text>
      </view>
      <view v-if="!hasMore && posts.length" class="no-more">
        <text>没有更多了</text>
      </view>
    </view>

    <view v-else-if="!loading && !pageError" class="card empty">
      <text class="section-title">暂无相关帖子</text>
      <view style="height: 8rpx" />
      <text class="section-desc">试试其他分类或发布你的闲置。</text>
    </view>

    <view v-if="pageError" class="card empty">
      <text class="section-title">交易内容暂时不可用</text>
      <view style="height: 8rpx" />
      <text class="section-desc">{{ pageError }}</text>
      <view style="height: 24rpx" />
      <button class="btn btn-primary" :disabled="loading" @tap="loadPosts(true)">
        {{ loading ? '重试中...' : '重新加载' }}
      </button>
    </view>

    <view v-if="loading && !posts.length" class="loading-state">
      <text>加载中...</text>
    </view>

    <BottomTabBar />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'

import AssistantSheet from '../../components/assistant/AssistantSheet.vue'
import BottomTabBar from '../../components/BottomTabBar.vue'
import { createModerationReport } from '../../services/moderation'
import {
  deleteTradePost,
  favoriteTradePost,
  fetchMyTradePosts,
  fetchTradePosts,
  type TradePost,
  unfavoriteTradePost,
  updateTradePostStatus,
} from '../../services/trade'
import { currentUser, ensureAuthenticated, isAuthenticated, redirectToLogin } from '../../utils/auth'
import { navigateTo } from '../../utils/navigation'
import { showToast } from '../../utils/ui'

const hasToken = computed(() => isAuthenticated.value)

const assistantVisible = ref(false)
const assistantTargetPostId = ref('')
const posts = ref<TradePost[]>([])
const myPosts = ref<TradePost[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const activeType = ref('')
const hasMore = ref(true)
const pageError = ref('')
const favoritingId = ref('')
const statusUpdatingId = ref('')
const reportingId = ref('')

const typeFilters = [
  { value: '', label: '全部' },
  { value: 'sell', label: '出售' },
  { value: 'buy', label: '求购' },
  { value: 'exchange', label: '交换' },
  { value: 'service', label: '服务' },
]

const statusOptions: Array<{ value: TradePost['status']; label: string }> = [
  { value: 'open', label: '出售中' },
  { value: 'reserved', label: '已预定' },
  { value: 'completed', label: '已完成' },
  { value: 'closed', label: '已关闭' },
]

const displayPosts = computed(() => {
  let filtered = posts.value
  if (searchKeyword.value.trim()) {
    const q = searchKeyword.value.trim().toLowerCase()
    filtered = filtered.filter(p =>
      p.title.toLowerCase().includes(q) || p.description.toLowerCase().includes(q)
    )
  }
  return filtered
})

onShow(() => {
  if (!hasToken.value) return
  loadPosts()
})

onPullDownRefresh(async () => {
  await loadPosts(true)
  uni.stopPullDownRefresh()
})

onReachBottom(() => {
  void loadPosts(true)
})

async function loadPosts(reset = false) {
  if (loading.value) return
  loading.value = true
  pageError.value = ''

  try {
    const [data, mine] = await Promise.all([
      fetchTradePosts({
        q: searchKeyword.value || undefined,
        type: activeType.value || undefined,
      }),
      fetchMyTradePosts(),
    ])
    posts.value = data
    myPosts.value = mine
    hasMore.value = data.length >= 20
  } catch (error) {
    const message = error instanceof Error ? error.message : '交易内容加载失败'
    pageError.value = message
    showToast(message, 'none')
  } finally {
    loading.value = false
  }
}

function handleTypeFilter(type: string) {
  activeType.value = type
  loadPosts(true)
}

function getTypeLabel(type: string) {
  const map: Record<string, string> = {
    sell: '出售',
    buy: '求购',
    exchange: '交换',
    service: '服务',
  }
  return map[type] || type
}

function getStatusLabel(status: TradePost['status']) {
  const map: Record<TradePost['status'], string> = {
    open: '出售中',
    reserved: '已预定',
    completed: '已完成',
    closed: '已关闭',
  }
  return map[status] || status
}

function getAuthorName(post: TradePost) {
  return post.author.nickname || post.author.full_name || post.author.email
}

function isMine(post: TradePost) {
  return post.author.email === (currentUser.value?.email ?? '')
}

function contactAuthor(post: TradePost) {
  if (!ensureAuthenticated(`/pages/chat/index?targetUserId=${post.author.id}`)) return
  navigateTo(`/pages/chat/index?targetUserId=${post.author.id}&sourceType=trade_post&sourceId=${post.id}`)
}

function openPostAssistant(postId: string) {
  if (!ensureAuthenticated('/pages/trade/index')) return
  assistantTargetPostId.value = postId
  assistantVisible.value = true
}

async function deletePost(id: string) {
  try {
    await deleteTradePost(id)
    posts.value = posts.value.filter(p => p.id !== id)
    myPosts.value = myPosts.value.filter(p => p.id !== id)
    showToast('已删除', 'success')
  } catch (error) {
    showToast('删除失败', 'none')
  }
}

async function changePostStatus(post: TradePost, nextStatus: TradePost['status']) {
  if (statusUpdatingId.value || post.status === nextStatus) return
  statusUpdatingId.value = post.id
  try {
    const updated = await updateTradePostStatus(post.id, nextStatus)
    myPosts.value = myPosts.value.map((item) => (item.id === post.id ? updated : item))
    if (updated.status === 'open') {
      posts.value = posts.value.some((item) => item.id === updated.id)
        ? posts.value.map((item) => (item.id === updated.id ? updated : item))
        : [updated, ...posts.value]
    } else {
      posts.value = posts.value.filter((item) => item.id !== updated.id)
    }
    showToast('交易状态已更新', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '状态更新失败')
  } finally {
    statusUpdatingId.value = ''
  }
}

async function reportTradePost(post: TradePost) {
  if (!ensureAuthenticated('/pages/trade/index')) return
  reportingId.value = post.id
  try {
    await createModerationReport({
      target_type: 'trade_post',
      target_id: post.id,
      reason: '交易内容可能违规',
      details: `${post.title}：${post.description.slice(0, 80)}`,
    })
    showToast('举报已提交，我们会尽快处理', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '举报失败')
  } finally {
    reportingId.value = ''
  }
}

async function toggleFavorite(post: TradePost) {
  if (!ensureAuthenticated('/pages/trade/index')) return
  if (isMine(post)) {
    showToast('不能收藏自己发布的交易')
    return
  }
  favoritingId.value = post.id
  try {
    if (post.is_favorited) {
      await unfavoriteTradePost(post.id)
    } else {
      await favoriteTradePost(post.id)
    }
    posts.value = posts.value.map((item) =>
      item.id === post.id ? { ...item, is_favorited: !post.is_favorited } : item,
    )
    showToast(post.is_favorited ? '已取消收藏' : '已收藏', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '收藏操作失败')
  } finally {
    favoritingId.value = ''
  }
}

function goCreate() {
  if (!ensureAuthenticated('/pages/trade/create')) return
  navigateTo('/pages/trade/create')
}

function goLogin() {
  redirectToLogin('/pages/trade/index')
}
</script>

<style scoped lang="scss">
.container {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(241, 107, 79, 0.18), transparent 34%),
    radial-gradient(circle at bottom right, rgba(216, 164, 75, 0.2), transparent 30%),
    #f7f1e8;
  padding-bottom: 180rpx;
}

.hero {
  padding-top: 4rpx;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20rpx;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 34rpx;
  font-weight: 700;
  color: #102133;
}

.toolbar-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20rpx;
}

.type-scroll {
  width: 100%;
  white-space: nowrap;
}

.type-row {
  display: inline-flex;
  gap: 16rpx;
}

.type-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 66rpx;
  padding: 0 24rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.86);
  border: 1rpx solid rgba(16, 33, 51, 0.1);
  color: #102133;
  font-size: 24rpx;
  font-weight: 600;
  line-height: 1;
  flex-shrink: 0;
}

.type-chip::after {
  border: 0;
}

.type-chip.active {
  background: rgba(241, 107, 79, 0.14);
  border-color: rgba(241, 107, 79, 0.22);
  color: #f16b4f;
}

.result-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.post-grid {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.post-card {
  padding: 24rpx;
  background: rgba(255, 255, 255, 0.88);
  border-radius: 24rpx;
  border: 1rpx solid rgba(16, 33, 51, 0.08);
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12rpx;
}

.post-type-badge {
  flex-shrink: 0;
  padding: 8rpx 16rpx;
  border-radius: 8rpx;
  font-size: 22rpx;
  color: #fff;
  font-weight: 600;
}

.status-badge {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44rpx;
  padding: 0 16rpx;
  border-radius: 999rpx;
  font-size: 21rpx;
  font-weight: 700;
}

.status-open {
  background: rgba(46, 125, 73, 0.12);
  color: #2e7d49;
}

.status-reserved {
  background: rgba(245, 164, 76, 0.15);
  color: #a76310;
}

.status-completed {
  background: rgba(74, 144, 226, 0.14);
  color: #2f6faa;
}

.status-closed {
  background: rgba(16, 33, 51, 0.1);
  color: #637083;
}

.post-type-badge.sell {
  background: #2e7d49;
}

.post-type-badge.buy {
  background: #4a90e2;
}

.post-type-badge.exchange {
  background: #f5a44c;
}

.post-type-badge.service {
  background: #9b59b6;
}

.post-price {
  margin-left: auto;
  font-size: 32rpx;
  font-weight: 700;
  color: #f16b4f;
}

.my-trade-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.my-trade-item {
  padding: 18rpx;
  border-radius: 20rpx;
  background: rgba(247, 241, 232, 0.86);
  border: 1rpx solid rgba(16, 33, 51, 0.08);
}

.my-trade-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.my-trade-title {
  min-width: 0;
  color: #102133;
  font-size: 27rpx;
  font-weight: 800;
}

.status-scroll {
  width: 100%;
  margin-top: 14rpx;
  white-space: nowrap;
}

.status-row {
  display: inline-flex;
  gap: 12rpx;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 58rpx;
  padding: 0 20rpx;
  margin: 0;
  border: 0;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.9);
  color: #44515f;
  font-size: 23rpx;
  font-weight: 700;
  line-height: 1;
}

.status-chip::after {
  border: 0;
}

.status-chip.active {
  background: #102133;
  color: #fff;
}

.post-title {
  font-size: 30rpx;
  font-weight: 700;
  color: #102133;
}

.post-desc {
  font-size: 26rpx;
  color: #7a7f87;
  line-height: 1.5;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.post-meta {
  display: flex;
  justify-content: space-between;
}

.action-row {
  display: flex;
  gap: 16rpx;
}

.loading-more,
.no-more {
  text-align: center;
  padding: 24rpx;
  font-size: 24rpx;
  color: #7a7f87;
}

.loading-state {
  text-align: center;
  padding: 100rpx;
}
</style>
