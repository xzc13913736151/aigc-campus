<template>
  <view class="container">
    <view class="section hero">
      <text class="eyebrow">CampusClaw 登录</text>
      <view style="height: 18rpx" />
      <text class="title">快速进入 CampusClaw，开始校园探索。</text>
      <view style="height: 18rpx" />
      <text class="subtitle">
        支持邮箱密码登录。App 演示版可直接使用演示账号进入核心功能。
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
        <!-- #ifdef MP-WEIXIN -->
        <button class="btn btn-primary" :disabled="submitting" @tap="handleLogin">
          {{ submitting ? '登录中...' : '使用微信一键登录' }}
        </button>
        <text class="helper">如果登录失败，请确认小程序 AppID 与后端微信配置一致后再重试。</text>
        <!-- #endif -->
        <!-- #ifndef MP-WEIXIN -->
        <button v-if="enablePasswordLogin" class="btn btn-primary" :disabled="submitting" @tap="handleDemoLogin">
          {{ submitting ? '登录中...' : '一键进入演示账号' }}
        </button>
        <text v-if="enablePasswordLogin" class="helper">App 演示版使用内置演示账号，不依赖微信登录。</text>
        <!-- #endif -->
        <view v-if="enablePasswordLogin" class="divider">
          <view class="divider-line" />
          <text>邮箱密码登录</text>
          <view class="divider-line" />
        </view>
        <input
          v-if="enablePasswordLogin"
          v-model="email"
          class="input"
          type="text"
          placeholder="邮箱"
          :disabled="submitting"
        />
        <input
          v-if="enablePasswordLogin"
          v-model="password"
          class="input"
          type="password"
          placeholder="密码"
          :disabled="submitting"
          @confirm="handlePasswordLogin"
        />
        <button v-if="enablePasswordLogin" class="btn btn-secondary" :disabled="submitting || !canPasswordLogin" @tap="handlePasswordLogin">
          {{ submitting ? '登录中...' : '邮箱密码登录' }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

import { ENABLE_PASSWORD_LOGIN } from '../../constants'
import { passwordLogin, wechatLogin } from '../../services/auth'
import { applyLoginResult, completeLogin } from '../../utils/auth'
import { showToast } from '../../utils/ui'
import { getWechatLoginCode } from '../../utils/wechat'

const submitting = ref(false)
const errorMessage = ref('')
const email = ref('')
const password = ref('')
const enablePasswordLogin = ENABLE_PASSWORD_LOGIN
const canPasswordLogin = computed(() => Boolean(email.value.trim() && password.value))
const DEMO_EMAIL = 'demo_frontend@campusclaw.local'
const DEMO_PASSWORD = 'demo123456'

const infoItems = [
  {
    title: '快速进入',
    description: 'App 演示版可使用演示账号快速进入，也支持邮箱密码登录。',
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

async function loginWithPassword(normalizedEmail: string, rawPassword: string) {
  const response = await passwordLogin({
    email: normalizedEmail,
    password: rawPassword,
  })
  applyLoginResult(response)
  showToast('登录成功', 'success')
  await completeLogin(response.user ?? null)
}

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

async function handlePasswordLogin() {
  errorMessage.value = ''
  const normalizedEmail = email.value.trim()
  if (!normalizedEmail || !password.value) {
    errorMessage.value = '请输入邮箱和密码'
    return
  }

  submitting.value = true
  try {
    await loginWithPassword(normalizedEmail, password.value)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '邮箱密码登录失败'
  } finally {
    submitting.value = false
  }
}

async function handleDemoLogin() {
  errorMessage.value = ''
  submitting.value = true
  try {
    email.value = DEMO_EMAIL
    password.value = DEMO_PASSWORD
    await loginWithPassword(DEMO_EMAIL, DEMO_PASSWORD)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '演示账号登录失败，请确认后端已运行并已导入演示数据'
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

.divider {
  display: flex;
  align-items: center;
  gap: 16rpx;
  color: #8a929c;
  font-size: 22rpx;
}

.divider-line {
  flex: 1;
  height: 1rpx;
  background: rgba(16, 33, 51, 0.1);
}
</style>
