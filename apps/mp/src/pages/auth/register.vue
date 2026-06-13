<template>
  <view class="container">
    <view class="section hero">
      <text class="eyebrow">CampusClaw 登录入口</text>
      <view style="height: 18rpx" />
      <text class="title">演示版不再单独提供注册表单，统一通过账号登录进入。</text>
      <view style="height: 18rpx" />
      <text class="subtitle">这样可以减少输入步骤，也更适合比赛现场快速体验。</text>
    </view>

    <view class="grid info-grid section">
      <view v-for="item in items" :key="item.title" class="card info-card">
        <text class="section-title" style="font-size: 32rpx">{{ item.title }}</text>
        <view style="height: 8rpx" />
        <text class="section-desc">{{ item.description }}</text>
      </view>
    </view>

    <view class="card">
      <text class="section-title">下一步怎么做</text>
      <view style="height: 10rpx" />
        <text class="section-desc">如果你是第一次进来，直接使用邮箱密码或演示账号登录即可，后面会自动进入资料补全流程。</text>
      <view style="height: 24rpx" />
      <view class="btn-row">
        <button class="btn btn-primary" @tap="goLogin">前往账号登录</button>
        <button class="btn btn-ghost" @tap="goForum">先看论坛首页</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { navigateTo, switchTab } from '../../utils/navigation'

const items = [
  {
    title: '统一入口',
    description: '所有用户都通过账号登录进入，避免再维护独立注册流程。',
  },
  {
    title: '首次补全',
    description: '第一次登录后会先引导补全资料，后续再进入论坛、组队和消息等核心页面。',
  },
  {
    title: '更适合小程序',
    description: '减少表单输入，更适合演示版里的自然使用路径。',
  },
]

function goLogin() {
  navigateTo('/pages/auth/login')
}

function goForum() {
  switchTab('/pages/forum/index')
}
</script>

<style scoped lang="scss">
.hero {
  padding-top: 12rpx;
}

.info-grid {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

.info-card {
  padding: 28rpx;
}
</style>
