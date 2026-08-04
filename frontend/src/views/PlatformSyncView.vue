<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { configureSyncSource, getSyncSources, runSyncSource } from '../api/platformSync'
import type { SyncSource } from '../api/platformSync'

const sources = ref<SyncSource[]>([])
const message = ref('')
const form = reactive({ platformCode: 'tujia', sourceLabel: 'tujia-demo.json', intervalMinutes: 360, isEnabled: true })

async function load() {
  try { sources.value = await getSyncSources() }
  catch { message.value = '同步源暂时无法读取。' }
}

async function save() {
  try {
    await configureSyncSource(form.platformCode, form.sourceLabel, form.intervalMinutes, form.isEnabled)
    message.value = form.isEnabled ? '同步源已保存，自动调度已启用。' : '同步源已保存，自动调度已停用。'
    await load()
  } catch { message.value = '配置失败，请检查平台代码、间隔和演示文件名。' }
}

async function run(item: SyncSource) {
  try {
    message.value = `${item.platform_name} 同步中...`
    await runSyncSource(item.platform_code)
    message.value = '同步完成。'
    await load()
  } catch {
    message.value = '同步失败，详细原因已保存在同步状态中。'
    await load()
  }
}

function time(value: string | null) { return value ? new Date(value).toLocaleString('zh-CN') : '尚未运行' }
onMounted(load)
</script>

<template>
  <main class="sync-page">
    <header><RouterLink to="/management/dashboard">Stay Scale</RouterLink><nav><RouterLink to="/management/dashboard">运营看板</RouterLink><RouterLink to="/management/reviews">审核队列</RouterLink></nav></header>
    <section class="hero"><span>AUTHORIZED DATA PIPELINE · M30</span><h1>平台同步中心</h1><p>配置授权接口或标准化文件连接器。后台会按设定间隔自动执行，失败任务最多重试三次。</p></section>
    <section class="configure"><h2>配置演示连接器</h2><label>平台代码<input v-model="form.platformCode" /></label><label>演示文件<input v-model="form.sourceLabel" /></label><label>同步间隔（分钟）<input v-model.number="form.intervalMinutes" type="number" min="15" max="10080" /></label><label class="toggle"><input v-model="form.isEnabled" type="checkbox" />启用自动同步</label><button @click="save">保存连接器</button></section>
    <p v-if="message" class="message">{{ message }}</p>
    <section class="sources"><p v-if="!sources.length">尚未配置同步源。</p><article v-for="item in sources" :key="item.public_id"><div><small>{{ item.connector_type }} · {{ item.status }} · {{ item.is_enabled ? '自动同步已启用' : '仅手动同步' }}</small><h2>{{ item.platform_name }}</h2><p>{{ item.source_label }} · 每 {{ item.interval_minutes }} 分钟</p><p>最近运行：{{ time(item.last_run_at) }} · 最近成功：{{ time(item.last_success_at) }}</p><p v-if="item.next_run_at">下次计划：{{ time(item.next_run_at) }}</p><p v-if="item.last_error" class="error">{{ item.last_error }}</p></div><button :disabled="item.status === 'running'" @click="run(item)">{{ item.status === 'running' ? '同步中' : '立即同步' }}</button></article></section>
  </main>
</template>

<style scoped>
.sync-page{min-height:100vh;padding-bottom:70px;background:radial-gradient(circle at 85% 0,rgb(184 109 61 / 18%),transparent 30%),#f4efe5;color:#173b34}.sync-page>header,.hero,.configure,.sources,.message{width:min(1080px,calc(100% - 40px));margin-inline:auto}.sync-page>header{display:flex;justify-content:space-between;padding:24px 0;border-bottom:1px solid rgb(23 59 52 / 15%)}nav{display:flex;gap:18px}a{color:inherit;text-decoration:none;font-weight:800}.hero{padding:70px 0 38px}.hero span{color:#b45f35;font-size:.65rem;font-weight:900;letter-spacing:.16em}.hero h1{margin:10px 0;font-family:'Noto Serif SC',serif;font-size:clamp(2.6rem,6vw,4.7rem);font-weight:500}.hero p,article p{color:#667570}.configure,.message,article{box-sizing:border-box;padding:22px;background:rgb(255 253 248 / 92%);border:1px solid rgb(23 59 52 / 14%);border-radius:14px}.configure{display:grid;grid-template-columns:1fr 1.6fr 1fr;gap:12px;align-items:end}.configure h2{grid-column:1/-1}.configure label{display:grid;gap:6px;color:#667570;font-size:.75rem}.configure .toggle{display:flex;align-items:center;gap:8px}.configure .toggle input{width:auto}input{box-sizing:border-box;width:100%;padding:12px;border:1px solid #d6c9b6;border-radius:8px}button{padding:11px 15px;color:white;background:#245a50;border:0;border-radius:8px;font-weight:800}.message{margin-top:12px}.sources{display:grid;gap:12px;margin-top:12px}article{display:flex;justify-content:space-between;align-items:center;gap:20px}article small{color:#b45f35;font-weight:900}.error{color:#a74532}@media(max-width:750px){.configure{grid-template-columns:1fr}article{align-items:flex-start;flex-direction:column}article button{width:100%}}
</style>
