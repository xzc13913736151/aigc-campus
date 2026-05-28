<template>
  <view class="container">
    <view class="section hero">
      <text class="eyebrow">CampusClaw 论坛</text>
      <view style="height: 18rpx" />
      <text class="title">校园最新动态、求助、分享和灵感，都从这里开始。</text>

      <view v-if="!hasToken" class="login-cta">
        <button class="btn btn-primary" @tap="goLogin">微信一键登录</button>
      </view>
    </view>

    <view class="card section forum-filter-card">
      <view class="field">
        <text class="label">搜索内容</text>
        <input
          v-model="query"
          class="input"
          type="text"
          placeholder="搜索标题、正文或你关心的话题"
          @confirm="refreshAll"
        />
      </view>

      <view style="height: 18rpx" />

      <view class="action-row filter-action-row">
        <button class="btn btn-secondary" size="mini" :disabled="loadingList" @tap="refreshAll">
          {{ loadingList ? "搜索中..." : "搜索帖子" }}
        </button>
        <button class="create-post-btn" @tap="goCreate">
          <text class="create-post-label">发布帖子</text>
        </button>
        <button v-if="hasToken && myPosts.length" class="btn btn-ghost" size="mini" @tap="toggleMineOnly">
          {{ mineOnly ? "查看全部帖子" : "只看我的帖子" }}
        </button>
      </view>

      <view style="height: 18rpx" />

      <view class="category-row">
        <button
          v-for="item in categories"
          :key="item"
          class="category-chip"
          :class="{ active: selectedCategory === item }"
          @tap="selectCategory(item)"
        >
          {{ item }}
        </button>
      </view>

      <view v-if="pageError" style="height: 14rpx" />
      <text v-if="pageError" class="error">{{ pageError }}</text>
    </view>

    <view class="section">
      <view class="result-head">
        <view>
          <text class="section-title">{{ query.trim() ? "帖子搜索结果" : "最新帖子" }}</text>
          <view style="height: 8rpx" />
          <text class="section-desc">
            {{ query.trim() ? `已为你找到 ${displayPosts.length} 条相关帖子` : `当前共有 ${displayPosts.length} 条帖子` }}
          </text>
        </view>
        <text v-if="loadingList" class="helper">加载中...</text>
      </view>
    </view>

    <view v-if="displayPosts.length" class="grid section">
      <view v-for="post in displayPosts" :key="post.id" class="card post-card" @tap="openDetail(post.id)">
        <view class="post-head">
          <view style="flex: 1">
            <text class="section-title post-title">{{ post.title }}</text>
            <view style="height: 10rpx" />
            <text class="section-desc">{{ getPostPreview(post) }}</text>
          </view>
          <text class="tag">{{ post.category || "未分类" }}</text>
        </view>

        <view style="height: 16rpx" />

        <view class="meta-row">
          <text class="helper">{{ getAuthorName(post) }}</text>
          <text class="helper">{{ formatDate(post.created_at) }}</text>
        </view>

        <view v-if="post.image_urls.length" style="height: 16rpx" />
        <scroll-view
          v-if="post.image_urls.length"
          class="image-strip"
          scroll-x
          enhanced
          show-scrollbar="false"
        >
          <view class="image-strip-inner">
            <image
              v-for="url in post.image_urls"
              :key="url"
              class="cover-image"
              :src="url"
              mode="aspectFill"
              @tap="previewImages(post.image_urls, url)"
            />
          </view>
        </scroll-view>

        <view v-if="post.tags.length" style="height: 16rpx" />
        <view v-if="post.tags.length" class="tag-row">
          <text v-for="tag in post.tags" :key="tag" class="tag"
            >#{{ tag }}</text
          >
        </view>

        <view style="height: 18rpx" />

        <view class="stat-row">
          <text class="helper">点赞 {{ post.like_count }}</text>
          <text class="helper">评论 {{ post.comment_count }}</text>
        </view>

        <view style="height: 18rpx" />

        <view class="action-row">
          <button class="btn btn-ghost" size="mini" @tap.stop="openDetail(post.id)">
            查看详情
          </button>
          <button
            v-if="!isMine(post)"
            class="btn btn-secondary"
            size="mini"
            @tap.stop="contactAuthor(post)"
          >
            联系TA
          </button>
          <button
            class="btn btn-ghost"
            size="mini"
            :disabled="likingPostId === post.id"
            @tap.stop="handleLike(post.id)"
          >
            {{
              post.is_liked
                ? `已点赞 ${post.like_count}`
                : `点赞 ${post.like_count}`
            }}
          </button>
          <button
            v-if="isMine(post)"
            class="btn btn-secondary"
            size="mini"
            @tap.stop="goEdit(post.id)"
          >
            编辑
          </button>
        </view>
      </view>
    </view>

    <view v-else class="card empty">
      <text class="section-title">还没有匹配到帖子内容</text>
      <view style="height: 8rpx" />
      <text class="section-desc"
        >你可以换一个关键词、切换分类，或者直接发布第一条帖子。</text
      >
      <view style="height: 24rpx" />
      <button class="btn btn-primary" @tap="goCreate">去发帖</button>
    </view>

    <BottomTabBar />
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { onPullDownRefresh, onShow } from "@dcloudio/uni-app";

