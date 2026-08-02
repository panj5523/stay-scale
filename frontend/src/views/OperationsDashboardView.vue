<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getDataRetentionReport, getOperationsDashboard } from '../api/operations'
import { clearAdminSession } from '../auth/session'
import type { DataRetentionReport, OperationsDashboard } from '../types/operations'

const router = useRouter()
const dashboard = ref<OperationsDashboard | null>(null)
const retention = ref<DataRetentionReport | null>(null)
const loading = ref(true)
const error = ref('')

async function loadDashboard() {
  loading.value = true
  error.value = ''
  try {
    dashboard.value = await getOperationsDashboard()
    try {
      retention.value = await getDataRetentionReport()
    } catch {
      // Keep the operational dashboard usable when the optional retention report is unavailable.
      retention.value = null
    }
  } catch {
    error.value = '看板数据暂时无法读取，请确认管理员登录状态和后端服务。'
  } finally {
    loading.value = false
  }
}

async function logout() {
  clearAdminSession()
  await router.replace('/management/login')
}

function coverageWidth(count: number): string {
  const max = Math.max(...(dashboard.value?.listing_quality.platform_coverage.map((item) => item.active_listing_count) ?? [1]))
  return `${Math.round((count / Math.max(max, 1)) * 100)}%`
}

onMounted(loadDashboard)
</script>

<template>
  <main class="dashboard-page">
    <header class="dashboard-header">
      <RouterLink class="brand" to="/"><span>S</span><strong>Stay Scale</strong></RouterLink>
      <nav><RouterLink to="/management/reviews">审核队列</RouterLink><button type="button" @click="logout">退出登录</button></nav>
    </header>

    <section class="dashboard-hero">
      <div><p>16 · OPERATIONS PULSE</p><h1>把数据健康度，<em>放在每天的视线里。</em></h1><span>只读统计 · 最近 24 小时导入 · 全部 AI 审计</span></div>
      <button type="button" :disabled="loading" @click="loadDashboard">{{ loading ? '读取中…' : '刷新看板 ↗' }}</button>
    </section>

    <div v-if="error" class="dashboard-error" role="alert">{{ error }}</div>
    <section v-else-if="dashboard" class="dashboard-content">
      <div class="metric-grid">
        <article><span>待审核记录</span><strong>{{ dashboard.review_queue.pending }}</strong><small>通过 {{ dashboard.review_queue.approved }} · 驳回 {{ dashboard.review_queue.rejected }}</small></article>
        <article><span>24H 导入批次</span><strong>{{ dashboard.ingestion.batches_24h }}</strong><small>成功 {{ dashboard.ingestion.completed_batches_24h }} · 异常 {{ dashboard.ingestion.failed_batches_24h }}</small></article>
        <article><span>可推荐统一民宿</span><strong>{{ dashboard.listing_quality.active_canonical_listings }}</strong><small>{{ dashboard.listing_quality.active_platform_listings }} 个平台房源处于 active</small></article>
        <article><span>AI Token 用量</span><strong>{{ dashboard.ai_usage.total_tokens.toLocaleString() }}</strong><small>自然解析、推荐说明、行程和评论</small></article>
      </div>

      <div class="dashboard-columns">
        <section class="panel"><header><div><span>PLATFORM COVERAGE</span><h2>平台覆盖</h2></div><small>活跃平台房源数</small></header><div class="coverage-list"><div v-for="item in dashboard.listing_quality.platform_coverage" :key="item.platform_code"><div><strong>{{ item.platform_name }}</strong><small>{{ item.active_listing_count }}</small></div><i><b :style="{ width: coverageWidth(item.active_listing_count) }"></b></i></div></div></section>
        <section class="panel"><header><div><span>AI USAGE BREAKDOWN</span><h2>AI 调用分布</h2></div><small>已保存的审计统计</small></header><div class="usage-list"><div><span>自然语言解析</span><strong>{{ dashboard.ai_usage.preference_parse_count }}</strong></div><div><span>推荐说明</span><strong>{{ dashboard.ai_usage.recommendation_explanation_count }}</strong></div><div><span>旅行计划</span><strong>{{ dashboard.ai_usage.travel_plan_count }}</strong></div><div><span>评论分析</span><strong>{{ dashboard.ai_usage.review_analysis_count }}</strong></div></div></section>
      </div>

      <section class="warning-panel"><span>DATA QUALITY SIGNALS</span><h2>需要关注的事项</h2><p v-if="!dashboard.warnings.length">当前没有待处理警告，数据状态平稳。</p><ul v-else><li v-for="warning in dashboard.warnings" :key="warning">{{ warning }}</li></ul></section>
      <section v-if="retention" class="warning-panel retention-panel"><span>DATA RETENTION</span><h2>数据保留提醒</h2><p>达到期限待归档：<strong>{{ retention.total_eligible_count }}</strong> 条。此报告只读，不会删除数据。</p><ul><li v-for="item in retention.categories.filter((category) => category.eligible_count > 0)" :key="item.key">{{ item.label }}：{{ item.eligible_count }} 条，截止 {{ item.cutoff_date }}</li><li v-if="!retention.total_eligible_count">当前没有达到保留期限的数据。</li></ul></section>
      <p class="dashboard-note">统计生成于 {{ new Date(dashboard.generated_at).toLocaleString('zh-CN') }} · 看板只读，不会修改业务数据。</p>
    </section>
  </main>
