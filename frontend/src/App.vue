<template>
  <RouterView />
  <AdminContextSwitch />
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import AdminContextSwitch from './components/AdminContextSwitch.vue'
</script>
