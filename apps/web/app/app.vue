<template>
  <div class="app-shell" :data-test="shellTestId">
    <NuxtRouteAnnouncer />
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
const shellTestId = 'app-shell';
</script>
