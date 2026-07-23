<template>
  <button
    class="like-button"
    :class="{ liked, compact, busy }"
    :disabled="busy"
    :aria-label="liked ? `取消点赞，当前 ${count} 个赞` : `点赞，当前 ${count} 个赞`"
    @tap.stop="emit('toggle')"
  >
    <text class="heart" aria-hidden="true">{{ liked ? '♥' : '♡' }}</text>
    <text class="count">{{ count }}</text>
  </button>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    liked: boolean
    count: number
    busy?: boolean
    compact?: boolean
  }>(),
  {
    busy: false,
    compact: false,
  },
)

const emit = defineEmits<{
  toggle: []
}>()
</script>

<style scoped lang="scss">
@use '../styles/tokens' as t;

.like-button {
  min-width: 116rpx;
  height: 76rpx;
  min-height: 76rpx;
  padding: 0 22rpx;
  margin: 0;
  border: 1rpx solid t.$color-line;
  border-radius: 20rpx;
  background: t.$color-surface;
  color: t.$color-ink-secondary;
  box-shadow: inset 0 1rpx 0 rgba(255, 255, 255, 0.8), 0 5rpx 14rpx rgba(67, 50, 38, 0.06);
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 10rpx;
  transition: transform t.$motion-fast ease, border-color t.$motion-fast ease, background-color t.$motion-fast ease;
}

.like-button:active {
  transform: translateY(2rpx) scale(0.98);
}

.like-button.liked {
  border-color: rgba(183, 83, 71, 0.24);
  background: rgba(183, 83, 71, 0.08);
}

.heart {
  color: t.$color-ink-muted;
  font-size: 38rpx;
  font-weight: 500;
  line-height: 1;
}

.liked .heart {
  color: t.$color-danger;
}

.count {
  min-width: 20rpx;
  color: t.$color-ink-secondary;
  font-size: 24rpx;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  text-align: left;
}

.liked .count {
  color: t.$color-danger;
}

.like-button.compact {
  min-width: 88rpx;
  height: 60rpx;
  min-height: 60rpx;
  padding: 0 16rpx;
  border-radius: 16rpx;
}

.compact .heart {
  font-size: 31rpx;
}

.compact .count {
  font-size: 22rpx;
}
</style>
