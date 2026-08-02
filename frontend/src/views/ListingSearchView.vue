<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { getLatestReviewAnalysis, getListingDetail, searchListings } from '../api/listings'
import ListingCard from '../components/ListingCard.vue'
import OfferDrawer from '../components/OfferDrawer.vue'
import type {
  ListingDetail,
  ListingSearchParams,
  ListingSearchResponse,
  ListingSort,
  ListingSummary,
  ReviewAnalysis,
} from '../types/listings'
import { formatShortDate, nextDateValue, stayNights } from '../utils/format'

type LoadState = 'idle' | 'loading' | 'success' | 'error'

const facilityOptions = [
  { code: 'wifi', label: '无线网络' },
  { code: 'kitchen', label: '可做饭' },
  { code: 'parking', label: '停车位' },
  { code: 'sea_view', label: '海景' },
]

const form = reactive({
  city: '大理市',
  checkIn: '2026-10-02',
  checkOut: '2026-10-05',
  guests: 2,
  district: '',
  keyword: '',
  maxPrice: '',
  sort: 'price_asc' as ListingSort,
  facilities: [] as string[],
})

const appliedSearch = ref<ListingSearchParams>({
  city: form.city,
  checkIn: form.checkIn,
  checkOut: form.checkOut,
  guests: form.guests,
})
const loadState = ref<LoadState>('idle')
const searchError = ref('')
const validationError = ref('')
const results = ref<ListingSearchResponse>({ items: [], total: 0, page: 1, page_size: 20 })
const drawerOpen = ref(false)
const detail = ref<ListingDetail | null>(null)
const detailLoading = ref(false)
const detailError = ref('')
const reviewAnalysis = ref<ReviewAnalysis | null>(null)
const reviewAnalysisError = ref('')

const nights = computed(() =>
  stayNights(appliedSearch.value.checkIn, appliedSearch.value.checkOut),
)
const minimumCheckOut = computed(() => nextDateValue(form.checkIn))
const stayLabel = computed(
  () =>
    `${formatShortDate(appliedSearch.value.checkIn)} — ${formatShortDate(appliedSearch.value.checkOut)}`,
)

function currentParams(): ListingSearchParams {
  return {
    city: form.city.trim(),
    checkIn: form.checkIn,
    checkOut: form.checkOut,
    guests: Number(form.guests),
    district: form.district || undefined,
    keyword: form.keyword.trim() || undefined,
    facilities: [...form.facilities],
    maxPrice: form.maxPrice ? Number(form.maxPrice) : undefined,
    sort: form.sort,
  }
}

function validateSearch(): boolean {
  validationError.value = ''
  if (!form.city.trim()) {
    validationError.value = '请输入目的地城市。'
    return false
  }
  if (!form.checkIn || !form.checkOut || form.checkOut <= form.checkIn) {
    validationError.value = '离店日期必须晚于入住日期。'
    return false
  }
  return true
}

async function runSearch() {
  if (!validateSearch()) return
  const params = currentParams()
  appliedSearch.value = params
  loadState.value = 'loading'
  searchError.value = ''

  try {
    results.value = await searchListings(params)
    loadState.value = 'success'
  } catch {
    results.value = { items: [], total: 0, page: 1, page_size: 20 }
    loadState.value = 'error'
    searchError.value = '暂时无法取得报价，请确认 FastAPI 和 MySQL 已启动后重试。'
  }
}

function toggleFacility(code: string) {
  const index = form.facilities.indexOf(code)
  if (index >= 0) form.facilities.splice(index, 1)
  else form.facilities.push(code)
  void runSearch()
}

function syncCheckOut() {
  if (form.checkIn && (!form.checkOut || form.checkOut < minimumCheckOut.value)) {
    form.checkOut = minimumCheckOut.value
  }
}

async function openComparison(listing: ListingSummary) {
  drawerOpen.value = true
  detail.value = null
  detailError.value = ''
  reviewAnalysis.value = null
  reviewAnalysisError.value = ''
  detailLoading.value = true

  try {
    const [listingDetail, analysis] = await Promise.all([
      getListingDetail(listing.public_id, appliedSearch.value),
      getLatestReviewAnalysis(listing.public_id).catch(() => {
        reviewAnalysisError.value = '评论分析暂时无法读取。'
        return null
      }),
    ])
    detail.value = listingDetail
    reviewAnalysis.value = analysis
  } catch {
    detailError.value = '平台报价读取失败，请关闭后重新尝试。'
  } finally {
    detailLoading.value = false
  }
}

