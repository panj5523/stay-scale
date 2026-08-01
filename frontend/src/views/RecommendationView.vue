<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { createRecommendation } from '../api/recommendations'
import type {
  RecommendationItem,
  RecommendationParams,
  RecommendationResponse,
  ScoreBreakdown,
  TravelStyle,
} from '../types/recommendations'
import { formatShortDate, stayNights } from '../utils/format'

type LoadState = 'idle' | 'loading' | 'success' | 'error'

const travelStyles: Array<{
  code: TravelStyle
  number: string
  name: string
  subtitle: string
  description: string
}> = [
  { code: 'value', number: '01', name: '精打细算', subtitle: 'VALUE', description: '总价优先，在预算内寻找更扎实的选择。' },
  { code: 'comfort', number: '02', name: '住得舒服', subtitle: 'COMFORT', description: '更看重评分、空调和日常居住体验。' },
  { code: 'scenery', number: '03', name: '为风景停留', subtitle: 'SCENERY', description: '让海景与环境特色拥有更高权重。' },
  { code: 'family', number: '04', name: '全家出发', subtitle: 'FAMILY', description: '厨房、洗衣与出入便利更重要。' },
]

const facilityOptions = [
  { code: 'wifi', label: '无线网络' },
  { code: 'air_conditioning', label: '空调' },
  { code: 'kitchen', label: '厨房' },
  { code: 'washer', label: '洗衣机' },
  { code: 'parking', label: '停车位' },
  { code: 'sea_view', label: '海景' },
  { code: 'ground_floor', label: '低楼层' },
]

const districtOptions = ['大理镇', '双廊镇']
const scoreLabels: Array<{ key: keyof ScoreBreakdown; label: string }> = [
  { key: 'price', label: '价格' },
  { key: 'rating', label: '评分' },
  { key: 'facilities', label: '设施' },
  { key: 'platform_coverage', label: '平台覆盖' },
  { key: 'location', label: '区域' },
]

const form = reactive({
  city: '大理市',
  checkIn: '2026-10-02',
  checkOut: '2026-10-05',
  guests: 2,
  budgetTotal: '1600',
  preferredFacilities: [] as string[],
  preferredDistricts: [] as string[],
  travelStyle: 'value' as TravelStyle,
  topK: 3,
})

const loadState = ref<LoadState>('idle')
const validationError = ref('')
const requestError = ref('')
const recommendation = ref<RecommendationResponse | null>(null)

const selectedStyle = computed(
  () => travelStyles.find((style) => style.code === form.travelStyle) ?? travelStyles[0],
)
const tripNights = computed(() => stayNights(form.checkIn, form.checkOut))
const resultTripLabel = computed(() => {
  const request = recommendation.value?.request
  if (!request) return ''
  return `${formatShortDate(request.check_in)} — ${formatShortDate(request.check_out)} · ${stayNights(request.check_in, request.check_out)} 晚`
})
const resultStyleName = computed(() => {
  const code = recommendation.value?.request.travel_style
  return travelStyles.find((style) => style.code === code)?.name ?? ''
})

function toggleSelection(values: string[], value: string) {
  const index = values.indexOf(value)
  if (index >= 0) values.splice(index, 1)
  else values.push(value)
}

function validateForm(): boolean {
  validationError.value = ''
  if (!form.city.trim()) {
    validationError.value = '请输入目的地城市。'
    return false
  }
  if (!form.checkIn || !form.checkOut || form.checkOut <= form.checkIn) {
    validationError.value = '离店日期必须晚于入住日期。'
    return false
  }
  if (form.budgetTotal && Number(form.budgetTotal) < 0) {
    validationError.value = '预算不能小于 0。'
    return false
  }
  return true
}

function currentParams(): RecommendationParams {
  return {
    city: form.city.trim(),
    checkIn: form.checkIn,
    checkOut: form.checkOut,
    guests: Number(form.guests),
    budgetTotal: form.budgetTotal ? Number(form.budgetTotal) : undefined,
    preferredFacilities: [...form.preferredFacilities],
    preferredDistricts: [...form.preferredDistricts],
    travelStyle: form.travelStyle,
    topK: Number(form.topK),
  }
}

