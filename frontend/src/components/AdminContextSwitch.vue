<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ADMIN_SESSION_EVENT, hasAdminSession } from '../auth/session'

const route = useRoute()
const signedIn = ref(hasAdminSession())
const isManagementPage = computed(() => route.path.startsWith('/management'))
const visible = computed(() => signedIn.value && route.name !== 'admin-login')

function refreshSession() { signedIn.value = hasAdminSession() }
onMounted(() => window.addEventListener(ADMIN_SESSION_EVENT, refreshSession))
onBeforeUnmount(() => window.removeEventListener(ADMIN_SESSION_EVENT, refreshSession))
</script>

<template>
  <RouterLink
    v-if="visible"
    class="admin-context-switch"
    :class="{ 'on-management': isManagementPage }"
    :to="isManagementPage ? '/' : '/management/dashboard'"
  >
    <span>{{ isManagementPage ? 'USER VIEW' : 'ADMIN' }}</span>
    {{ isManagementPage ? '访问用户端' : '返回管理后台' }}
  </RouterLink>
</template>

<style scoped>
.admin-context-switch{position:fixed;right:22px;bottom:22px;z-index:1000;display:grid;gap:2px;min-width:112px;padding:11px 15px;color:#fff;text-decoration:none;background:#b45f35;border:1px solid rgb(255 255 255 / 28%);border-radius:10px;box-shadow:0 12px 34px rgb(23 59 52 / 24%);font-size:.78rem;font-weight:800;text-align:left}.admin-context-switch span{font-size:.52rem;letter-spacing:.15em;opacity:.72}.admin-context-switch.on-management{background:#245a50}@media(max-width:600px){.admin-context-switch{right:14px;bottom:14px;min-width:auto;padding:9px 12px;font-size:.7rem}}
</style>
