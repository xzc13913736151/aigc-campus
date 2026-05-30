<template>
  <view class="cached-image-root" @tap="$emit('tap')">
    <image
      class="cached-image-inner"
      :src="displaySrc"
      :mode="mode"
      @error="handleError"
    />
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { getMediaUrl } from '../utils/media'

const props = withDefaults(
  defineProps<{
    src?: string
    mode?: string
  }>(),
  {
    src: '',
    mode: 'aspectFill',
  },
)

defineEmits<{
  (event: 'tap'): void
}>()

const localSrc = ref('')
const failed = ref(false)

const remoteSrc = computed(() => getMediaUrl(props.src))
const displaySrc = computed(() => localSrc.value || remoteSrc.value)

watch(
  remoteSrc,
  (url) => {
    localSrc.value = ''
    failed.value = false
    void cacheImage(url)
  },
  { immediate: true },
)

async function cacheImage(url: string) {
  if (!url || !/^https?:\/\//i.test(url)) {
    return
  }

  try {
    const result = await uni.downloadFile({ url })
    if (result.statusCode && result.statusCode >= 200 && result.statusCode < 300 && result.tempFilePath) {
      localSrc.value = result.tempFilePath
    }
  } catch (error) {
    console.warn('media image download failed', url, error)
  }
}

function handleError() {
  failed.value = true
  console.warn('media image render failed', displaySrc.value)
}
</script>

<style scoped>
.cached-image-root,
.cached-image-inner {
  width: 100%;
  height: 100%;
  display: block;
}

.cached-image-root {
  overflow: hidden;
}
</style>
