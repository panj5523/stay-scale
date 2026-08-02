<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { decideReviewTask, getReviewTasks } from '../api/managementReview'
import { clearAdminSession } from '../auth/session'
import type { ReviewStatus, ReviewTask } from '../types/managementReview'

type LoadState = 'loading' | 'success' | 'error'

const status = ref<ReviewStatus | 'all'>('pending')
const router = useRouter()
const loadState = ref<LoadState>('loading')
const tasks = ref<ReviewTask[]>([])
const total = ref(0)
const selected = ref<ReviewTask | null>(null)
const requestError = ref('')
const actionState = ref<'idle' | 'loading' | 'error'>('idle')
const decision = reactive({
  reviewerName: '项目管理员',
  reason: '',
  targetCanonicalPublicId: '',
})

const selectedPayload = computed(() => selected.value?.normalized_payload ?? {})
const selectedEvidence = computed(() => selected.value?.evidence ?? {})

async function loadTasks() {
  loadState.value = 'loading'
  requestError.value = ''
  try {
    const response = await getReviewTasks(status.value)
    tasks.value = response.items
    total.value = response.total
    if (selected.value && !tasks.value.some((item) => item.record_id === selected.value?.record_id)) {
      selected.value = null
    }
    loadState.value = 'success'
  } catch {
    tasks.value = []
    loadState.value = 'error'
    requestError.value = '审核队列暂时无法读取，请确认 FastAPI 和 MySQL 已启动。'
  }
}

function chooseTask(task: ReviewTask) {
  selected.value = task
  decision.reason = ''
  decision.targetCanonicalPublicId = task.candidate?.public_id ?? ''
  actionState.value = 'idle'
  requestError.value = ''
}

async function submitDecision(action: 'approve' | 'reject') {
  if (!selected.value) return
  if (decision.reviewerName.trim().length < 2 || decision.reason.trim().length < 3) {
    actionState.value = 'error'
    requestError.value = '请填写审核人，并输入至少 3 个字的审核原因。'
    return
  }
  if (action === 'approve' && !decision.targetCanonicalPublicId.trim()) {
    actionState.value = 'error'
    requestError.value = '通过审核前必须填写目标统一民宿 ID。'
    return
  }
  actionState.value = 'loading'
  requestError.value = ''
  try {
    await decideReviewTask(selected.value.record_id, {
      action,
      reviewerName: decision.reviewerName.trim(),
      reason: decision.reason.trim(),
      targetCanonicalPublicId:
        action === 'approve' ? decision.targetCanonicalPublicId.trim() : undefined,
    })
    selected.value = null
    await loadTasks()
    actionState.value = 'idle'
  } catch {
    actionState.value = 'error'
    requestError.value = '审核提交失败。该任务可能已处理，或目标统一民宿不存在。'
  }
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}

onMounted(loadTasks)

async function logout() {
  clearAdminSession()
  await router.replace('/management/login')
}
</script>

