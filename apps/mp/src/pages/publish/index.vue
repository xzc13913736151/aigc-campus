<template>
  <view class="container">
    <view class="section hero">
      <text class="eyebrow">CampusClaw 匹配</text>
      <view style="height: 18rpx" />
      <text class="title">找到合适的人、队伍和校园交易机会。</text>
    </view>

    <view class="match-list">
      <view class="match-card" @tap="goTeammates">
        <view class="match-icon-wrap teammates">
          <text class="match-icon-text">组队</text>
        </view>
        <view class="match-info">
          <text class="match-title">组队匹配</text>
          <text class="match-desc">找队友、招募成员、发起项目合作</text>
          <view class="match-tags">
            <text class="match-tag">比赛组队</text>
            <text class="match-tag">项目合作</text>
            <text class="match-tag">学习搭子</text>
          </view>
        </view>
      </view>

      <view class="match-card" @tap="goDating">
        <view class="match-icon-wrap dating">
          <text class="match-icon-text">恋爱</text>
        </view>
        <view class="match-info">
          <text class="match-title">恋爱匹配</text>
          <text class="match-desc">遇见那个TA，告别单身</text>
          <view class="match-tags">
            <text class="match-tag">心动对象</text>
            <text class="match-tag">校园恋爱</text>
            <text class="match-tag">缘分匹配</text>
          </view>
        </view>
      </view>

      <view class="match-card" @tap="goTrade">
        <view class="match-icon-wrap trade">
          <text class="match-icon-text">交易</text>
        </view>
        <view class="match-info">
          <text class="match-title">交易匹配</text>
          <text class="match-desc">买卖闲置、交换物品、技能服务</text>
          <view class="match-tags">
            <text class="match-tag">闲置交易</text>
            <text class="match-tag">物品交换</text>
            <text class="match-tag">技能服务</text>
          </view>
        </view>
      </view>
    </view>

    <view class="tips-card">
      <text class="tips-title">使用提示</text>
      <view style="height: 16rpx" />
      <text class="tips-item">• 组队匹配：适合发布招募需求，寻找志同道合的伙伴</text>
      <text class="tips-item">• 恋爱匹配：完善资料后可在广场展示，提高曝光</text>
      <text class="tips-item">• 交易匹配：发布闲置物品或求购需求，快速匹配</text>
    </view>

    <BottomTabBar />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import BottomTabBar from '../../components/BottomTabBar.vue'
import { isAuthenticated, redirectToLogin } from '../../utils/auth'
import { navigateTo } from '../../utils/navigation'

const hasToken = computed(() => isAuthenticated.value)

function ensureAuthAndNavigate(path: string) {
  if (!hasToken.value) {
    redirectToLogin(path)
    return
  }
  navigateTo(path)
}

function goTeammates() {
  ensureAuthAndNavigate('/pages/teammates/index')
}

function goDating() {
  ensureAuthAndNavigate('/pages/dating/index')
}

function goTrade() {
  ensureAuthAndNavigate('/pages/trade/index')
}
</script>

<style scoped lang="scss">
.container {
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(241, 107, 79, 0.18), transparent 34%),
    radial-gradient(circle at bottom right, rgba(216, 164, 75, 0.2), transparent 30%),
    #f5f1e8;
  padding-bottom: 180rpx;
}

.hero {
  padding-top: 4rpx;
}

.match-list {
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.match-card {
  display: flex;
  align-items: center;
  padding: 28rpx;
  background: rgba(255, 255, 255, 0.88);
  border-radius: 28rpx;
  border: 1rpx solid rgba(16, 33, 51, 0.08);
  gap: 24rpx;
}

.match-icon-wrap {
  width: 100rpx;
  height: 100rpx;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.match-icon-wrap.teammates {
  background: linear-gradient(135deg, #8b654f, #ad8b76);
}

.match-icon-wrap.dating {
  background: linear-gradient(135deg, #c15f3c, #ff8a6b);
}

.match-icon-wrap.trade {
  background: linear-gradient(135deg, #557a5d, #52c775);
}

.match-icon-text {
  color: #fff;
  font-size: 28rpx;
  font-weight: 700;
}

.match-info {
  flex: 1;
  min-width: 0;
}

.match-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #2f2a24;
  display: block;
}

.match-desc {
  font-size: 24rpx;
  color: #6f675d;
  margin-top: 6rpx;
  display: block;
}

.match-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 12rpx;
}

.match-tag {
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(16, 33, 51, 0.06);
  color: #2f2a24;
  font-size: 20rpx;
}

.tips-card {
  margin: 0 24rpx;
  padding: 28rpx;
  background: rgba(255, 255, 255, 0.74);
  border-radius: 24rpx;
  border: 1rpx solid rgba(16, 33, 51, 0.08);
}

.tips-title {
  font-size: 28rpx;
  font-weight: 700;
  color: #2f2a24;
}

.tips-item {
  display: block;
  font-size: 24rpx;
  color: #6f675d;
  line-height: 1.8;
}
</style>