onMounted(runSearch)
</script>

<template>
  <main class="search-page">
    <header class="site-header">
      <a class="brand" href="/" aria-label="Stay Scale 首页">
        <span class="brand-mark">S</span>
        <span class="brand-copy">
          <strong>Stay Scale</strong>
          <small>民宿比价实验室</small>
        </span>
      </a>

      <nav aria-label="主导航">
        <a class="active" href="#results">找民宿</a>
        <RouterLink to="/recommendations">智能推荐</RouterLink>
        <RouterLink to="/status">运行状态</RouterLink>
      </nav>
    </header>

    <section class="search-hero">
      <div class="hero-copy">
        <p class="eyebrow">STAY FAIR · TRAVEL SLOW</p>
        <h1>把每个平台的价格，<br /><em>摊在同一张桌上。</em></h1>
        <p class="hero-intro">
          同一家民宿，不同平台、不同房型、不同优惠条件。我们把费用拆开，帮你看见真正的入住总价。
        </p>
      </div>

      <aside class="hero-note" aria-label="当前演示数据说明">
        <span>云南 · 大理</span>
        <strong>03</strong>
        <p>家统一民宿<br />来自 3 个平台的演示报价</p>
      </aside>
    </section>

    <form class="search-console" aria-label="民宿搜索条件" @submit.prevent="runSearch">
      <label class="destination-field">
        <span>去哪里</span>
        <div>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s7-6 7-12a7 7 0 1 0-14 0c0 6 7 12 7 12Zm0-9a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" /></svg>
          <input v-model="form.city" name="city" placeholder="城市或目的地" />
        </div>
      </label>

      <label>
        <span>入住</span>
        <input v-model="form.checkIn" name="check-in" type="date" @change="syncCheckOut" />
      </label>

      <label>
        <span>离店</span>
        <input v-model="form.checkOut" name="check-out" type="date" :min="minimumCheckOut" />
      </label>

      <label>
        <span>住客</span>
        <select v-model.number="form.guests" name="guests">
          <option v-for="count in 6" :key="count" :value="count">{{ count }} 位住客</option>
        </select>
      </label>

      <button class="search-button" type="submit" :disabled="loadState === 'loading'">
        <span>{{ loadState === 'loading' ? '比价中' : '开始比价' }}</span>
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 14 0m-5-5 5 5-5 5" /></svg>
      </button>

      <p v-if="validationError" class="validation-error" role="alert">{{ validationError }}</p>
    </form>

    <section id="results" class="results-section" aria-live="polite">
      <div class="filter-bar">
        <div class="filter-group facility-filters" aria-label="设施筛选">
          <span class="filter-label">想要</span>
          <button
            v-for="option in facilityOptions"
            :key="option.code"
            type="button"
            :class="{ selected: form.facilities.includes(option.code) }"
            :aria-pressed="form.facilities.includes(option.code)"
            @click="toggleFacility(option.code)"
          >
            {{ option.label }}
          </button>
        </div>

        <div class="select-filters">
          <label>
            <span class="sr-only">区域</span>
            <select v-model="form.district" @change="runSearch">
              <option value="">全部区域</option>
              <option value="大理镇">大理镇</option>
              <option value="双廊镇">双廊镇</option>
            </select>
          </label>
          <label>
            <span class="sr-only">价格上限</span>
            <select v-model="form.maxPrice" @change="runSearch">
              <option value="">不限总价</option>
              <option value="1200">总价 ¥1,200 内</option>
              <option value="1500">总价 ¥1,500 内</option>
              <option value="2200">总价 ¥2,200 内</option>
            </select>
          </label>
          <label>
            <span class="sr-only">排序方式</span>
            <select v-model="form.sort" @change="runSearch">
              <option value="price_asc">总价从低到高</option>
              <option value="price_desc">总价从高到低</option>
              <option value="rating_desc">评分优先</option>
            </select>
          </label>
        </div>
      </div>

      <div class="results-heading">
        <div>
          <p>CURATED STAYS · {{ appliedSearch.city }}</p>
          <h2>
            {{ loadState === 'loading' ? '正在寻找合适的住处' : `找到 ${results.total} 家可比价民宿` }}
          </h2>
        </div>
        <p class="trip-summary">{{ stayLabel }} · {{ nights }} 晚 · {{ appliedSearch.guests }} 人</p>
      </div>

      <div v-if="loadState === 'loading'" class="skeleton-list" aria-label="正在加载民宿">
        <div v-for="index in 3" :key="index" class="skeleton-card">
          <span></span><div><i></i><i></i><i></i></div>
        </div>
      </div>

      <div v-else-if="loadState === 'error'" class="result-state error-state" role="alert">
        <span>!</span>
        <h2>报价线路暂时中断</h2>
        <p>{{ searchError }}</p>
        <button type="button" @click="runSearch">重新连接</button>
      </div>

      <div v-else-if="!results.items.length" class="result-state">
        <span>○</span>
        <h2>没有找到符合条件的演示民宿</h2>
        <p>试着取消部分设施或价格筛选，当前演示报价只覆盖 2026 年 10 月 2 日至 5 日。</p>
      </div>

      <div v-else class="listing-list">
        <ListingCard
          v-for="(listing, index) in results.items"
          :key="listing.public_id"
          :listing="listing"
          :nights="nights"
          :index="index"
          @compare="openComparison"
        />
      </div>
    </section>

    <footer class="site-footer">
      <div><span class="brand-mark small">S</span><strong>Stay Scale</strong></div>
      <p>演示价格和评论不用于真实预订 · M14 评论洞察与跨平台比价</p>
      <RouterLink to="/status">检查服务状态 →</RouterLink>
    </footer>

      <OfferDrawer
      v-if="drawerOpen"
      :detail="detail"
      :loading="detailLoading"
        :error="detailError"
        :review-analysis="reviewAnalysis"
        :review-analysis-error="reviewAnalysisError"
      :check-in="appliedSearch.checkIn"
      :check-out="appliedSearch.checkOut"
      @close="drawerOpen = false"
    />
  </main>