<template>
  <main class="review-page">
    <header class="review-header">
      <RouterLink class="brand" to="/"><span>S</span><strong>Stay Scale</strong></RouterLink>
      <div>
        <small>INTERNAL · DEVELOPMENT</small>
        <strong>数据审核台</strong>
      </div>
      <nav><RouterLink to="/management/dashboard">运营看板</RouterLink><RouterLink to="/">返回比价</RouterLink><button type="button" @click="logout">退出登录</button></nav>
    </header>

    <section class="review-hero">
      <div><p>13 · MANAGEMENT REVIEW</p><h1>让数据进入推荐前，<em>先经过人的判断。</em></h1></div>
      <aside><strong>{{ total }}</strong><span>当前筛选任务</span><small>每次决定均保存审计记录</small></aside>
    </section>

    <section class="review-workspace">
      <aside class="queue-panel">
        <div class="queue-heading">
          <div><span>REVIEW QUEUE</span><h2>待审核导入记录</h2></div>
          <select v-model="status" @change="loadTasks">
            <option value="pending">待处理</option>
            <option value="approved">已通过</option>
            <option value="rejected">已驳回</option>
            <option value="all">全部</option>
          </select>
        </div>

        <div v-if="loadState === 'loading'" class="queue-state">正在读取匹配证据…</div>
        <div v-else-if="loadState === 'error'" class="queue-state error">{{ requestError }}</div>
        <div v-else-if="!tasks.length" class="queue-state">当前没有符合条件的审核任务。</div>
        <template v-else>
          <button
            v-for="task in tasks"
            :key="task.record_id"
            type="button"
            class="task-card"
            :class="{ active: selected?.record_id === task.record_id }"
            @click="chooseTask(task)"
          >
            <span>{{ task.platform_code }} · #{{ task.record_id }}</span>
            <strong>{{ task.listing_name }}</strong>
            <small>匹配度 {{ Number(task.match_score) * 100 }}% · {{ task.review_status }}</small>
          </button>
        </template>
      </aside>

      <section v-if="selected" class="evidence-panel">
        <div class="evidence-heading">
          <div><span>NORMALIZED RECORD</span><h2>{{ selected.listing_name }}</h2></div>
          <strong>{{ (Number(selected.match_score) * 100).toFixed(1) }}%</strong>
        </div>

        <div class="evidence-grid">
          <article><span>平台与外部 ID</span><strong>{{ selected.platform_code }} · {{ selected.external_id }}</strong></article>
          <article><span>城市 / 区域</span><strong>{{ formatValue(selectedPayload.city) }} · {{ formatValue(selectedPayload.district) }}</strong></article>
          <article class="wide"><span>归一化地址</span><strong>{{ formatValue(selectedPayload.address) }}</strong></article>
        </div>

        <div class="candidate-card">
          <span>建议关联的统一民宿</span>
          <template v-if="selected.candidate">
            <strong>{{ selected.candidate.name }}</strong>
            <p>{{ selected.candidate.public_id }} · {{ selected.candidate.city }} {{ selected.candidate.district }}</p>
            <small>{{ selected.candidate.address }}</small>
          </template>
          <p v-else>当前没有候选统一民宿，需要驳回或后续增加“创建新民宿”流程。</p>
        </div>

        <details>
          <summary>查看完整匹配证据</summary>
          <pre>{{ JSON.stringify(selectedEvidence, null, 2) }}</pre>
        </details>

        <form v-if="selected.review_status === 'pending'" class="decision-form" @submit.prevent>
          <label><span>审核人</span><input v-model="decision.reviewerName" maxlength="80" /></label>
          <label><span>目标统一民宿 ID</span><input v-model="decision.targetCanonicalPublicId" maxlength="32" placeholder="例如 DL_000001" /></label>
          <label class="wide"><span>审核原因</span><textarea v-model="decision.reason" maxlength="500" rows="3" placeholder="说明通过或驳回的依据"></textarea></label>
          <p v-if="actionState === 'error'" role="alert">{{ requestError }}</p>
          <div class="decision-actions">
            <button type="button" class="reject" :disabled="actionState === 'loading'" @click="submitDecision('reject')">驳回记录</button>
            <button type="button" class="approve" :disabled="actionState === 'loading'" @click="submitDecision('approve')">通过并关联</button>
          </div>
        </form>
        <div v-else class="decided-note">该任务已完成审核，当前状态：{{ selected.review_status }}</div>
      </section>

      <section v-else class="evidence-empty"><span>SELECT A RECORD</span><h2>选择一条任务查看证据</h2><p>通过不会修改统一民宿本身，只建立平台房源关联；驳回后该房源不会进入比价和推荐。</p></section>
    </section>
  </main>
</template>

