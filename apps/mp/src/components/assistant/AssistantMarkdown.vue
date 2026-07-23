<template>
  <view class="markdown">
    <view v-for="(block, index) in blocks" :key="`${index}-${block.text}`" class="markdown-block" :class="`is-${block.type}`">
      <text v-if="block.type === 'bullet'" class="marker">•</text>
      <text v-else-if="block.type === 'ordered'" class="marker">{{ block.marker }}</text>
      <text v-else-if="block.type === 'quote'" class="marker">“</text>
      <text class="markdown-text">{{ block.text }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ content: string }>()

type MarkdownBlock = {
  type: 'heading' | 'paragraph' | 'bullet' | 'ordered' | 'quote'
  text: string
  marker?: string
}

const blocks = computed<MarkdownBlock[]>(() =>
  String(props.content || '')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      if (/^#{1,3}\s+/.test(line)) {
        return { type: 'heading', text: line.replace(/^#{1,3}\s+/, '') }
      }
      if (/^[-*]\s+/.test(line)) {
        return { type: 'bullet', text: line.replace(/^[-*]\s+/, '') }
      }
      const ordered = line.match(/^(\d+)[.)]\s+(.*)$/)
      if (ordered) {
        return { type: 'ordered', marker: `${ordered[1]}.`, text: ordered[2] }
      }
      if (/^>\s?/.test(line)) {
        return { type: 'quote', text: line.replace(/^>\s?/, '') }
      }
      return { type: 'paragraph', text: line }
    }),
)
</script>

<style scoped lang="scss">
@use '../../styles/tokens' as t;

.markdown {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.markdown-block {
  display: flex;
  align-items: flex-start;
  gap: 10rpx;
}

.markdown-text {
  flex: 1;
  min-width: 0;
  color: t.$color-ink;
  font-size: 26rpx;
  line-height: 1.72;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.is-heading .markdown-text {
  margin-top: 6rpx;
  font-size: 29rpx;
  font-weight: 650;
  line-height: 1.45;
}

.is-quote {
  padding: 12rpx 16rpx;
  border-left: 4rpx solid t.$color-ai;
  background: t.$color-input;
}

.marker {
  flex: 0 0 28rpx;
  color: t.$color-ai;
  font-size: 24rpx;
  font-weight: 650;
  line-height: 1.72;
  text-align: right;
}
</style>