async function runRecommendation() {
  if (!validateForm()) return
  loadState.value = 'loading'
  requestError.value = ''

  try {
    recommendation.value = await createRecommendation(currentParams())
    loadState.value = 'success'
  } catch {
    recommendation.value = null
    loadState.value = 'error'
    requestError.value = '暂时无法完成推荐，请确认 FastAPI 和 MySQL 已启动后重试。'
  }
}

function scoreWidth(score: string): string {
  return `${Math.min(100, Math.max(0, Number(score)))}%`
}

function rankLabel(item: RecommendationItem): string {
  return item.rank.toString().padStart(2, '0')
}
</script>

<template>
  <main class="recommendation-page">
    <header class="recommendation-header">
      <RouterLink class="brand" to="/" aria-label="Stay Scale 首页">
        <span class="brand-mark">S</span>
        <span class="brand-copy"><strong>Stay Scale</strong><small>住得明白，也住得合拍</small></span>
      </RouterLink>
      <nav aria-label="主导航">
        <RouterLink to="/">找民宿</RouterLink>
        <a class="active" href="#preference-studio">智能推荐</a>
        <RouterLink to="/status">运行状态</RouterLink>
      </nav>
    </header>

    <section class="recommendation-hero">
      <div class="hero-index" aria-hidden="true">06</div>
      <div class="hero-copy">
        <p class="eyebrow">A STAY THAT FITS · 可解释推荐</p>
        <h1>不是替你决定，<br /><em>是把偏好算清楚。</em></h1>
        <p>
          告诉我们这趟旅程真正看重什么。系统会用当前可订价格、评分、设施和平台覆盖度计算排序，
          每一个结论都有依据。
        </p>
      </div>
      <div class="hero-score" aria-label="推荐算法说明">
        <div><span>5</span><small>项评分维度</small></div>
        <div><span>4</span><small>种旅行风格</small></div>
        <p>EXPLAINABLE<br />BY DESIGN</p>
      </div>
    </section>

    <form id="preference-studio" class="preference-studio" @submit.prevent="runRecommendation">
      <div class="studio-heading">
        <div>
          <p>01 · TRIP BASICS</p>
          <h2>先说说这趟旅行</h2>
        </div>
        <span>{{ tripNights > 0 ? `${tripNights} 晚 · ${form.guests} 人` : '等待完整日期' }}</span>
      </div>

      <div class="basic-grid">
        <label>
          <span>目的地</span>
          <input v-model="form.city" name="city" placeholder="城市或目的地" />
        </label>
        <label>
          <span>入住</span>
          <input v-model="form.checkIn" name="check-in" type="date" />
        </label>
        <label>
          <span>离店</span>
          <input v-model="form.checkOut" name="check-out" type="date" />
        </label>
        <label>
          <span>住客</span>
          <select v-model.number="form.guests" name="guests">
            <option v-for="count in 6" :key="count" :value="count">{{ count }} 位</option>
          </select>
        </label>
        <label>
          <span>入住总预算</span>
          <div class="currency-input"><b>¥</b><input v-model="form.budgetTotal" name="budget" type="number" min="0" /></div>
        </label>
      </div>

      <fieldset class="style-section">
        <legend><span>02 · TRAVEL TEMPO</span>你想怎样度过这几天？</legend>
        <div class="style-grid">
          <label v-for="style in travelStyles" :key="style.code" :class="{ selected: form.travelStyle === style.code }">
            <input v-model="form.travelStyle" type="radio" name="travel-style" :value="style.code" />
            <span class="style-number">{{ style.number }}</span>
            <small>{{ style.subtitle }}</small>
            <strong>{{ style.name }}</strong>
            <p>{{ style.description }}</p>
          </label>
        </div>
      </fieldset>

      <div class="preference-grid">
        <fieldset>
          <legend><span>03 · MUST-HAVES</span>特别在意的设施</legend>
          <div class="choice-list">
            <button
              v-for="facility in facilityOptions"
              :key="facility.code"
              type="button"
              :class="{ selected: form.preferredFacilities.includes(facility.code) }"
              :aria-pressed="form.preferredFacilities.includes(facility.code)"
              @click="toggleSelection(form.preferredFacilities, facility.code)"
            >
              <i></i>{{ facility.label }}
            </button>
          </div>
        </fieldset>
        <fieldset>
          <legend><span>04 · NEIGHBORHOOD</span>更喜欢住在哪儿</legend>
          <div class="choice-list">
            <button
              v-for="district in districtOptions"
              :key="district"
              type="button"
              :class="{ selected: form.preferredDistricts.includes(district) }"
              :aria-pressed="form.preferredDistricts.includes(district)"
              @click="toggleSelection(form.preferredDistricts, district)"
            >
              <i></i>{{ district }}
            </button>
          </div>
        </fieldset>
      </div>

      <div class="submit-row">
        <div>
          <strong>当前倾向：{{ selectedStyle.name }}</strong>
          <span>结果由真实候选计算，相同条件会得到稳定排序。</span>
          <p v-if="validationError" role="alert">{{ validationError }}</p>
        </div>
        <button type="submit" :disabled="loadState === 'loading'">
          {{ loadState === 'loading' ? '正在计算匹配度…' : '生成我的推荐' }}
          <span aria-hidden="true">→</span>
        </button>
      </div>
    </form>

    <section id="recommendation-results" class="result-section" aria-live="polite">
      <div v-if="loadState === 'idle'" class="result-intro">
        <span>YOUR MATCH</span>
        <h2>选择完成后，推荐会在这里展开。</h2>
        <p>我们会同时展示综合得分和五项评分依据，不用猜“为什么是它”。</p>
      </div>

      <div v-else-if="loadState === 'loading'" class="calculating-state">
        <div class="orbit"><i></i><span>5D</span></div>
        <h2>正在衡量每一种取舍</h2>
        <p>核对可订价格、评分、设施、区域与平台覆盖度…</p>
      </div>

      <div v-else-if="loadState === 'error'" class="empty-state error-state" role="alert">
        <span>CONNECTION PAUSED</span>
        <h2>推荐线路暂时没有接通</h2>
        <p>{{ requestError }}</p>
        <button type="button" @click="runRecommendation">重新尝试</button>
      </div>

      <div v-else-if="recommendation?.status === 'no_candidates'" class="empty-state">
        <span>NO AVAILABLE MATCH</span>
        <h2>这组条件下暂无可订民宿</h2>
        <p>可以调整日期、预算或减少设施偏好。你的请求已保存，系统没有用无报价房源凑数。</p>
      </div>

      <template v-else-if="recommendation">
        <div class="result-heading">
          <div>
            <p>PERSONAL SHORTLIST · {{ recommendation.request.city }}</p>
            <h2>为你排出的 {{ recommendation.results.length }} 个选择</h2>
          </div>
          <div class="result-meta">
            <strong>{{ resultTripLabel }}</strong>
            <span>{{ resultStyleName }} · {{ recommendation.algorithm_version }}</span>
          </div>
        </div>

        <article v-for="item in recommendation.results" :key="item.listing_public_id" class="recommendation-card">
          <div class="rank-column">
            <span>RANK</span>
            <strong>{{ rankLabel(item) }}</strong>
            <i></i>
          </div>

          <div class="listing-summary">
            <p>{{ item.district }} · {{ item.platform_count }} 个平台可比</p>
            <h3>{{ item.listing_name }}</h3>
            <ul>
              <li v-for="reason in item.reasons" :key="reason">{{ reason }}</li>
            </ul>
            <div class="listing-facts">
              <span><small>入住总价</small><strong>¥{{ Number(item.total_amount).toLocaleString('zh-CN') }}</strong></span>
              <span><small>最高评分</small><strong>{{ item.best_rating ?? '暂无' }}</strong></span>
              <RouterLink to="/">返回比价列表 →</RouterLink>
            </div>
          </div>

          <div class="score-panel">
            <div class="total-score">
              <span :style="{ '--score': `${Number(item.total_score) * 3.6}deg` }"><b>{{ item.total_score }}</b></span>
              <p>综合匹配度<small>/ 100</small></p>
            </div>
            <div class="score-list">
              <div v-for="score in scoreLabels" :key="score.key">
                <span>{{ score.label }}</span>
                <i><b :style="{ width: scoreWidth(item.score_breakdown[score.key]) }"></b></i>
                <strong>{{ item.score_breakdown[score.key] }}</strong>
              </div>
            </div>
          </div>
        </article>

        <p class="session-note">推荐会话 {{ recommendation.session_id }} 已保存，可通过后端接口重新读取。</p>
      </template>
    </section>

    <footer class="recommendation-footer">
      <div><span class="brand-mark small">S</span><strong>Stay Scale</strong></div>
      <p>推荐分数用于演示，不代表平台背书或真实预订建议 · M6 前端推荐体验</p>
      <RouterLink to="/status">检查服务状态 →</RouterLink>
    </footer>
  </main>
