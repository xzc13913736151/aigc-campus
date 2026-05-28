<template>
  <view class="container">
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

      <view class="card section">
        <view class="toolbar-head">
          <view>
            <text class="section-title">交易广场</text>
            <view style="height: 8rpx" />
            <text class="section-desc">下拉页面可以刷新内容。</text>
          </view>
          <button class="btn btn-secondary" size="mini" @tap="goCreate">发布交易</button>
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
              size="mini"
              :disabled="favoritingId === post.id"
              @tap="toggleFavorite(post)"
            >
              {{ favoritingId === post.id ? '处理中...' : post.is_favorited ? '已收藏' : '收藏' }}
            </button>
            <button
              v-if="!isMine(post)"
              class="btn btn-secondary"
              size="mini"
              @tap="contactAuthor(post)"
            >
              联系TA
            </button>
            <button
              v-if="isMine(post)"
              class="btn btn-ghost"
              size="mini"
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

import BottomTabBar from '../../components/BottomTabBar.vue'
import {
  deleteTradePost,
  favoriteTradePost,
  fetchMyTradePosts,
  fetchTradePosts,
  type TradePost,
  unfavoriteTradePost,
} from '../../services/trade'
import { currentUser, ensureAuthenticated, isAuthenticated, redirectToLogin } from '../../utils/auth'
import { navigateTo } from '../../utils/navigation'
import { showToast } from '../../utils/ui'

const hasToken = computed(() => isAuthenticated.value)

const posts = ref<TradePost[]>([])
const myPosts = ref<TradePost[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const activeType = ref('')
const hasMore = ref(true)
const pageError = ref('')
const favoritingId = ref('')

const typeFilters = [
  { value: '', label: '全部' },
  { value: 'sell', label: '出售' },
  { value: 'buy', label: '求购' },
  { value: 'exchange', label: '交换' },
  { value: 'service', label: '服务' },
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
}

.post-type-badge {
  padding: 8rpx 16rpx;
  border-radius: 8rpx;
  font-size: 22rpx;
  color: #fff;
  font-weight: 600;
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
  font-size: 32rpx;
  font-weight: 700;
  color: #f16b4f;
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