import BottomTabBar from "../../components/BottomTabBar.vue";
import type { ForumPost } from "../../types/api";
import {
  fetchForumPosts,
  fetchMyForumPosts,
  toggleForumPostLike,
} from "../../services/forum";
import {
  currentUser,
  ensureAuthenticated,
  isAuthenticated,
  redirectToLogin,
} from "../../utils/auth";
import { navigateTo } from "../../utils/navigation";
import { showToast } from "../../utils/ui";

const categories = [
  "全部",
  "校园日常",
  "学习交流",
  "活动组局",
  "实习求职",
  "项目合作",
  "组队招募",
  "情绪树洞",
];
const selectedCategory = ref("全部");
const query = ref("");
const posts = ref<ForumPost[]>([]);
const myPosts = ref<ForumPost[]>([]);
const loadingList = ref(false);
const likingPostId = ref("");
const pageError = ref("");
const hasToken = ref(isAuthenticated.value);
const mineOnly = ref(false);

const displayPosts = computed(() => {
  let source = mineOnly.value ? myPosts.value : posts.value;
  if (query.value.trim()) {
    const q = query.value.trim().toLowerCase()
    source = source.filter((p: ForumPost) =>
      p.title.toLowerCase().includes(q) ||
      p.body.toLowerCase().includes(q) ||
      (p.summary && p.summary.toLowerCase().includes(q))
    )
  }
  if (selectedCategory.value !== "全部") {
    source = (source as ForumPost[]).filter((p: ForumPost) => p.category === selectedCategory.value)
  }
  return [...source].sort((first, second) =>
    second.created_at.localeCompare(first.created_at),
  );
});

onMounted(() => {
  refreshAll();
});

onShow(() => {
  hasToken.value = isAuthenticated.value;
  refreshAll();
});

onPullDownRefresh(async () => {
  await refreshAll();
  uni.stopPullDownRefresh();
});

async function refreshAll() {
  loadingList.value = true;
  pageError.value = "";

  try {
    const category =
      selectedCategory.value === "全部" ? "" : selectedCategory.value;
    const [list, mine] = await Promise.all([
      fetchForumPosts(query.value, category),
      hasToken.value ? fetchMyForumPosts() : Promise.resolve([]),
    ]);
    posts.value = list;
    myPosts.value = mine;
  } catch (error) {
    pageError.value = error instanceof Error ? error.message : "加载帖子失败";
  } finally {
    loadingList.value = false;
    hasToken.value = isAuthenticated.value;
  }
}

function selectCategory(category: string) {
  selectedCategory.value = category;
  void refreshAll();
}

function toggleMineOnly() {
  mineOnly.value = !mineOnly.value;
}

function getAuthorName(post: ForumPost) {
  return post.author.nickname || post.author.full_name || post.author.email;
}

function getPostPreview(post: ForumPost) {
  return post.summary || post.body;
}

function isMine(post: ForumPost) {
  return post.author.email === (currentUser.value?.email ?? "");
}