</template>

<style scoped>
.search-page {
  min-height: 100vh;
  overflow: hidden;
}

.site-header,
.search-hero,
.search-console,
.results-section,
.site-footer {
  width: min(1240px, calc(100% - 48px));
  margin-right: auto;
  margin-left: auto;
}

.site-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 0;
}

.brand {
  display: inline-flex;
  gap: 11px;
  align-items: center;
  color: var(--color-primary-deep);
  text-decoration: none;
}

.brand-copy {
  display: flex;
  flex-direction: column;
}

.brand-copy strong {
  font-family: Georgia, serif;
  font-size: 1rem;
  letter-spacing: 0.02em;
}

.brand-copy small {
  margin-top: 2px;
  color: var(--color-muted);
  font-size: 0.58rem;
  letter-spacing: 0.1em;
}

.brand-mark {
  display: grid;
  width: 36px;
  height: 36px;
  color: var(--color-surface);
  font-family: Georgia, serif;
  font-weight: 700;
  background: var(--color-primary);
  border-radius: 50% 50% 50% 14%;
  place-items: center;
}

.brand-mark.small {
  width: 28px;
  height: 28px;
  font-size: 0.75rem;
}

nav {
  display: flex;
  gap: 28px;
}

nav a {
  position: relative;
  padding: 7px 0;
  color: var(--color-muted);
  font-size: 0.78rem;
  font-weight: 700;
  text-decoration: none;
}

nav a.active {
  color: var(--color-primary-deep);
}

nav a.active::after {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  height: 2px;
  content: '';
  background: var(--color-accent);
}

.search-hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 230px;
  gap: 60px;
  align-items: end;
  padding: 78px 0 98px;
}

.search-hero::before {
  position: absolute;
  top: 32px;
  right: 4%;
  width: 330px;
  height: 180px;
  content: '';
  border-top: 1px dashed rgb(36 90 80 / 25%);
  border-right: 1px dashed rgb(36 90 80 / 25%);
  border-radius: 0 160px 0 0;
  transform: rotate(-7deg);
  pointer-events: none;
}

.search-hero::after {
  position: absolute;
  top: 20px;
  right: 31%;
  width: 9px;
  height: 9px;
  content: '';
  background: var(--color-accent);
  border: 5px solid var(--color-canvas);
  border-radius: 50%;
}

.eyebrow {
  margin: 0;
  color: var(--color-accent);
  font-size: 0.7rem;
  font-weight: 900;
  letter-spacing: 0.18em;
}

.hero-copy h1 {
  margin: 20px 0 24px;
  color: var(--color-primary-deep);
  font-family: 'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', serif;
  font-size: clamp(2.8rem, 5.7vw, 5.6rem);
  font-weight: 600;
  line-height: 1.12;
  letter-spacing: -0.055em;
}

