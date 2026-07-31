<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getReadiness } from '../api/health'
import type { ReadinessResponse } from '../types/health'

type LoadState = 'loading' | 'success' | 'error'

const loadState = ref<LoadState>('loading')
const health = ref<ReadinessResponse | null>(null)
const errorMessage = ref('')

const services = computed(() => [
  {
    name: 'Vue 3 前端',
    detail: 'Vite 开发服务器',
    status: 'up' as const,
  },
  {
    name: 'MySQL 8.0',
    detail: health.value?.checks.database.message ?? '等待后端检查',
    status: health.value?.checks.database.status ?? 'down',
  },
  {
    name: 'Redis',
    detail: health.value?.checks.redis.message ?? '等待后端检查',
    status: health.value?.checks.redis.status ?? 'down',
  },
])

async function loadHealth() {
  loadState.value = 'loading'
  errorMessage.value = ''

  try {
    health.value = await getReadiness()
    loadState.value = 'success'
  } catch {
    health.value = null
    loadState.value = 'error'
    errorMessage.value = '无法连接 FastAPI，请确认后端已在 8000 端口启动。'
  }
}

onMounted(loadHealth)
</script>

<template>
  <main class="status-page">
    <div class="route-line" aria-hidden="true"></div>

    <header class="brand-bar">
      <a class="brand" href="/" aria-label="Stay Scale 首页">
        <span class="brand-mark">S</span>
        <span>Stay Scale</span>
      </a>
      <span class="stage-badge">M0 · 工程骨架</span>
    </header>

    <section class="hero">
      <p class="eyebrow">民宿智能推荐与旅行规划平台</p>
      <h1>旅程还未出发，<br />基础服务已经就位。</h1>
      <p class="intro">
        这是项目的运行环境检查页。当前模块只验证前端、后端、MySQL 与 Redis 的连接，不包含任何模拟业务功能。
      </p>
    </section>

    <section class="status-panel" aria-labelledby="status-title">
      <div class="panel-heading">
        <div>
          <p class="panel-kicker">Environment check</p>
          <h2 id="status-title">运行状态</h2>
        </div>
        <button class="refresh-button" type="button" :disabled="loadState === 'loading'" @click="loadHealth">
          {{ loadState === 'loading' ? '检查中…' : '重新检查' }}
        </button>
      </div>

      <div v-if="loadState === 'error'" class="connection-error" role="alert">
        <span class="error-dot"></span>
        <div>
          <strong>FastAPI 未连接</strong>
          <p>{{ errorMessage }}</p>
        </div>
      </div>

      <div class="service-grid">
        <article v-for="service in services" :key="service.name" class="service-card">
          <div class="service-status" :class="`is-${service.status}`">
            <span></span>
            {{ service.status === 'up' ? '正常' : '未就绪' }}
          </div>
          <h3>{{ service.name }}</h3>
          <p>{{ service.detail }}</p>
        </article>
      </div>

      <footer class="panel-footer">
        <span>FastAPI {{ health?.version ?? '等待连接' }}</span>
        <span v-if="health">最近检查：{{ new Date(health.timestamp).toLocaleString('zh-CN') }}</span>
        <span v-else>API：/api/v1/health/ready</span>
      </footer>
    </section>

    <p class="next-step">下一站 · MySQL 数据模型与演示数据</p>
  </main>
</template>