</template>

<style scoped>
.recommendation-page { min-height: 100vh; overflow: hidden; }
.recommendation-header, .recommendation-hero, .preference-studio, .result-section, .recommendation-footer { width: min(1240px, calc(100% - 48px)); margin-inline: auto; }
.recommendation-header { display: flex; align-items: center; justify-content: space-between; padding: 24px 0; }
.brand { display: inline-flex; gap: 11px; align-items: center; color: var(--color-primary-deep); text-decoration: none; }
.brand-mark { display: grid; width: 36px; height: 36px; color: var(--color-surface); font-family: Georgia, serif; font-weight: 700; background: var(--color-primary); border-radius: 50% 50% 50% 14%; place-items: center; }
.brand-mark.small { width: 28px; height: 28px; font-size: .75rem; }
.brand-copy { display: flex; flex-direction: column; }
.brand-copy strong { font-family: Georgia, serif; font-size: 1rem; }
.brand-copy small { margin-top: 2px; color: var(--color-muted); font-size: .58rem; letter-spacing: .08em; }
nav { display: flex; gap: 28px; }
nav a { position: relative; padding: 7px 0; color: var(--color-muted); font-size: .78rem; font-weight: 700; text-decoration: none; }
nav a.active { color: var(--color-primary-deep); }
nav a.active::after { position: absolute; right: 0; bottom: 0; left: 0; height: 2px; content: ''; background: var(--color-accent); }

