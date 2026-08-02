<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { loginAdmin } from '../api/auth'
import { saveAdminSession } from '../auth/session'

const router = useRouter()
const route = useRoute()
const form = reactive({ username: 'admin', password: '' })
const state = ref<'idle' | 'loading' | 'error'>('idle')
const errorMessage = ref('')

async function submit() {
  if (form.username.trim().length < 3 || form.password.length < 8) {
    state.value = 'error'
    errorMessage.value = '请输入管理员账号和至少 8 位密码。'
    return
  }
  state.value = 'loading'
  errorMessage.value = ''
  try {
    const result = await loginAdmin(form.username.trim(), form.password)
    saveAdminSession(result.access_token, result.user)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/management/reviews'
    await router.replace(redirect)
  } catch {
    state.value = 'error'
    errorMessage.value = '账号或密码错误，或者管理员账号已停用。'
  }
}
</script>

<template>
  <main class="login-page">
    <RouterLink class="back-link" to="/">← 返回 Stay Scale</RouterLink>
    <section class="login-card">
      <div class="login-mark">S</div>
      <p>SECURE OPERATIONS · ADMIN ACCESS</p>
      <h1>数据审核台登录</h1>
      <span>只有已创建并启用的管理员账号可以处理平台导入记录。</span>
      <form @submit.prevent="submit">
        <label><small>管理员账号</small><input v-model="form.username" autocomplete="username" maxlength="64" /></label>
        <label><small>密码</small><input v-model="form.password" type="password" autocomplete="current-password" maxlength="128" /></label>
        <p v-if="state === 'error'" role="alert">{{ errorMessage }}</p>
        <button type="submit" :disabled="state === 'loading'">{{ state === 'loading' ? '正在验证…' : '进入审核台' }}</button>
      </form>
      <footer>访问令牌仅保存在当前浏览器 · 密码不会发送到前端日志</footer>
    </section>
  </main>
</template>

<style scoped>
.login-page { display: grid; min-height: 100vh; padding: 24px; background: radial-gradient(circle at 16% 12%, rgb(216 107 61 / 18%), transparent 28%), linear-gradient(135deg, #173a33, #285b50 55%, #dfd3b9); place-items: center; }
.back-link { position: fixed; top: 24px; left: 28px; color: rgb(255 255 255 / 72%); font-size: .75rem; text-decoration: none; }
.login-card { width: min(460px, 100%); padding: 42px; background: rgb(255 252 246 / 96%); border: 1px solid rgb(255 255 255 / 30%); border-radius: 24px; box-shadow: 0 34px 100px rgb(9 28 24 / 32%); }
.login-mark { display: grid; width: 52px; height: 52px; color: white; font-family: Georgia, serif; font-size: 1.4rem; background: var(--color-primary); border-radius: 50%; place-items: center; }
.login-card > p { margin: 26px 0 0; color: var(--color-accent); font-size: .62rem; font-weight: 900; letter-spacing: .15em; }
h1 { margin: 10px 0; color: var(--color-primary-deep); font-family: 'Noto Serif SC', serif; font-size: 2.2rem; font-weight: 600; }
.login-card > span { color: var(--color-muted); font-size: .78rem; line-height: 1.7; }
form { display: grid; gap: 15px; margin-top: 28px; }
label { display: flex; flex-direction: column; gap: 7px; }
label small { color: var(--color-muted); font-size: .65rem; }
input { padding: 13px 14px; color: var(--color-primary-deep); background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 9px; outline: 0; }
input:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px rgb(36 90 80 / 8%); }
form p { margin: 0; color: var(--color-danger); font-size: .7rem; }
button { padding: 14px; color: white; font-weight: 800; background: var(--color-primary); border: 0; border-radius: 9px; }
button:disabled { cursor: wait; opacity: .65; }
footer { padding-top: 20px; margin-top: 26px; color: var(--color-muted); font-size: .62rem; text-align: center; border-top: 1px solid var(--color-border); }
@media (max-width: 520px) { .login-page { padding: 14px; } .login-card { padding: 30px 22px; } .back-link { position: absolute; top: 16px; left: 18px; } }
</style>
