<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createConversation, sendConversationMessage } from '../api/aiConversations'
import type { Conversation } from '../api/aiConversations'
import { saveAIRecommendationDraft } from '../ai/recommendationTransfer'
import type { ParsedPreferences } from '../types/preferenceParsing'

const conversation = ref<Conversation | null>(null)
const content = ref('')
const loading = ref(false)
const error = ref('')
const router = useRouter()

async function start() {
  try { conversation.value = await createConversation() }
  catch { error.value = '请先登录普通用户账号。' }
}

async function send() {
  if (!conversation.value || content.value.trim().length < 3) return
  loading.value = true
  error.value = ''
  try {
    conversation.value = await sendConversationMessage(conversation.value.public_id, content.value.trim())
    content.value = ''
  } catch { error.value = '消息发送失败，请确认后端服务正常。' }
  finally { loading.value = false }
}

async function continueToRecommendation(result: ParsedPreferences) {
  saveAIRecommendationDraft(result)
  await router.push('/recommendations?source=ai')
}

onMounted(start)
</script>

<template>
  <main class="chat-page">
    <header><RouterLink to="/">Stay Scale</RouterLink><nav><RouterLink to="/account">个人中心</RouterLink><RouterLink to="/recommendations">智能推荐</RouterLink></nav></header>
    <section class="hero"><span>AI TRAVEL COMPANION · M32</span><h1>把旅行想法，说给我听。</h1><p>AI 会先把自然语言整理成可确认的结构化需求，再带入推荐流程。</p></section>
    <section v-if="conversation" class="chat-card">
      <div class="messages">
        <p v-if="!conversation.messages.length" class="empty">例如：两个人去大理，住三晚，总预算 1600 元。</p>
        <article v-for="(message, index) in conversation.messages" :key="`${message.created_at}-${index}`" :class="message.role">
          <small>{{ message.role === 'user' ? '你' : 'Stay Scale AI' }}</small><p>{{ message.content }}</p>
          <div v-if="message.structured_result" class="structured-result"><div><span v-if="message.structured_result.city">{{ message.structured_result.city }}</span><span v-if="message.structured_result.check_in">{{ message.structured_result.check_in }} 至 {{ message.structured_result.check_out || '待确认' }}</span><span v-if="message.structured_result.guests">{{ message.structured_result.guests }} 人</span><span v-if="message.structured_result.budget_total">预算 ¥{{ message.structured_result.budget_total }}</span></div><button type="button" @click="continueToRecommendation(message.structured_result)">带入智能推荐 →</button></div>
        </article>
      </div>
      <form @submit.prevent="send"><input v-model="content" maxlength="1000" placeholder="描述你的旅行需求..." /><button :disabled="loading">{{ loading ? '整理中...' : '发送' }}</button></form>
    </section>
    <p v-if="error" class="error">{{ error }}</p>
  </main>
</template>

<style scoped>
.chat-page{min-height:100vh;padding-bottom:70px;background:radial-gradient(circle at 85% 0,rgb(194 115 62 / 18%),transparent 32%),#f4efe5;color:#173b34}.chat-page>header,.hero,.chat-card,.error{width:min(980px,calc(100% - 36px));margin-inline:auto}.chat-page>header{display:flex;justify-content:space-between;padding:24px 0;border-bottom:1px solid rgb(23 59 52 / 15%)}a{color:inherit;text-decoration:none;font-weight:800}nav{display:flex;gap:18px}.hero{padding:65px 0 35px}.hero span{color:#b45f35;font-size:.65rem;font-weight:900;letter-spacing:.16em}.hero h1{margin:10px 0;font-family:'Noto Serif SC',serif;font-size:clamp(2.4rem,6vw,4.5rem);font-weight:500}.hero p{color:#667570}.chat-card{box-sizing:border-box;padding:22px;background:#fffdf8;border:1px solid #d8cdbb;border-radius:16px}.messages{display:grid;gap:12px;min-height:280px}.messages article{max-width:80%;padding:12px 16px;border-radius:12px;background:#edf3ee}.messages article.user{justify-self:end;background:#245a50;color:white}.messages small{font-size:.65rem;font-weight:800}.messages article>p{margin:6px 0;line-height:1.6}.structured-result{display:grid;gap:10px;padding:10px;color:#173b34;background:#fff;border-radius:8px}.structured-result div{display:flex;flex-wrap:wrap;gap:6px}.structured-result span{padding:5px 8px;background:#edf3ee;border-radius:6px;font-size:.68rem}.structured-result button{justify-self:start}.empty{align-self:center;color:#71807c;text-align:center}.chat-card form{display:flex;gap:8px;margin-top:20px}.chat-card input{flex:1;padding:13px;border:1px solid #d6c9b6;border-radius:8px}.chat-card button{padding:11px 17px;color:white;background:#245a50;border:0;border-radius:8px;font-weight:800}.error{margin-top:15px;color:#a94a3f}@media(max-width:600px){.messages article{max-width:95%}.chat-card form{flex-direction:column}.chat-card button{width:100%}}
</style>
