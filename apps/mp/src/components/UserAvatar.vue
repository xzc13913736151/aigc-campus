<template>
  <view
    class="user-avatar"
    :class="[`size-${size}`, { fallback: !avatarUrl }]"
    :style="avatarStyle"
  >
    <CachedImage v-if="avatarUrl" :src="avatarUrl" mode="aspectFill" />
    <text v-else class="avatar-initial">{{ initial }}</text>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import CachedImage from './CachedImage.vue'
import { isAuthenticated } from '../utils/auth'
import { getCachedAvatar, resolveProfileAvatar } from '../utils/profileAvatar'

const props = withDefaults(
  defineProps<{
    userId?: string
    name?: string
    src?: string
    size?: 'small' | 'medium' | 'large'
  }>(),
  {
    userId: '',
    name: '',
    src: '',
    size: 'medium',
  },
)

const resolvedAvatar = ref('')
const avatarUrl = computed(() => props.src || resolvedAvatar.value)
const initial = computed(() => props.name.trim().slice(0, 1) || '同')
const avatarStyle = computed(() => {
  const sizes = {
    small: '52rpx',
    medium: '68rpx',
    large: '88rpx',
  }
  const radius = props.size === 'small' ? '16rpx' : props.size === 'large' ? '24rpx' : '20rpx'
  return {
    width: sizes[props.size],
    height: sizes[props.size],
    minWidth: sizes[props.size],
    minHeight: sizes[props.size],
    flex: `0 0 ${sizes[props.size]}`,
    overflow: 'hidden',
    borderRadius: radius,
    backgroundColor: '#f1ece2',
    border: '1rpx solid #ded6c9',
  }
})

watch(
  [() => props.userId, () => props.src, () => isAuthenticated.value],
  async ([userId, src, authenticated]) => {
    resolvedAvatar.value = src || getCachedAvatar(userId)
    if (src || !userId || !authenticated) {
      return
    }
    try {
      resolvedAvatar.value = await resolveProfileAvatar(userId)
    } catch {
      resolvedAvatar.value = ''
    }
  },
  { immediate: true },
)
</script>

<style scoped lang="scss">
@use '../styles/tokens' as t;

.user-avatar {
  flex-shrink: 0;
  overflow: hidden;
  border: 1rpx solid t.$color-line;
  border-radius: 20rpx;
  background: t.$color-input;
  box-shadow: 0 4rpx 12rpx rgba(67, 50, 38, 0.07);
}

.user-avatar.fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  color: t.$color-brand-deep;
}

.size-small {
  width: 52rpx;
  height: 52rpx;
  border-radius: 16rpx;
}

.size-medium {
  width: 68rpx;
  height: 68rpx;
}

.size-large {
  width: 88rpx;
  height: 88rpx;
  border-radius: 24rpx;
}

.avatar-initial {
  font-size: 26rpx;
  font-weight: 650;
  line-height: 1;
}

.size-small .avatar-initial {
  font-size: 21rpx;
}

.size-large .avatar-initial {
  font-size: 32rpx;
}
</style>
