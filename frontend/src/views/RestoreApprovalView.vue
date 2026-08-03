<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { decideRestoreRequest, executeRestoreRequest, getRestoreExecutionReadiness, listRestoreRequests } from '../api/operations'
import type { RestoreRequest } from '../types/operations'

const requests = ref<RestoreRequest[]>([])
const loading = ref(true)
const message = ref('')

async function loadRequests() {
  loading.value = true
  message.value = ''
  try {
    requests.value = await listRestoreRequests()
  } catch {
    message.value = '恢复申请暂时无法读取，请确认管理员登录状态。'
  } finally {
    loading.value = false
  }
}

async function decide(item: RestoreRequest, action: 'approved' | 'rejected') {
  const reason = window.prompt(action === 'approved' ? '请输入批准原因' : '请输入驳回原因')?.trim()
  if (!reason) return
  try {
    await decideRestoreRequest(item.public_id, action, reason)
    await loadRequests()
  } catch {
    message.value = '审批失败。只有超级管理员可以审批，且申请必须处于待审批状态。'
  }
}

async function checkReadiness(item: RestoreRequest) {
  try {
    const readiness = await getRestoreExecutionReadiness(item.public_id)
    message.value = readiness.ready_to_execute
      ? '安全闸门检查通过，但尚未执行数据恢复。'
      : `暂不可执行：${readiness.blockers.join('；')}`
  } catch {
    message.value = '安全闸门检查失败，只有超级管理员可以执行检查。'
  }
}

async function executeRestore(item: RestoreRequest) {
  const confirmation = window.prompt('高风险操作：请输入 RESTORE INSERT ONLY 以确认只新增事务恢复')
  if (confirmation !== 'RESTORE INSERT ONLY') {
    message.value = '确认短语不正确，未执行恢复。'
    return
  }
  try {
    const result = await executeRestoreRequest(item.public_id, confirmation)
    message.value = `事务恢复完成：新增 ${result.total_inserted} 条，未覆盖、未删除。`
    await loadRequests()
  } catch {
    message.value = '恢复未执行或已整体回滚，请重新检查安全闸门和数据库约束。'
  }
}

onMounted(loadRequests)
</script>

<template>
  <main class="approval-page">
    <header><RouterLink to="/management/dashboard">Stay Scale</RouterLink><nav><RouterLink to="/management/dashboard">运营看板</RouterLink><RouterLink to="/management/reviews">导入审核</RouterLink><RouterLink to="/">普通页面</RouterLink></nav></header>
    <section class="hero"><span>RESTORE GOVERNANCE · M24</span><h1>恢复申请审批</h1><p>这里只审批恢复资格，不会执行数据库恢复。</p></section>
    <p v-if="message" class="message">{{ message }}</p>
    <section class="request-list">
      <p v-if="loading">正在读取申请…</p>
      <p v-else-if="!requests.length">暂无恢复申请。</p>
      <article v-for="item in requests" :key="item.public_id">
        <div><small>{{ item.status.toUpperCase() }}</small><h2>{{ item.archive_id }}</h2><p>可新增 {{ item.plan_snapshot.total_insert_candidates }} 条 · 冲突 {{ item.plan_snapshot.total_conflicts }} 条 · {{ new Date(item.created_at).toLocaleString('zh-CN') }}</p><p v-if="item.decision_reason">审批意见：{{ item.decision_reason }}</p><p v-if="item.execution_summary">执行结果：新增 {{ item.execution_summary.total_inserted }} 条 · 未覆盖 · 未删除 · {{ item.executed_at ? new Date(item.executed_at).toLocaleString('zh-CN') : '' }}</p></div>
        <div class="actions"><template v-if="item.status === 'pending'"><button type="button" @click="decide(item, 'approved')">批准</button><button type="button" class="reject" @click="decide(item, 'rejected')">驳回</button></template><template v-if="item.status === 'approved'"><button type="button" @click="checkReadiness(item)">执行前检查</button><button type="button" class="reject" @click="executeRestore(item)">执行只新增恢复</button></template></div>
      </article>
    </section>
  </main>
</template>

<style scoped>
.approval-page { min-height: 100vh; padding-bottom: 72px; background: radial-gradient(circle at 90% 0, rgb(192 119 70 / 16%), transparent 30%), #f5f0e6; color: #173b34; }
header, .hero, .request-list, .message { width: min(1100px, calc(100% - 40px)); margin-inline: auto; }
header { display: flex; justify-content: space-between; align-items: center; padding: 24px 0; border-bottom: 1px solid rgb(23 59 52 / 16%); }
header a { color: inherit; text-decoration: none; font-weight: 800; } nav { display: flex; gap: 18px; font-size: .75rem; }
.hero { padding: 72px 0 42px; } .hero span { color: #b45f35; font-size: .66rem; font-weight: 900; letter-spacing: .16em; }
.hero h1 { margin: 10px 0; font-family: 'Noto Serif SC', serif; font-size: clamp(2.5rem, 6vw, 4.7rem); font-weight: 500; } .hero p, article p { color: #61726d; }
.message { padding: 14px 18px; background: #fff8ed; border: 1px solid #d8c6aa; border-radius: 10px; }
.request-list { display: grid; gap: 12px; } article { display: flex; justify-content: space-between; gap: 20px; padding: 24px; background: rgb(255 253 248 / 90%); border: 1px solid rgb(23 59 52 / 14%); border-radius: 15px; }
article small { color: #b45f35; font-weight: 900; } article h2 { margin: 8px 0; font-family: Georgia, serif; font-size: 1.1rem; } article p { margin: 5px 0; font-size: .76rem; }
.actions { display: flex; align-items: center; gap: 8px; } button { padding: 10px 15px; color: white; background: #245a50; border: 0; border-radius: 8px; font-weight: 800; } button.reject { background: #a94a3f; }
@media (max-width: 650px) { header, article { align-items: flex-start; flex-direction: column; } nav { flex-wrap: wrap; } .actions, .actions button { width: 100%; } }
</style>
