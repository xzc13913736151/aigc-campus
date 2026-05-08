<template>
  <view />
</template>

<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'

import { bootstrapAuth } from './utils/auth'

onLaunch(() => {
  void bootstrapAuth()
})
</script>

<style lang="scss">
@use './styles/app.scss';
</style>