<style scoped>
.review-page { min-height: 100vh; padding-bottom: 60px; background: radial-gradient(circle at 85% 0, rgb(216 107 61 / 12%), transparent 30%), linear-gradient(120deg, #f1eee5, #faf7f0 55%, #e8efe9); }
.review-header, .review-hero, .review-workspace { width: min(1320px, calc(100% - 48px)); margin-inline: auto; }
.review-header { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; padding: 22px 0; border-bottom: 1px solid var(--color-border); }
.brand { display: flex; gap: 10px; align-items: center; color: var(--color-primary-deep); text-decoration: none; }
.brand span { display: grid; width: 34px; height: 34px; color: white; font-family: Georgia, serif; background: var(--color-primary); border-radius: 50%; place-items: center; }
.review-header > div { display: flex; flex-direction: column; text-align: center; }
.review-header small { color: var(--color-accent); font-size: .55rem; letter-spacing: .15em; }
.review-header nav { display: flex; gap: 18px; justify-content: flex-end; }
.review-header nav a, .review-header nav button { padding: 0; color: var(--color-muted); font-size: .72rem; text-decoration: none; background: transparent; border: 0; }
.review-hero { display: grid; grid-template-columns: 1fr 230px; gap: 60px; align-items: end; padding: 70px 0 52px; }
.review-hero p, .queue-heading span, .evidence-heading span { color: var(--color-accent); font-size: .65rem; font-weight: 900; letter-spacing: .16em; }
.review-hero h1 { max-width: 830px; margin: 12px 0 0; color: var(--color-primary-deep); font-family: 'Noto Serif SC', serif; font-size: clamp(2.5rem, 5vw, 4.8rem); font-weight: 500; line-height: 1.1; }
.review-hero em { color: var(--color-accent); font-style: normal; }
.review-hero aside { display: flex; flex-direction: column; padding: 24px; background: rgb(255 252 246 / 72%); border: 1px solid var(--color-border); border-radius: 16px; }
.review-hero aside strong { color: var(--color-primary); font-family: Georgia, serif; font-size: 3rem; }
.review-hero aside span { color: var(--color-primary-deep); font-weight: 800; }
.review-hero aside small { margin-top: 6px; color: var(--color-muted); }
.review-workspace { display: grid; grid-template-columns: 390px minmax(0, 1fr); min-height: 650px; overflow: hidden; background: rgb(255 252 246 / 86%); border: 1px solid var(--color-border); border-radius: 22px; box-shadow: 0 28px 70px rgb(31 58 51 / 11%); }
.queue-panel { padding: 25px; background: rgb(36 90 80 / 5%); border-right: 1px solid var(--color-border); }
.queue-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 15px; padding-bottom: 18px; }
.queue-heading h2, .evidence-heading h2, .evidence-empty h2 { margin: 6px 0 0; color: var(--color-primary-deep); font-family: 'Noto Serif SC', serif; font-size: 1.25rem; }
.queue-heading select { padding: 8px; color: var(--color-primary-deep); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 8px; }
.task-card { display: flex; width: 100%; padding: 15px; margin-top: 9px; text-align: left; flex-direction: column; background: var(--color-surface); border: 1px solid transparent; border-radius: 12px; }
.task-card.active { border-color: var(--color-accent); box-shadow: 0 8px 24px rgb(31 58 51 / 8%); }
.task-card span { color: var(--color-accent); font-size: .6rem; font-weight: 800; text-transform: uppercase; }
.task-card strong { margin-top: 6px; color: var(--color-primary-deep); }
.task-card small { margin-top: 5px; color: var(--color-muted); }
.queue-state { padding: 45px 16px; color: var(--color-muted); text-align: center; }
.queue-state.error { color: var(--color-danger); }
.evidence-panel { padding: 34px; }
.evidence-heading { display: flex; align-items: flex-end; justify-content: space-between; padding-bottom: 24px; border-bottom: 1px solid var(--color-border); }
.evidence-heading > strong { color: var(--color-primary); font-family: Georgia, serif; font-size: 2.3rem; }
.evidence-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 22px; }
.evidence-grid article { display: flex; padding: 13px; flex-direction: column; background: rgb(36 90 80 / 5%); border-radius: 9px; }
.evidence-grid .wide { grid-column: 1 / -1; }
.evidence-grid span, .candidate-card > span, .decision-form span { color: var(--color-muted); font-size: .62rem; }
.evidence-grid strong { margin-top: 5px; color: var(--color-primary-deep); font-size: .78rem; }
.candidate-card { padding: 18px; margin-top: 16px; background: rgb(216 107 61 / 7%); border: 1px solid rgb(216 107 61 / 20%); border-radius: 12px; }
.candidate-card strong { display: block; margin-top: 8px; color: var(--color-primary-deep); }
.candidate-card p, .candidate-card small { margin: 5px 0 0; color: var(--color-muted); font-size: .72rem; }
details { margin-top: 16px; color: var(--color-muted); font-size: .72rem; }
pre { max-height: 220px; padding: 14px; overflow: auto; white-space: pre-wrap; background: #213b35; color: #e7eee9; border-radius: 9px; }
.decision-form { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; padding-top: 22px; margin-top: 22px; border-top: 1px solid var(--color-border); }
.decision-form label { display: flex; flex-direction: column; gap: 7px; }
.decision-form .wide, .decision-form > p, .decision-actions { grid-column: 1 / -1; }
.decision-form input, .decision-form textarea { padding: 11px 12px; color: var(--color-primary-deep); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 8px; outline: 0; }
.decision-form > p { margin: 0; color: var(--color-danger); font-size: .7rem; }
.decision-actions { display: flex; gap: 10px; justify-content: flex-end; }
.decision-actions button { padding: 11px 16px; font-weight: 800; border-radius: 8px; }
.reject { color: var(--color-danger); background: transparent; border: 1px solid currentColor; }
.approve { color: white; background: var(--color-primary); border: 1px solid var(--color-primary); }
.decided-note { padding: 16px; margin-top: 22px; color: var(--color-muted); background: rgb(36 90 80 / 5%); border-radius: 9px; }
.evidence-empty { display: grid; text-align: center; place-content: center; }
.evidence-empty > span { color: var(--color-accent); font-size: .62rem; font-weight: 900; letter-spacing: .16em; }
.evidence-empty p { max-width: 470px; color: var(--color-muted); line-height: 1.7; }
@media (max-width: 850px) { .review-header { grid-template-columns: 1fr auto; } .review-header > div { display: none; } .review-hero { grid-template-columns: 1fr; } .review-hero aside { display: none; } .review-workspace { grid-template-columns: 1fr; } .queue-panel { border-right: 0; border-bottom: 1px solid var(--color-border); } .evidence-panel { padding: 24px 18px; } }
@media (max-width: 560px) { .review-header, .review-hero, .review-workspace { width: min(100% - 24px, 520px); } .review-header nav a:first-child { display: none; } .review-hero { padding-top: 50px; } .review-hero h1 { font-size: 2.7rem; } .evidence-grid, .decision-form { grid-template-columns: 1fr; } .decision-form label, .decision-form .wide { grid-column: 1; } }
</style>
