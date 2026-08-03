<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { getRecommendationHistory, getUserFavorites, getUserProfile, loginUser, registerUser, removeUserFavorite } from '../api/users'
import type { Favorite, UserProfile } from '../api/users'
import { clearUserSession, hasUserSession, saveUserSession } from '../auth/userSession'

const mode = ref<'login' | 'register'>('login')
const profile = ref<UserProfile | null>(null)
const favorites = ref<Favorite[]>([])
const history = ref<Array<{ session_id: string; request: { city: string; check_in: string; check_out: string }; results: unknown[] }>>([])
const message = ref('')
const form = reactive({ email: '', password: '', displayName: '' })

async function loadAccount() {
  if (!hasUserSession()) return
  try { profile.value = await getUserProfile(); favorites.value = await getUserFavorites(); history.value = await getRecommendationHistory() }
  catch { clearUserSession(); profile.value = null }
}
async function submit() {
  message.value = ''
  try {
    const result = mode.value === 'register' ? await registerUser(form.email, form.password, form.displayName) : await loginUser(form.email, form.password)
    saveUserSession(result.access_token, result.user); profile.value = result.user; favorites.value = await getUserFavorites(); history.value = await getRecommendationHistory()
  } catch { message.value = mode.value === 'register' ? '注册失败，请检查邮箱或确认该邮箱未被使用。' : '邮箱或密码不正确。' }
}
async function removeFavorite(item: Favorite) { await removeUserFavorite(item.listing_public_id); favorites.value = favorites.value.filter((favorite) => favorite.listing_public_id !== item.listing_public_id) }
function logout() { clearUserSession(); profile.value = null; favorites.value = [] }
onMounted(loadAccount)
</script>

<template><main class="account-page"><header><RouterLink to="/">Stay Scale</RouterLink><RouterLink to="/">返回民宿搜索</RouterLink></header><section class="hero"><span>TRAVELER PROFILE · M29</span><h1>{{ profile ? `你好，${profile.display_name}` : '把喜欢的住处，留给下一段旅程。' }}</h1></section><section v-if="!profile" class="auth-card"><div class="tabs"><button @click="mode = 'login'">登录</button><button @click="mode = 'register'">注册</button></div><label v-if="mode === 'register'">昵称<input v-model="form.displayName" /></label><label>邮箱<input v-model="form.email" type="email" /></label><label>密码<input v-model="form.password" type="password" minlength="8" /></label><button class="primary" @click="submit">{{ mode === 'register' ? '创建账户' : '登录' }}</button><p v-if="message">{{ message }}</p></section><section v-else class="profile-card"><header><div><small>{{ profile.email }}</small><h2>我的收藏</h2></div><button @click="logout">退出登录</button></header><p v-if="!favorites.length">还没有收藏民宿，之后可以从民宿详情加入收藏。</p><article v-for="item in favorites" :key="item.listing_public_id"><div><strong>{{ item.name }}</strong><small>{{ item.city }} · {{ item.district }}</small></div><button @click="removeFavorite(item)">取消收藏</button></article><h2>推荐历史</h2><p v-if="!history.length">暂无推荐历史。</p><article v-for="item in history" :key="item.session_id"><div><strong>{{ item.request.city }}</strong><small>{{ item.request.check_in }} 至 {{ item.request.check_out }} · {{ item.results.length }} 个结果</small></div><RouterLink :to="`/recommendations?session=${item.session_id}`">查看</RouterLink></article></section></main></template>

<style scoped>
.account-page{min-height:100vh;padding-bottom:70px;background:radial-gradient(circle at 85% 0,rgb(194 115 62 / 18%),transparent 30%),linear-gradient(130deg,#f2eee4,#fbf8f1);color:#173b34}.account-page>header,.hero,.auth-card,.profile-card{width:min(940px,calc(100% - 36px));margin-inline:auto}.account-page>header{display:flex;justify-content:space-between;padding:24px 0;border-bottom:1px solid rgb(23 59 52 / 16%)}a{color:inherit;text-decoration:none;font-weight:800}.hero{padding:70px 0 36px}.hero span{color:#b45f35;font-size:.66rem;font-weight:900;letter-spacing:.16em}.hero h1{max-width:760px;margin:12px 0;font-family:'Noto Serif SC',serif;font-size:clamp(2.4rem,6vw,4.5rem);font-weight:500}.auth-card,.profile-card{box-sizing:border-box;padding:28px;background:rgb(255 253 248 / 92%);border:1px solid rgb(23 59 52 / 14%);border-radius:16px}.tabs{display:flex;gap:8px;margin-bottom:20px}label{display:grid;gap:7px;margin:14px 0;color:#61726d;font-size:.75rem}input{padding:13px;border:1px solid #d8cbb8;border-radius:8px;background:#fff}.primary,button{padding:10px 14px;border:0;border-radius:8px;background:#245a50;color:white;font-weight:800}.profile-card>header,article{display:flex;justify-content:space-between;align-items:center}.profile-card h2{margin:5px 0 20px;font-family:'Noto Serif SC',serif}article{padding:16px 0;border-top:1px solid #ded4c4}article div{display:grid;gap:5px}small{color:#71807c}@media(max-width:600px){article,.profile-card>header{align-items:flex-start;flex-direction:column;gap:12px}}
</style>