.recommendation-hero { position: relative; display: grid; grid-template-columns: 130px minmax(0, 1fr) 230px; gap: 42px; align-items: center; padding: 92px 0 112px; }
.recommendation-hero::after { position: absolute; top: 55px; right: 7%; width: 310px; height: 200px; content: ''; border-top: 1px dashed rgb(36 90 80 / 24%); border-right: 1px dashed rgb(36 90 80 / 24%); border-radius: 0 160px 0 0; transform: rotate(-8deg); pointer-events: none; }
.hero-index { color: transparent; font-family: Georgia, serif; font-size: 7rem; line-height: 1; -webkit-text-stroke: 1px rgb(36 90 80 / 18%); }
.eyebrow, .studio-heading p, fieldset legend span, .result-heading p { margin: 0; color: var(--color-accent); font-size: .68rem; font-weight: 900; letter-spacing: .16em; }
.hero-copy h1 { margin: 18px 0 24px; color: var(--color-primary-deep); font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: clamp(2.8rem, 5.5vw, 5.3rem); font-weight: 600; line-height: 1.12; letter-spacing: -.055em; }
.hero-copy h1 em { color: var(--color-accent); font-style: normal; }
.hero-copy > p:last-child { max-width: 670px; margin: 0; color: var(--color-muted); line-height: 1.85; }
.hero-score { position: relative; z-index: 1; display: grid; grid-template-columns: 1fr 1fr; padding: 24px; background: rgb(255 252 246 / 72%); border: 1px solid var(--color-border); border-radius: 70px 70px 14px 14px; backdrop-filter: blur(8px); }
.hero-score div { text-align: center; }
.hero-score div:first-child { border-right: 1px solid var(--color-border); }
.hero-score span { display: block; color: var(--color-primary-deep); font-family: Georgia, serif; font-size: 2.6rem; }
.hero-score small { color: var(--color-muted); font-size: .62rem; }
.hero-score p { grid-column: 1 / -1; margin: 20px 0 0; color: var(--color-accent); font-size: .6rem; font-weight: 800; line-height: 1.5; letter-spacing: .16em; text-align: center; }