function openDetail(postId: string) {
  navigateTo(`/pages/forum/detail?id=${postId}`);
}

function goCreate() {
  if (!ensureAuthenticated("/pages/forum/create")) {
    return;
  }
  navigateTo("/pages/forum/create");
}

function goEdit(postId: string) {
  if (!ensureAuthenticated(`/pages/forum/create?id=${postId}`)) {
    return;
  }
  navigateTo(`/pages/forum/create?id=${postId}`);
}

async function handleLike(postId: string) {
  if (!ensureAuthenticated(`/pages/forum/detail?id=${postId}`)) {
    return;
  }

  likingPostId.value = postId;
  try {
    const result = await toggleForumPostLike(postId);
    posts.value = posts.value.map((post) =>
      post.id === postId
        ? { ...post, is_liked: result.liked, like_count: result.like_count }
        : post,
    );
    myPosts.value = myPosts.value.map((post) =>
      post.id === postId
        ? { ...post, is_liked: result.liked, like_count: result.like_count }
        : post,
    );
  } catch (error) {
    showToast(error instanceof Error ? error.message : "点赞失败");
  } finally {
    likingPostId.value = "";
  }
}

function previewImages(urls: string[], current: string) {
  uni.previewImage({ current, urls });
}

function formatDate(value: string) {
  return value.replace("T", " ").slice(0, 16);
}

function goLogin() {
  redirectToLogin("/pages/forum/index");
}

function contactAuthor(post: ForumPost) {
  if (!ensureAuthenticated(`/pages/chat/index?targetUserId=${post.author.id}`)) {
    return
  }
  navigateTo(`/pages/chat/index?targetUserId=${post.author.id}`)
}
</script>

<style scoped lang="scss">
.hero {
  padding-top: 4rpx;
}

.entry-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20rpx;
}

.entry-card {
  padding: 28rpx;
}

.login-cta {
  margin-top: 24rpx;
}

.accent-team {
  background: linear-gradient(
    135deg,
    rgba(241, 107, 79, 0.12),
    rgba(255, 255, 255, 0.92)
  );
}

.accent-dating {
  background: linear-gradient(
    135deg,
    rgba(216, 164, 75, 0.14),
    rgba(255, 255, 255, 0.92)
  );
}

.entry-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #102133;
}

.entry-desc {
  font-size: 24rpx;
  line-height: 1.7;
  color: #6b7280;
}

.toolbar-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20rpx;
}

.toolbar-head > view {
  flex: 1;
  min-width: 0;
}

.create-post-btn {
  flex: 0 0 188rpx;
  max-width: 188rpx;
  min-width: 188rpx;
  height: 72rpx;
  min-height: 72rpx;
  padding: 0;
  margin: 0;
  border: 0;
  border-radius: 999rpx;
  background: #f16b4f;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.create-post-btn::after {
  border: 0;
}

.create-post-label {
  color: #fff;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1;
  text-align: center;
  white-space: nowrap;
}

.category-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.category-chip {
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

.category-chip::after {
  border: 0;
}

.category-chip.active {
  background: rgba(241, 107, 79, 0.14);
  color: #f16b4f;
  border-color: rgba(241, 107, 79, 0.22);
}

.forum-filter-card .action-row {
  justify-content: flex-start;
  align-items: center;
  gap: 14rpx;
}

.filter-action-row {
  flex-wrap: wrap;
}

.post-card,
.my-post-card {
  display: flex;
  flex-direction: column;
}

.my-post-card {
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(241, 107, 79, 0.08);
  border: 1rpx solid rgba(241, 107, 79, 0.14);
}

.post-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.post-title {
  margin-bottom: 0;
  font-size: 34rpx;
}

.result-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16rpx;
}

.meta-row,
.stat-row,
.action-row {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  flex-wrap: wrap;
}

.image-strip {
  width: 100%;
  white-space: nowrap;
}

.image-strip-inner {
  display: inline-flex;
  gap: 16rpx;
}

.cover-image {
  width: 220rpx;
  height: 164rpx;
  border-radius: 20rpx;
  background: rgba(16, 33, 51, 0.08);
  flex-shrink: 0;
}
</style>
