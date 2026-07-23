<template>
  <view class="container">
    <view class="card section plain-hero">
      <text class="eyebrow">CampusClaw 黑名单</text>
      <view style="height: 18rpx" />
      <text class="title">黑名单是你的个人安全开关，用来主动切断不想继续发生的连接。</text>
      <view style="height: 18rpx" />
      <text class="subtitle">被你拉黑的人不会继续出现在匹配候选人中，也不能再与你建立或继续聊天。</text>
    </view>

    <view class="grid stats-grid section">
      <view class="card stat-card">
        <text class="stat-value">{{ blocks.length }}</text>
        <view style="height: 8rpx" />
        <text class="section-desc">已拉黑用户</text>
      </view>
      <view class="card stat-card">
        <text class="stat-value">{{ recentBlocks }}</text>
        <view style="height: 8rpx" />
        <text class="section-desc">近 7 天新增</text>
      </view>
    </view>

    <view class="card section">
      <view class="section-head">
        <view>
          <text class="section-title">黑名单列表</text>
          <view style="height: 8rpx" />
          <text class="section-desc">如果你希望恢复联系，可以在这里解除拉黑。</text>
        </view>
        <button class="btn btn-ghost" :disabled="loading" @tap="loadBlocks">
          {{ loading ? '刷新中...' : '刷新' }}
        </button>
      </view>

      <view style="height: 20rpx" />

      <view v-if="blocks.length" class="grid">
        <view v-for="item in blocks" :key="item.id" class="card block-card">
          <view class="block-head">
            <view style="flex: 1">
              <text class="section-title block-name">{{ getUserName(item) }}</text>
              <view style="height: 8rpx" />
              <text class="helper">{{ item.blocked_user_detail.email }}</text>
            </view>
            <text class="tag">已拉黑</text>
          </view>
          <view style="height: 14rpx" />
          <text class="section-desc">拉黑原因：{{ item.reason || '未填写原因' }}</text>
          <view style="height: 10rpx" />
          <text class="helper">拉黑时间：{{ formatDate(item.created_at) }}</text>
          <view style="height: 18rpx" />
          <button class="btn btn-secondary" :disabled="removingId === item.id" @tap="handleUnblock(item.id)">
            {{ removingId === item.id ? '处理中...' : '解除拉黑' }}
          </button>
        </view>
      </view>

      <view v-else class="empty">
        <text class="section-title" style="font-size: 32rpx">当前没有黑名单记录</text>
        <view style="height: 10rpx" />
        <text class="section-desc">如果你在匹配或聊天里遇到不想继续联系的人，后续可以直接把对方加入黑名单。</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import type { BlockItem } from '../../types/api'
import { deleteBlock, fetchMyBlocks } from '../../services/moderation'
import { ensureAuthenticated } from '../../utils/auth'
import { showToast } from '../../utils/ui'

const blocks = ref<BlockItem[]>([])
const loading = ref(false)
const removingId = ref('')

const recentBlocks = computed(() => {
  const now = Date.now()
  const sevenDays = 7 * 24 * 60 * 60 * 1000
  return blocks.value.filter((item) => now - new Date(item.created_at).getTime() <= sevenDays).length
})

async function loadBlocks() {
  loading.value = true
  try {
    blocks.value = await fetchMyBlocks()
  } catch (error) {
    showToast(error instanceof Error ? error.message : '加载黑名单失败')
  } finally {
    loading.value = false
  }
}

async function handleUnblock(blockId: string) {
  removingId.value = blockId
  try {
    await deleteBlock(blockId)
    blocks.value = blocks.value.filter((item) => item.id !== blockId)
    showToast('已解除拉黑', 'success')
  } catch (error) {
    showToast(error instanceof Error ? error.message : '解除拉黑失败')
  } finally {
    removingId.value = ''
  }
}

function getUserName(item: BlockItem) {
  return item.blocked_user_detail.nickname || item.blocked_user_detail.full_name || item.blocked_user_detail.email
}

function formatDate(value: string) {
  return value.replace('T', ' ').slice(0, 16)
}

onShow(() => {
  if (!ensureAuthenticated('/pages/blocks/index')) {
    return
  }
  loadBlocks()
})
</script>

<style scoped lang="scss">
.plain-hero {
  box-shadow: 0 16rpx 48rpx rgba(16, 33, 51, 0.06);
}

.stats-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.stat-card {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 42rpx;
  font-weight: 700;
  color: #2f2a24;
}

.section-head,
.block-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.block-card {
  display: flex;
  flex-direction: column;
}

.block-name {
  margin-bottom: 0;
  font-size: 30rpx;
}
</style>