.preference-studio { padding: 42px; background: rgb(255 252 246 / 91%); border: 1px solid var(--color-border); border-radius: 24px; box-shadow: 0 30px 80px rgb(31 58 51 / 12%); }
.studio-heading { display: flex; align-items: flex-end; justify-content: space-between; padding-bottom: 26px; border-bottom: 1px solid var(--color-border); }
.studio-heading h2, fieldset legend, .result-heading h2, .result-intro h2, .calculating-state h2, .empty-state h2 { margin: 8px 0 0; color: var(--color-primary-deep); font-family: 'Noto Serif SC', 'Songti SC', serif; font-size: 1.8rem; font-weight: 600; }
.studio-heading > span { color: var(--color-muted); font-size: .78rem; }
.basic-grid { display: grid; grid-template-columns: 1.2fr repeat(2, 1fr) .65fr 1fr; margin: 28px 0 44px; border: 1px solid var(--color-border); border-radius: 14px; }
.basic-grid > label { min-width: 0; padding: 15px 18px; border-right: 1px solid var(--color-border); }
.basic-grid > label:last-child { border-right: 0; }
.basic-grid label > span { display: block; margin-bottom: 8px; color: var(--color-muted); font-size: .62rem; font-weight: 800; letter-spacing: .1em; }
.basic-grid input, .basic-grid select { width: 100%; min-width: 0; padding: 0; color: var(--color-primary-deep); font-size: .9rem; font-weight: 700; background: transparent; border: 0; outline: 0; }
.currency-input { display: flex; gap: 6px; color: var(--color-accent); }
fieldset { min-width: 0; padding: 0; margin: 0; border: 0; }
fieldset legend { display: flex; flex-direction: column; margin-bottom: 20px; }
fieldset legend span { margin-bottom: 7px; }
.style-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.style-grid label { position: relative; min-height: 190px; padding: 20px; overflow: hidden; cursor: pointer; background: var(--color-canvas); border: 1px solid transparent; border-radius: 15px; transition: transform 180ms ease, border 180ms ease; }
.style-grid label:hover { transform: translateY(-3px); }
.style-grid label.selected { background: rgb(36 90 80 / 7%); border-color: var(--color-primary); }
.style-grid input { position: absolute; opacity: 0; }
.style-number { position: absolute; top: 8px; right: 13px; color: rgb(36 90 80 / 11%); font-family: Georgia, serif; font-size: 4.5rem; }
.style-grid small { position: relative; display: block; color: var(--color-accent); font-size: .58rem; font-weight: 900; letter-spacing: .14em; }
.style-grid strong { position: relative; display: block; margin-top: 42px; color: var(--color-primary-deep); font-family: 'Noto Serif SC', serif; font-size: 1.18rem; }
.style-grid p { position: relative; margin: 10px 0 0; color: var(--color-muted); font-size: .76rem; line-height: 1.65; }
.preference-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 50px; padding-top: 44px; margin-top: 44px; border-top: 1px solid var(--color-border); }
.choice-list { display: flex; flex-wrap: wrap; gap: 9px; }
.choice-list button { display: inline-flex; gap: 8px; align-items: center; padding: 10px 13px; color: var(--color-muted); font-size: .76rem; font-weight: 700; background: transparent; border: 1px solid var(--color-border); border-radius: 999px; }
.choice-list button i { width: 7px; height: 7px; background: var(--color-border); border-radius: 50%; }
.choice-list button.selected { color: var(--color-primary); background: rgb(36 90 80 / 7%); border-color: var(--color-primary); }
.choice-list button.selected i { background: var(--color-accent); box-shadow: 0 0 0 3px rgb(216 107 61 / 13%); }
.submit-row { display: flex; align-items: center; justify-content: space-between; gap: 28px; padding-top: 34px; margin-top: 42px; border-top: 1px solid var(--color-border); }
.submit-row > div { display: flex; flex-direction: column; color: var(--color-primary-deep); }
.submit-row > div span { margin-top: 5px; color: var(--color-muted); font-size: .72rem; }
.submit-row p { margin: 7px 0 0; color: var(--color-danger); font-size: .75rem; }
.submit-row > button { display: flex; gap: 38px; align-items: center; justify-content: space-between; min-width: 245px; padding: 17px 20px; color: white; font-weight: 800; background: var(--color-primary); border: 0; border-radius: 11px; }
.submit-row > button:hover:not(:disabled) { background: var(--color-primary-deep); transform: translateY(-2px); }
.submit-row > button:disabled { cursor: wait; opacity: .65; }