.hero-copy h1 em {
  color: var(--color-accent);
  font-style: normal;
}

.hero-intro {
  max-width: 650px;
  margin: 0;
  color: var(--color-muted);
  font-size: 1rem;
  line-height: 1.85;
}

.hero-note {
  position: relative;
  z-index: 1;
  padding: 26px;
  background: rgb(255 252 246 / 65%);
  border: 1px solid var(--color-border);
  border-radius: 90px 90px 14px 14px;
  backdrop-filter: blur(8px);
}

.hero-note > span {
  color: var(--color-accent);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.11em;
}

.hero-note strong {
  display: block;
  margin: 14px 0 4px;
  color: var(--color-primary-deep);
  font-family: Georgia, serif;
  font-size: 4rem;
  font-weight: 400;
  line-height: 1;
}

.hero-note p {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.72rem;
  line-height: 1.6;
}

.search-console {
  position: relative;
  z-index: 4;
  display: grid;
  grid-template-columns: 1.25fr 1fr 1fr 0.8fr auto;
  gap: 0;
  padding: 10px;
  margin-top: -45px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 18px;
  box-shadow: 0 24px 70px rgb(31 58 51 / 14%);
}

.search-console label {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
  padding: 8px 20px;
  border-right: 1px solid var(--color-border);
}

.search-console label > span {
  margin-bottom: 6px;
  color: var(--color-muted);
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.1em;
}

.search-console input,
.search-console select {
  width: 100%;
  min-width: 0;
  padding: 2px 0;
  color: var(--color-primary-deep);
  font-size: 0.9rem;
  font-weight: 700;
  background: transparent;
  border: 0;
  outline: 0;
}

.destination-field > div {
  display: flex;
  gap: 8px;
  align-items: center;
}

.destination-field svg {
  width: 18px;
  color: var(--color-accent);
  fill: currentcolor;
}

.search-button {
  display: flex;
  gap: 24px;
  align-items: center;
  justify-content: space-between;
  min-width: 155px;
  padding: 16px 20px;
  color: white;
  font-weight: 800;
  background: var(--color-primary);
  border: 0;
  border-radius: 11px;
  transition: transform 180ms ease, background 180ms ease;
}

.search-button:hover:not(:disabled) {
  background: var(--color-primary-deep);
  transform: translateY(-2px);
}

.search-button:disabled {
  cursor: wait;
  opacity: 0.7;
}

.search-button svg {
  width: 20px;
  fill: none;
  stroke: currentcolor;
  stroke-linecap: round;
  stroke-width: 1.8;
}

.validation-error {
  position: absolute;
  top: calc(100% + 8px);
  left: 10px;
  margin: 0;
  color: var(--color-danger);
  font-size: 0.74rem;
}

.results-section {
  padding: 58px 0 80px;
}

.filter-bar,
.results-heading,
.site-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.filter-bar {
  gap: 20px;
  padding-bottom: 26px;
  border-bottom: 1px solid var(--color-border);
}

.filter-group,
.select-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.filter-label {
  margin-right: 5px;
  color: var(--color-muted);
  font-size: 0.72rem;
  font-weight: 800;
}

.facility-filters button,
.select-filters select {
  padding: 8px 12px;
  color: var(--color-muted);
  font-size: 0.72rem;
  font-weight: 700;
  background: rgb(255 252 246 / 55%);
  border: 1px solid var(--color-border);
  border-radius: 999px;
}

