<template>
  <view class="container">
    <view class="section hero">
      <text class="eyebrow">CampusClaw 登录</text>
      <view style="height: 18rpx" />
      <text class="title">使用微信一键登录，几秒内进入 CampusClaw。</text>
      <view style="height: 18rpx" />
      <text class="subtitle">
        首次登录成功后，系统会先引导你补全头像、昵称和基础资料。完成后会自动回到你原本想去的页面。
      </text>
    </view>

    <view class="grid info-grid section">
      <view v-for="item in infoItems" :key="item.title" class="card info-card">
        <text class="section-title" style="font-size: 32rpx">{{ item.title }}</text>
        <view style="height: 8rpx" />
        <text class="section-desc">{{ item.description }}</text>
      </view>
    </view>

    <view class="card">
      <text class="section-title">登录说明</text>
      <view style="height: 10rpx" />
      <text class="section-desc">登录后会自动建立会话，并判断你是否需要优先完成资料补全。</text>
      <view style="height: 24rpx" />

      <view class="form login-form">
        <text v-if="errorMessage" class="error">{{ errorMessage }}</text>
        <button class="btn btn-primary" :disabled="submitting" @tap="handleLogin">
          {{ submitting ? '登录中...' : '使用微信一键登录' }}
        </button>
        <text class="helper">如果登录失败，请确认小程序 AppID 与后端微信配置一致后再重试。</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import { wechatLogin } from '../../services/auth'
import { applyLoginResult, completeLogin } from '../../utils/auth'
import { showToast } from '../../utils/ui'
import { getWechatLoginCode } from '../../utils/wechat'

const submitting = ref(false)
const errorMessage = ref('')

const infoItems = [
  {
    title: '快速进入',
    description: '不需要单独注册账号，直接使用微信完成登录。',
  },
  {
    title: '首次引导',
    description: '第一次登录后会先进入资料页，补全后才能继续使用核心功能。',
  },
  {
    title: '自动回跳',
    description: '登录成功后会自动回到你原本想去的页面，不需要重复操作。',
  },
]

async function handleLogin() {
  errorMessage.value = ''
  submitting.value = true
  try {
    const code = await getWechatLoginCode()
    const response = await wechatLogin(code)
    applyLoginResult(response)
    showToast('登录成功', 'success')
    await completeLogin(response.user ?? null)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '微信登录失败，请稍后重试'
  } finally {
    submitting.value = false
  }
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

.login-form {
  gap: 16rpx;
}
</style>