.result-section { padding: 92px 0 82px; }
.result-intro, .calculating-state, .empty-state { display: grid; min-height: 300px; padding: 40px; text-align: center; border: 1px dashed var(--color-border); border-radius: 24px; place-content: center; }
.result-intro > span, .empty-state > span { color: var(--color-accent); font-size: .66rem; font-weight: 900; letter-spacing: .18em; }
.result-intro p, .calculating-state p, .empty-state p { max-width: 580px; margin: 12px auto 0; color: var(--color-muted); line-height: 1.7; }
.orbit { position: relative; display: grid; width: 82px; height: 82px; margin: 0 auto 18px; color: var(--color-primary); border: 1px dashed var(--color-primary); border-radius: 50%; place-items: center; animation: rotate 2.2s linear infinite; }
.orbit i { position: absolute; top: -5px; width: 10px; height: 10px; background: var(--color-accent); border-radius: 50%; }
.orbit span { font-family: Georgia, serif; font-weight: 700; animation: rotate-back 2.2s linear infinite; }
.empty-state button { width: fit-content; padding: 10px 16px; margin: 22px auto 0; color: white; font-weight: 700; background: var(--color-primary); border: 0; border-radius: 8px; }
.result-heading { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 26px; }
.result-meta { display: flex; flex-direction: column; align-items: flex-end; color: var(--color-primary-deep); font-size: .78rem; }
.result-meta span { margin-top: 5px; color: var(--color-muted); font-size: .7rem; }
.recommendation-card { display: grid; grid-template-columns: 90px minmax(0, 1fr) 360px; min-height: 310px; margin-top: 16px; overflow: hidden; background: rgb(255 252 246 / 88%); border: 1px solid var(--color-border); border-radius: 22px; box-shadow: 0 18px 50px rgb(31 58 51 / 7%); }
.rank-column { display: flex; align-items: center; flex-direction: column; padding: 26px 12px; color: var(--color-muted); background: rgb(36 90 80 / 5%); }
.rank-column span { font-size: .56rem; font-weight: 900; letter-spacing: .16em; }
.rank-column strong { margin-top: 15px; color: var(--color-primary); font-family: Georgia, serif; font-size: 3.2rem; font-weight: 400; }
.rank-column i { flex: 1; width: 1px; margin-top: 20px; background: linear-gradient(var(--color-accent), transparent); }
.listing-summary { display: flex; min-width: 0; padding: 32px; flex-direction: column; }
.listing-summary > p { margin: 0; color: var(--color-accent); font-size: .66rem; font-weight: 800; letter-spacing: .1em; }
.listing-summary h3 { margin: 10px 0 18px; color: var(--color-primary-deep); font-family: 'Noto Serif SC', serif; font-size: clamp(1.35rem, 2.4vw, 2rem); font-weight: 600; }
.listing-summary ul { display: grid; gap: 8px; padding: 0; margin: 0; list-style: none; }
.listing-summary li { position: relative; padding-left: 17px; color: var(--color-muted); font-size: .8rem; line-height: 1.55; }
.listing-summary li::before { position: absolute; top: .5em; left: 0; width: 6px; height: 6px; content: ''; background: var(--color-success); border-radius: 50%; }
.listing-facts { display: flex; gap: 28px; align-items: flex-end; padding-top: 22px; margin-top: auto; border-top: 1px solid var(--color-border); }
.listing-facts span { display: flex; flex-direction: column; }
.listing-facts small { color: var(--color-muted); font-size: .6rem; }
.listing-facts strong { margin-top: 3px; color: var(--color-primary-deep); font-size: 1rem; }
.listing-facts a { margin-left: auto; color: var(--color-primary); font-size: .72rem; font-weight: 800; text-decoration: none; }
.score-panel { display: grid; grid-template-columns: 130px 1fr; gap: 22px; align-items: center; padding: 30px; background: var(--color-primary-deep); }
.total-score { text-align: center; }
.total-score > span { display: grid; width: 110px; height: 110px; color: white; background: conic-gradient(var(--color-accent) var(--score), rgb(255 255 255 / 12%) 0); border-radius: 50%; place-items: center; }
.total-score > span::before { position: absolute; width: 90px; height: 90px; content: ''; background: var(--color-primary-deep); border-radius: 50%; }
.total-score b { position: relative; font-family: Georgia, serif; font-size: 1.8rem; font-weight: 400; }
.total-score p { margin: 11px 0 0; color: white; font-size: .68rem; font-weight: 700; }
.total-score small { color: rgb(255 255 255 / 45%); }
.score-list { display: grid; gap: 13px; }
.score-list > div { display: grid; grid-template-columns: 48px 1fr 32px; gap: 8px; align-items: center; color: rgb(255 255 255 / 62%); font-size: .6rem; }
.score-list i { height: 4px; overflow: hidden; background: rgb(255 255 255 / 12%); border-radius: 9px; }
.score-list i b { display: block; height: 100%; background: var(--color-accent); border-radius: inherit; }
.score-list strong { color: white; font-family: Georgia, serif; font-size: .7rem; font-weight: 400; text-align: right; }
.session-note { margin: 18px 0 0; color: var(--color-muted); font-size: .65rem; text-align: right; }
.recommendation-footer { display: flex; gap: 20px; align-items: center; justify-content: space-between; padding: 32px 0 42px; border-top: 1px solid var(--color-border); }
.recommendation-footer > div { display: flex; gap: 9px; align-items: center; color: var(--color-primary-deep); font-family: Georgia, serif; }
.recommendation-footer p, .recommendation-footer a { color: var(--color-muted); font-size: .7rem; text-decoration: none; }
@keyframes rotate { to { transform: rotate(360deg); } }
@keyframes rotate-back { to { transform: rotate(-360deg); } }