</template>

<style scoped>
.dashboard-page { min-height: 100vh; padding-bottom: 70px; background: radial-gradient(circle at 80% 0, rgb(36 90 80 / 14%), transparent 32%), linear-gradient(120deg, #f4f0e7, #fbf8f0 56%, #e8efe9); }
.dashboard-header, .dashboard-hero, .dashboard-content { width: min(1240px, calc(100% - 48px)); margin-inline: auto; }
.dashboard-header { display: flex; align-items: center; justify-content: space-between; padding: 23px 0; border-bottom: 1px solid var(--color-border); }
.brand { display: flex; gap: 10px; align-items: center; color: var(--color-primary-deep); text-decoration: none; }
.brand span { display: grid; width: 34px; height: 34px; color: white; font-family: Georgia, serif; background: var(--color-primary); border-radius: 50%; place-items: center; }
.dashboard-header nav { display: flex; gap: 18px; align-items: center; }
.dashboard-header nav a, .dashboard-header nav button { color: var(--color-muted); font-size: .72rem; text-decoration: none; background: transparent; border: 0; }
.dashboard-hero { display: flex; align-items: flex-end; justify-content: space-between; gap: 25px; padding: 70px 0 45px; }
.dashboard-hero p, .panel header span, .warning-panel > span { margin: 0; color: var(--color-accent); font-size: .63rem; font-weight: 900; letter-spacing: .16em; }
.dashboard-hero h1 { max-width: 800px; margin: 12px 0; color: var(--color-primary-deep); font-family: 'Noto Serif SC', serif; font-size: clamp(2.6rem, 5vw, 4.6rem); font-weight: 500; line-height: 1.1; }
.dashboard-hero em { color: var(--color-accent); font-style: normal; }
.dashboard-hero span { color: var(--color-muted); font-size: .75rem; }
.dashboard-hero button { padding: 13px 17px; color: white; font-weight: 800; background: var(--color-primary); border: 0; border-radius: 9px; }
.dashboard-hero button:disabled { opacity: .6; }
.dashboard-error { width: min(1240px, calc(100% - 48px)); padding: 20px; margin: 0 auto; color: var(--color-danger); background: rgb(170 70 58 / 8%); border-radius: 10px; }
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.metric-grid article, .panel, .warning-panel { padding: 23px; background: rgb(255 252 246 / 86%); border: 1px solid var(--color-border); border-radius: 16px; box-shadow: 0 14px 38px rgb(31 58 51 / 5%); }
.metric-grid span { color: var(--color-muted); font-size: .68rem; }
.metric-grid strong { display: block; margin-top: 10px; color: var(--color-primary); font-family: Georgia, serif; font-size: 2.8rem; font-weight: 400; }
.metric-grid small { display: block; margin-top: 5px; color: var(--color-muted); font-size: .65rem; }
.dashboard-columns { display: grid; grid-template-columns: 1.2fr 1fr; gap: 12px; margin-top: 12px; }
.panel header { display: flex; align-items: flex-end; justify-content: space-between; padding-bottom: 18px; border-bottom: 1px solid var(--color-border); }
.panel h2, .warning-panel h2 { margin: 6px 0 0; color: var(--color-primary-deep); font-family: 'Noto Serif SC', serif; font-size: 1.35rem; }
.panel header small { color: var(--color-muted); font-size: .65rem; }
.coverage-list { display: grid; gap: 17px; padding-top: 22px; }
.coverage-list > div > div { display: flex; justify-content: space-between; color: var(--color-primary-deep); font-size: .75rem; }
.coverage-list small { color: var(--color-muted); }
.coverage-list i { display: block; height: 6px; margin-top: 7px; overflow: hidden; background: rgb(36 90 80 / 10%); border-radius: 8px; }
.coverage-list b { display: block; height: 100%; background: var(--color-accent); border-radius: inherit; }
.usage-list { display: grid; gap: 14px; padding-top: 22px; }
.usage-list div { display: flex; align-items: center; justify-content: space-between; padding-bottom: 10px; border-bottom: 1px dashed var(--color-border); }
.usage-list span { color: var(--color-muted); font-size: .75rem; }
.usage-list strong { color: var(--color-primary); font-family: Georgia, serif; font-size: 1.25rem; }
.warning-panel { margin-top: 12px; }
.warning-panel p, .warning-panel li { color: var(--color-muted); font-size: .76rem; line-height: 1.7; }
.warning-panel ul { padding-left: 18px; margin-bottom: 0; }
.dashboard-note { color: var(--color-muted); font-size: .64rem; text-align: right; }
@media (max-width: 900px) { .metric-grid { grid-template-columns: repeat(2, 1fr); } .dashboard-columns { grid-template-columns: 1fr; } }
@media (max-width: 560px) { .dashboard-header, .dashboard-hero, .dashboard-content, .dashboard-error { width: min(100% - 24px, 520px); } .dashboard-hero { align-items: flex-start; flex-direction: column; padding-top: 50px; } .dashboard-hero button { width: 100%; } .metric-grid { grid-template-columns: 1fr 1fr; gap: 8px; } .metric-grid article { padding: 16px 12px; } .metric-grid strong { font-size: 2.2rem; } }
</style>