.facility-filters button.selected {
  color: var(--color-surface);
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.select-filters select {
  padding-right: 28px;
  border-radius: 8px;
}

.results-heading {
  align-items: flex-end;
  padding: 42px 0 24px;
}

.results-heading p {
  margin: 0 0 7px;
  color: var(--color-accent);
  font-size: 0.66rem;
  font-weight: 900;
  letter-spacing: 0.14em;
}

.results-heading h2 {
  margin: 0;
  color: var(--color-primary-deep);
  font-family: 'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', serif;
  font-size: clamp(1.7rem, 3vw, 2.5rem);
  font-weight: 600;
}

.results-heading .trip-summary {
  margin: 0 0 6px;
  color: var(--color-muted);
  letter-spacing: 0;
}

.listing-list,
.skeleton-list {
  display: grid;
  gap: 18px;
}

.skeleton-card {
  display: grid;
  grid-template-columns: 240px 1fr;
  min-height: 220px;
  overflow: hidden;
  background: rgb(255 252 246 / 60%);
  border: 1px solid var(--color-border);
  border-radius: 22px;
}

.skeleton-card > span,
.skeleton-card i {
  background: linear-gradient(100deg, rgb(36 90 80 / 5%) 20%, rgb(255 255 255 / 52%) 45%, rgb(36 90 80 / 5%) 70%) 0 0 / 250% 100%;
  animation: shimmer 1.5s infinite linear;
}

.skeleton-card > div {
  display: grid;
  gap: 18px;
  align-content: center;
  padding: 30px;
}

.skeleton-card i {
  width: 70%;
  height: 15px;
  border-radius: 6px;
}

.skeleton-card i:nth-child(2) { width: 46%; height: 27px; }
.skeleton-card i:nth-child(3) { width: 82%; }

.result-state {
  display: grid;
  min-height: 330px;
  padding: 40px;
  text-align: center;
  background: rgb(255 252 246 / 55%);
  border: 1px dashed var(--color-border);
  border-radius: 22px;
  place-content: center;
}

.result-state > span {
  color: var(--color-accent);
  font-family: Georgia, serif;
  font-size: 3rem;
}

.result-state h2 {
  margin: 10px 0 7px;
  color: var(--color-primary-deep);
  font-family: 'Noto Serif SC', serif;
}

.result-state p {
  max-width: 530px;
  margin: 0;
  color: var(--color-muted);
  line-height: 1.7;
}

.result-state button {
  width: fit-content;
  padding: 10px 16px;
  margin: 20px auto 0;
  color: white;
  font-weight: 700;
  background: var(--color-primary);
  border: 0;
  border-radius: 8px;
}

.site-footer {
  gap: 20px;
  padding: 32px 0 42px;
  border-top: 1px solid var(--color-border);
}

.site-footer > div {
  display: flex;
  gap: 9px;
  align-items: center;
  color: var(--color-primary-deep);
  font-family: Georgia, serif;
}

.site-footer p,
.site-footer a {
  color: var(--color-muted);
  font-size: 0.7rem;
  text-decoration: none;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@keyframes shimmer {
  to { background-position: -250% 0; }
}

@media (max-width: 960px) {
  .search-console {
    grid-template-columns: 1.3fr 1fr 1fr;
  }

  .search-console label:nth-of-type(3) {
    border-right: 0;
  }

  .search-console label:nth-of-type(4) {
    border-top: 1px solid var(--color-border);
  }

  .search-button {
    grid-column: 2 / -1;
    margin-top: 10px;
  }

  .filter-bar {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (max-width: 700px) {
  .site-header,
  .search-hero,
  .search-console,
  .results-section,
  .site-footer {
    width: min(100% - 28px, 620px);
  }

  .site-header {
    padding-top: 17px;
  }

  .brand-copy small,
  nav a.active {
    display: none;
  }

  nav {
    gap: 14px;
  }

  .search-hero {
    display: block;
    padding: 62px 0 84px;
  }

  .search-hero::before {
    right: -180px;
  }

  .search-hero::after {
    right: 12%;
  }

  .hero-copy h1 {
    font-size: clamp(2.6rem, 13vw, 4.3rem);
  }

  .hero-note {
    display: none;
  }

  .search-console {
    display: grid;
    grid-template-columns: 1fr 1fr;
    padding: 8px;
    margin-top: -44px;
  }

  .search-console label {
    padding: 12px;
    border-bottom: 1px solid var(--color-border);
  }

  .search-console .destination-field {
    grid-column: 1 / -1;
    border-right: 0;
  }

  .search-console label:nth-of-type(3) {
    border-right: 0;
  }

  .search-console label:nth-of-type(4) {
    border-bottom: 0;
  }

  .search-button {
    grid-row: 3;
    grid-column: 2;
    min-width: 0;
    margin: 8px 0 0 8px;
  }

  .results-section {
    padding-top: 48px;
  }

  .select-filters {
    display: grid;
    grid-template-columns: 1fr 1fr;
    width: 100%;
  }

  .select-filters label:last-child {
    grid-column: 1 / -1;
  }

  .select-filters select {
    width: 100%;
  }

  .results-heading {
    align-items: flex-start;
    flex-direction: column;
    gap: 12px;
  }

  .results-heading .trip-summary {
    order: -1;
  }

  .skeleton-card {
    grid-template-columns: 1fr;
  }

  .skeleton-card > span {
    min-height: 170px;
  }

  .site-footer {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