@media (max-width: 1050px) {
  .recommendation-hero { grid-template-columns: minmax(0, 1fr) 210px; }
  .hero-index { display: none; }
  .basic-grid { grid-template-columns: 1.2fr 1fr 1fr; }
  .basic-grid > label:nth-child(3) { border-right: 0; }
  .basic-grid > label:nth-child(n + 4) { border-top: 1px solid var(--color-border); }
  .basic-grid > label:nth-child(4) { grid-column: 1 / 2; }
  .basic-grid > label:last-child { grid-column: 2 / -1; }
  .recommendation-card { grid-template-columns: 74px minmax(0, 1fr); }
  .score-panel { grid-column: 1 / -1; grid-template-columns: 140px 1fr; }
}

@media (max-width: 720px) {
  .recommendation-header, .recommendation-hero, .preference-studio, .result-section, .recommendation-footer { width: min(100% - 28px, 620px); }
  .brand-copy small, nav a:first-child { display: none; }
  nav { gap: 14px; }
  .recommendation-hero { display: block; padding: 62px 0 76px; }
  .hero-score { display: none; }
  .hero-copy h1 { font-size: clamp(2.6rem, 13vw, 4.3rem); }
  .preference-studio { padding: 24px 18px; border-radius: 18px; }
  .studio-heading { align-items: flex-start; flex-direction: column; gap: 12px; }
  .basic-grid { grid-template-columns: 1fr 1fr; }
  .basic-grid > label { border-bottom: 1px solid var(--color-border); }
  .basic-grid > label:first-child, .basic-grid > label:last-child { grid-column: 1 / -1; border-right: 0; }
  .basic-grid > label:nth-child(3) { border-right: 0; }
  .basic-grid > label:nth-child(4) { grid-column: auto; border-bottom: 0; }
  .basic-grid > label:last-child { border-bottom: 0; }
  .style-grid { grid-template-columns: 1fr 1fr; }
  .style-grid label { min-height: 175px; }
  .preference-grid { grid-template-columns: 1fr; gap: 32px; }
  .submit-row { align-items: stretch; flex-direction: column; }
  .submit-row > button { width: 100%; }
  .result-section { padding-top: 62px; }
  .result-heading { align-items: flex-start; flex-direction: column; gap: 14px; }
  .result-meta { align-items: flex-start; }
  .recommendation-card { grid-template-columns: 58px minmax(0, 1fr); }
  .rank-column { padding-inline: 7px; }
  .rank-column strong { font-size: 2.2rem; }
  .listing-summary { padding: 23px 18px; }
  .listing-facts { align-items: flex-start; flex-wrap: wrap; gap: 18px; }
  .listing-facts a { width: 100%; margin-left: 0; }
  .score-panel { grid-template-columns: 1fr; }
  .total-score { display: flex; gap: 18px; align-items: center; text-align: left; }
  .total-score > span { flex: 0 0 auto; width: 90px; height: 90px; }
  .total-score > span::before { width: 72px; height: 72px; }
  .recommendation-footer { align-items: flex-start; flex-direction: column; }
}

@media (prefers-reduced-motion: reduce) {
  .orbit, .orbit span { animation: none; }
}
</style>
