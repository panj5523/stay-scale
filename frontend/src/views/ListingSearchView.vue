<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { getLatestReviewAnalysis, getListingDetail, searchListings } from '../api/listings'
import { addUserFavorite, getUserFavorites, removeUserFavorite } from '../api/users'
import { hasUserSession } from '../auth/userSession'
import ListingCard from '../components/ListingCard.vue'
import OfferDrawer from '../components/OfferDrawer.vue'
import {
  MAX_COMPARISONS,
  addComparison,
  getComparisons,
  removeComparison,
} from '../comparison/comparisonStorage'
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
const favoriteIds = ref(new Set<string>())
const favoritePendingIds = ref(new Set<string>())
const favoriteMessage = ref('')
const favoriteMessageKind = ref<'info' | 'success' | 'error'>('info')
const comparisonIds = ref(new Set(getComparisons().map((entry) => entry.listing.public_id)))
const comparisonMessage = ref('')
const comparisonMessageKind = ref<'success' | 'error'>('success')

const nights = computed(() =>
  stayNights(appliedSearch.value.checkIn, appliedSearch.value.checkOut),
)
const minimumCheckOut = computed(() => nextDateValue(form.checkIn))
const stayLabel = computed(
  () =>
    `${formatShortDate(appliedSearch.value.checkIn)} — ${formatShortDate(appliedSearch.value.checkOut)}`,
)
const activeFilterCount = computed(
  () => form.facilities.length + Number(Boolean(form.district)) + Number(Boolean(form.maxPrice)),
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

function clearFilters() {
  form.facilities.splice(0)
  form.district = ''
  form.maxPrice = ''
  form.sort = 'price_asc'
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

async function loadFavorites() {
  if (!hasUserSession()) return

  try {
    const favorites = await getUserFavorites()
    favoriteIds.value = new Set(favorites.map((favorite) => favorite.listing_public_id))
  } catch {
    favoriteMessageKind.value = 'error'
    favoriteMessage.value = '收藏状态暂时无法读取，你仍可继续浏览房源。'
  }
}

async function toggleFavorite(listing: ListingSummary) {
  favoriteMessage.value = ''
  if (!hasUserSession()) {
    favoriteMessageKind.value = 'info'
    favoriteMessage.value = '登录后即可收藏房源，并在个人中心随时查看。'
    return
  }
  if (favoritePendingIds.value.has(listing.public_id)) return

  favoritePendingIds.value = new Set(favoritePendingIds.value).add(listing.public_id)
  const wasFavorite = favoriteIds.value.has(listing.public_id)

  try {
    if (wasFavorite) {
      await removeUserFavorite(listing.public_id)
      const nextIds = new Set(favoriteIds.value)
      nextIds.delete(listing.public_id)
      favoriteIds.value = nextIds
      favoriteMessage.value = `已取消收藏「${listing.name}」。`
    } else {
      await addUserFavorite(listing.public_id)
      favoriteIds.value = new Set(favoriteIds.value).add(listing.public_id)
      favoriteMessage.value = `已收藏「${listing.name}」。`
    }
    favoriteMessageKind.value = 'success'
  } catch {
    favoriteMessageKind.value = 'error'
    favoriteMessage.value = '收藏操作没有完成，请稍后重试。'
  } finally {
    const nextPendingIds = new Set(favoritePendingIds.value)
    nextPendingIds.delete(listing.public_id)
    favoritePendingIds.value = nextPendingIds
  }
}

function toggleComparison(listing: ListingSummary) {
  comparisonMessage.value = ''
  if (comparisonIds.value.has(listing.public_id)) {
    removeComparison(listing.public_id)
    const nextIds = new Set(comparisonIds.value)
    nextIds.delete(listing.public_id)
    comparisonIds.value = nextIds
    comparisonMessageKind.value = 'success'
    comparisonMessage.value = `已将「${listing.name}」移出比较清单。`
    return
  }

  const result = addComparison({
    listing,
    search: {
      checkIn: appliedSearch.value.checkIn,
      checkOut: appliedSearch.value.checkOut,
      guests: appliedSearch.value.guests,
    },
  })
  if (result === 'full') {
    comparisonMessageKind.value = 'error'
    comparisonMessage.value = `比较清单最多保留 ${MAX_COMPARISONS} 家，请先移出一家。`
    return
  }

  comparisonIds.value = new Set(comparisonIds.value).add(listing.public_id)
  comparisonMessageKind.value = 'success'
  comparisonMessage.value = `已将「${listing.name}」加入比较清单。`
}

onMounted(() => {
  void runSearch()
  void loadFavorites()
})
</script>

<template>
  <main class="search-page">
    <header class="site-header">
      <a class="brand" href="/" aria-label="Stay Scale 首页">Stay Scale</a>

      <nav aria-label="主导航">
        <a class="active" href="#results">首页</a>
        <a href="#search-console">目的地</a>
        <RouterLink to="/recommendations">智能推荐</RouterLink>
        <RouterLink to="/account">收藏夹</RouterLink>
        <RouterLink to="/compare">我的比较</RouterLink>
      </nav>

      <div class="header-actions">
        <RouterLink to="/account" aria-label="我的收藏">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1.1L12 21l7.8-7.5 1.1-1.1a5.5 5.5 0 0 0-.1-7.8Z" /></svg>
          <span>收藏</span>
        </RouterLink>
        <RouterLink class="profile-link" to="/account" aria-label="个人中心">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm7 8a7 7 0 0 0-14 0" /></svg>
        </RouterLink>
      </div>
    </header>

    <section class="hero-shell">
      <div class="hero-overlay"></div>
      <div class="hero-content">
        <p class="eyebrow">STAY FAIR · TRAVEL FREE</p>
        <h1>智能对比，<br />选出最适合你的民宿</h1>
        <p>多平台价格对比 · 真实住客评价 · 可解释智能推荐</p>
      </div>

      <form id="search-console" class="search-console" aria-label="民宿搜索条件" @submit.prevent="runSearch">
        <label class="destination-field">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s7-6 7-12a7 7 0 1 0-14 0c0 6 7 12 7 12Zm0-9a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" /></svg>
          <span><small>目的地</small><input v-model="form.city" name="city" placeholder="城市或目的地" /></span>
        </label>

        <label>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 2v3m10-3v3M3 9h18M5 4h14a2 2 0 0 1 2 2v14H3V6a2 2 0 0 1 2-2Z" /></svg>
          <span><small>入住日期</small><input v-model="form.checkIn" name="check-in" type="date" @change="syncCheckOut" /></span>
        </label>

        <label>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 2v3m10-3v3M3 9h18M5 4h14a2 2 0 0 1 2 2v14H3V6a2 2 0 0 1 2-2Z" /></svg>
          <span><small>退房日期</small><input v-model="form.checkOut" name="check-out" type="date" :min="minimumCheckOut" /></span>
        </label>

        <label>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm7 8a7 7 0 0 0-14 0" /></svg>
          <span>
            <small>入住人数</small>
            <select v-model.number="form.guests" name="guests">
              <option v-for="count in 6" :key="count" :value="count">{{ count }} 位成人</option>
            </select>
          </span>
        </label>

        <button class="search-button" type="submit" :disabled="loadState === 'loading'">
          {{ loadState === 'loading' ? '正在比价' : '搜索民宿' }}
        </button>

        <p v-if="validationError" class="validation-error" role="alert">{{ validationError }}</p>
      </form>
    </section>

    <section id="results" class="results-section" aria-live="polite">
      <div class="filter-bar">
        <div class="filter-group facility-filters" aria-label="设施筛选">
          <span class="filter-title">筛选</span>
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
              <option value="">位置区域</option>
              <option value="大理镇">大理镇</option>
              <option value="双廊镇">双廊镇</option>
            </select>
          </label>
          <label>
            <span class="sr-only">价格上限</span>
            <select v-model="form.maxPrice" @change="runSearch">
              <option value="">价格范围</option>
              <option value="1200">总价 ¥1,200 内</option>
              <option value="1500">总价 ¥1,500 内</option>
              <option value="2200">总价 ¥2,200 内</option>
            </select>
          </label>
          <label>
            <span class="sr-only">排序方式</span>
            <select v-model="form.sort" @change="runSearch">
              <option value="price_asc">推荐排序</option>
              <option value="price_desc">总价从高到低</option>
              <option value="rating_desc">评分优先</option>
            </select>
          </label>
          <button v-if="activeFilterCount" class="clear-filter" type="button" @click="clearFilters">
            清空 {{ activeFilterCount }} 项
          </button>
        </div>
      </div>

      <div class="results-heading">
        <div>
          <p>CURATED STAYS · {{ appliedSearch.city }}</p>
          <h2>{{ loadState === 'loading' ? '正在寻找合适的住处' : `找到 ${results.total} 家可比价民宿` }}</h2>
          <span>以下为你整理多平台报价与住客评价</span>
        </div>
        <div class="results-actions">
          <p class="trip-summary">{{ stayLabel }} · {{ nights }} 晚 · {{ appliedSearch.guests }} 人</p>
          <RouterLink v-if="comparisonIds.size" class="comparison-shortcut" to="/compare">
            查看比较 {{ comparisonIds.size }}/{{ MAX_COMPARISONS }} →
          </RouterLink>
        </div>
      </div>

      <div
        v-if="favoriteMessage"
        class="favorite-message"
        :class="`favorite-message--${favoriteMessageKind}`"
        role="status"
      >
        <span>{{ favoriteMessage }}</span>
        <RouterLink v-if="favoriteMessageKind === 'info'" to="/account">前往登录</RouterLink>
        <button type="button" aria-label="关闭收藏提示" @click="favoriteMessage = ''">×</button>
      </div>

      <div
        v-if="comparisonMessage"
        class="favorite-message comparison-message"
        :class="`favorite-message--${comparisonMessageKind}`"
        role="status"
      >
        <span>{{ comparisonMessage }}</span>
        <RouterLink v-if="comparisonIds.size" to="/compare">查看比较</RouterLink>
        <button type="button" aria-label="关闭比较提示" @click="comparisonMessage = ''">×</button>
      </div>

      <div v-if="loadState === 'loading'" class="skeleton-list" aria-label="正在加载民宿">
        <div v-for="index in 3" :key="index" class="skeleton-card"><span></span><i></i><i></i></div>
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
          :favorite="favoriteIds.has(listing.public_id)"
          :favorite-pending="favoritePendingIds.has(listing.public_id)"
          :compared="comparisonIds.has(listing.public_id)"
          @compare="openComparison"
          @toggle-favorite="toggleFavorite"
          @toggle-comparison="toggleComparison"
        />
      </div>

      <div class="trust-strip" aria-label="平台服务优势">
        <div><span>◇</span><p><strong>多平台价格对比</strong><small>同房源更低价</small></p></div>
        <div><span>◎</span><p><strong>真实住客评价</strong><small>多维度真实反馈</small></p></div>
        <div><span>✦</span><p><strong>智能推荐排序</strong><small>更懂你的选择</small></p></div>
        <div><span>◌</span><p><strong>全程价格透明</strong><small>费用拆分更清晰</small></p></div>
      </div>
    </section>

    <footer class="site-footer">
      <strong>Stay Scale</strong>
      <p>演示价格和评论不用于真实预订 · 跨平台民宿智能比价</p>
      <RouterLink to="/status">服务状态 →</RouterLink>
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
  overflow-x: clip;
  overflow-y: visible;
}

.site-header,
.results-section,
.site-footer {
  width: min(1400px, calc(100% - 72px));
  margin-right: auto;
  margin-left: auto;
}

.site-header {
  position: sticky;
  z-index: 30;
  top: 0;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 34px;
  align-items: center;
  min-height: 78px;
  isolation: isolate;
}

.site-header::before {
  position: absolute;
  z-index: -1;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 100vw;
  content: '';
  background: rgb(255 255 255 / 88%);
  border-bottom: 1px solid rgb(219 229 234 / 88%);
  box-shadow: 0 8px 28px rgb(22 50 79 / 6%);
  transform: translateX(-50%);
  backdrop-filter: blur(16px) saturate(1.15);
}

.brand {
  color: var(--color-primary-deep);
  font-family: Georgia, 'Times New Roman', serif;
  font-size: clamp(1.6rem, 2.5vw, 2.4rem);
  font-weight: 700;
  letter-spacing: -0.03em;
  text-decoration: none;
}

nav {
  display: flex;
  gap: clamp(22px, 3vw, 44px);
  height: 78px;
  align-items: center;
}

nav a {
  position: relative;
  display: grid;
  height: 100%;
  color: var(--color-ink);
  font-size: 0.9rem;
  text-decoration: none;
  place-items: center;
}

nav a::after {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  height: 2px;
  content: '';
  background: transparent;
}

nav a:hover,
nav a.active {
  color: var(--color-primary);
}

nav a.active::after {
  background: var(--color-primary);
}

.header-actions {
  display: flex;
  gap: 18px;
  align-items: center;
  justify-content: flex-end;
}

.header-actions a {
  display: flex;
  gap: 7px;
  align-items: center;
  color: var(--color-primary-deep);
  font-size: 0.82rem;
  text-decoration: none;
}

.header-actions svg {
  width: 21px;
  fill: none;
  stroke: currentcolor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.6;
}

.header-actions .profile-link {
  display: grid;
  width: 38px;
  height: 38px;
  color: white;
  background: var(--color-primary-deep);
  border-radius: 50%;
  place-items: center;
}

.profile-link svg { width: 19px; }

.hero-shell {
  position: relative;
  min-height: 390px;
  margin-bottom: 66px;
  overflow: visible;
  background: #dcecf5;
}

.hero-shell::before {
  position: absolute;
  inset: 0;
  content: '';
  background: url('/images/stay-scale-hero-aegean-v2.png') center 54% / cover no-repeat;
  filter: saturate(0.88) contrast(0.92) brightness(0.94);
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgb(238 247 252 / 91%) 0%, rgb(220 237 247 / 58%) 34%, rgb(197 224 240 / 5%) 66%),
    linear-gradient(rgb(117 179 215 / 4%), rgb(57 137 187 / 8%)),
    linear-gradient(0deg, rgb(22 50 79 / 8%), transparent 58%);
}

.hero-content {
  position: relative;
  z-index: 1;
  width: min(1400px, calc(100% - 72px));
  padding-top: 62px;
  margin: auto;
}

.eyebrow {
  margin: 0 0 16px;
  color: var(--color-accent-deep);
  font-size: 0.68rem;
  font-weight: 900;
  letter-spacing: 0.18em;
}

.hero-content h1 {
  margin: 0;
  color: var(--color-primary-deep);
  font-family: 'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', serif;
  font-size: clamp(2.6rem, 4.2vw, 4.6rem);
  font-weight: 700;
  line-height: 1.17;
  letter-spacing: -0.045em;
}

.hero-content > p:last-child {
  margin: 20px 0 0;
  color: var(--color-primary);
  font-size: 1rem;
  letter-spacing: 0.03em;
}

.search-console {
  position: absolute;
  z-index: 3;
  right: 50%;
  bottom: -32px;
  display: grid;
  grid-template-columns: 1.25fr 1fr 1fr 0.9fr auto;
  width: min(1320px, calc(100% - 120px));
  min-height: 96px;
  padding: 12px;
  background: rgb(255 253 248 / 96%);
  border: 1px solid rgb(46 111 149 / 45%);
  border-radius: 14px;
  box-shadow: var(--shadow-float);
  transform: translateX(50%);
  backdrop-filter: blur(14px);
}

.search-console label {
  display: flex;
  gap: 13px;
  align-items: center;
  min-width: 0;
  padding: 8px 20px;
  border-right: 1px solid var(--color-border);
}

.search-console label > svg {
  flex: 0 0 auto;
  width: 20px;
  color: var(--color-primary-soft);
  fill: none;
  stroke: currentcolor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.6;
}

.destination-field > svg { fill: currentcolor; stroke: none; }

.search-console label > span {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
}

.search-console small {
  margin-bottom: 5px;
  color: var(--color-muted);
  font-size: 0.65rem;
  font-weight: 700;
}

.search-console input,
.search-console select {
  width: 100%;
  min-width: 0;
  padding: 0;
  color: var(--color-primary-deep);
  font-size: 0.82rem;
  font-weight: 700;
  background: transparent;
  border: 0;
  outline: 0;
}

.search-button {
  min-width: 150px;
  margin-left: 12px;
  color: white;
  font-weight: 800;
  background: linear-gradient(135deg, var(--color-accent), #f07c68);
  border: 0;
  border-radius: 10px;
  box-shadow: 0 10px 22px rgb(226 109 90 / 24%);
  transition: transform 180ms ease, box-shadow 180ms ease;
}

.search-button:hover:not(:disabled) {
  box-shadow: 0 14px 28px rgb(226 109 90 / 32%);
  transform: translateY(-2px);
}

.search-button:disabled { cursor: wait; opacity: 0.7; }

.validation-error {
  position: absolute;
  top: calc(100% + 8px);
  left: 12px;
  margin: 0;
  color: var(--color-danger);
  font-size: 0.72rem;
}

.results-section { padding: 12px 0 70px; }

.filter-bar,
.results-heading,
.site-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.filter-bar {
  gap: 18px;
  min-height: 54px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--color-border);
}

.filter-group,
.select-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
  align-items: center;
}

.filter-title {
  margin-right: 4px;
  color: var(--color-muted);
  font-size: 0.72rem;
  font-weight: 800;
}

.facility-filters button,
.select-filters select,
.clear-filter {
  min-height: 36px;
  padding: 7px 14px;
  color: var(--color-primary-deep);
  font-size: 0.72rem;
  font-weight: 700;
  background: white;
  border: 1px solid var(--color-border);
  border-radius: 999px;
}

.facility-filters button.selected {
  color: white;
  background: var(--color-primary-deep);
  border-color: var(--color-primary-deep);
}

.select-filters select { padding-right: 28px; }
.clear-filter { color: var(--color-accent-deep); background: transparent; }

.results-heading {
  align-items: flex-end;
  padding: 28px 0 20px;
}

.results-heading p { margin: 0 0 6px; }

.results-heading > div > p {
  color: var(--color-primary-soft);
  font-size: 0.62rem;
  font-weight: 900;
  letter-spacing: 0.14em;
}

.results-heading h2 {
  display: inline;
  margin: 0;
  color: var(--color-primary-deep);
  font-family: 'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', serif;
  font-size: clamp(1.45rem, 2.6vw, 2.15rem);
}

.results-heading > div > span {
  margin-left: 12px;
  color: var(--color-muted);
  font-size: 0.68rem;
}

.results-heading .trip-summary {
  color: var(--color-muted);
  font-size: 0.7rem;
}

.results-actions { text-align: right; }
.comparison-shortcut {
  display: inline-block;
  margin-top: 8px;
  color: var(--color-accent-deep);
  font-size: 0.72rem;
  font-weight: 800;
  text-decoration: none;
}

.favorite-message {
  display: flex;
  gap: 14px;
  align-items: center;
  padding: 12px 15px;
  margin: -6px 0 18px;
  color: var(--color-primary-deep);
  font-size: 0.76rem;
  background: var(--color-surface-tint);
  border: 1px solid rgb(46 111 149 / 18%);
  border-radius: 10px;
}

.favorite-message--success { background: rgb(221 236 232 / 72%); }
.favorite-message--error { color: var(--color-danger); background: rgb(255 240 237 / 92%); }
.favorite-message a { margin-left: auto; color: var(--color-primary); font-weight: 800; }
.favorite-message button {
  padding: 0;
  color: currentcolor;
  font-size: 1.2rem;
  line-height: 1;
  background: transparent;
  border: 0;
}

.listing-list,
.skeleton-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}

.skeleton-card {
  display: grid;
  grid-template-rows: 220px 60px 34px;
  gap: 15px;
  padding-bottom: 20px;
  overflow: hidden;
  background: white;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
}

.skeleton-card span,
.skeleton-card i {
  display: block;
  background: linear-gradient(100deg, rgb(221 236 232 / 45%) 20%, white 45%, rgb(221 236 232 / 45%) 70%) 0 0 / 250% 100%;
  animation: shimmer 1.5s infinite linear;
}

.skeleton-card i { width: 75%; margin-left: 20px; border-radius: 8px; }
.skeleton-card i:last-child { width: 52%; }

.result-state {
  display: grid;
  min-height: 330px;
  padding: 40px;
  text-align: center;
  background: white;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-card);
  place-content: center;
}

.result-state > span { color: var(--color-accent); font: 3rem Georgia, serif; }
.result-state h2 { margin: 10px 0 7px; color: var(--color-primary-deep); font-family: 'Noto Serif SC', serif; }
.result-state p { max-width: 530px; margin: 0; color: var(--color-muted); line-height: 1.7; }
.result-state button { width: fit-content; padding: 10px 16px; margin: 20px auto 0; color: white; font-weight: 700; background: var(--color-primary); border: 0; border-radius: 8px; }

.trust-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 24px 30px;
  margin-top: 24px;
  background: linear-gradient(90deg, var(--color-surface-tint), #f8fcfb 68%, rgb(244 232 208 / 42%));
  border: 1px solid rgb(46 111 149 / 10%);
  border-radius: 13px;
}

.trust-strip > div { display: flex; gap: 12px; align-items: center; }
.trust-strip > div > span { display: grid; width: 38px; height: 38px; color: var(--color-primary); font-size: 1.25rem; border: 1px solid rgb(46 111 149 / 22%); border-radius: 50%; place-items: center; }
.trust-strip p { display: flex; flex-direction: column; gap: 3px; margin: 0; }
.trust-strip strong { color: var(--color-primary-deep); font-size: 0.76rem; }
.trust-strip small { color: var(--color-muted); font-size: 0.64rem; }

.site-footer {
  gap: 20px;
  padding: 28px 0 38px;
  border-top: 1px solid var(--color-border);
}

.site-footer strong { color: var(--color-primary-deep); font-family: Georgia, serif; font-size: 1.15rem; }
.site-footer p,
.site-footer a { color: var(--color-muted); font-size: 0.68rem; text-decoration: none; }

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

@keyframes shimmer { to { background-position: -250% 0; } }

@media (max-width: 1120px) {
  .site-header { grid-template-columns: auto 1fr auto; }
  nav { justify-content: center; gap: 22px; }
  nav a:nth-last-child(-n + 2) { display: none; }
  .search-console { grid-template-columns: 1.2fr 1fr 1fr; width: min(900px, calc(100% - 56px)); }
  .search-console label:nth-of-type(3) { border-right: 0; }
  .search-console label:nth-of-type(4) { border-top: 1px solid var(--color-border); }
  .search-button { grid-column: 2 / -1; min-height: 56px; margin-top: 8px; }
  .hero-shell { margin-bottom: 132px; }
}

@media (max-width: 900px) {
  .site-header,
  .results-section,
  .site-footer,
  .hero-content { width: min(100% - 36px, 760px); }
  .site-header { min-height: 68px; }
  nav { height: 68px; }
  .header-actions a:first-child { display: none; }
  .listing-list,
  .skeleton-list { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .filter-bar { align-items: flex-start; flex-direction: column; }
  .select-filters { width: 100%; }
  .trust-strip { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 680px) {
  .site-header { grid-template-columns: 1fr auto; }
  .brand { font-size: 1.65rem; }
  nav { display: none; }
  .hero-shell { min-height: 500px; margin-bottom: 190px; }
  .hero-overlay {
    background:
      linear-gradient(90deg, rgb(232 244 250 / 89%), rgb(208 231 244 / 38%)),
      linear-gradient(rgb(104 170 207 / 5%), rgb(48 126 176 / 9%));
  }

  .hero-shell::before { background-position: 38% 54%; }
  .hero-content { padding-top: 48px; }
  .hero-content h1 {
    max-width: 350px;
    font-size: clamp(2.25rem, 10.5vw, 3.15rem);
    line-height: 1.2;
    overflow-wrap: anywhere;
  }
  .hero-content > p:last-child { max-width: 300px; font-size: 0.86rem; line-height: 1.7; }
  .search-console { bottom: -152px; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); width: calc(100% - 28px); padding: 8px; }
  .search-console label { padding: 12px; border-bottom: 1px solid var(--color-border); }
  .search-console .destination-field { grid-column: 1 / -1; border-right: 0; }
  .search-console label:nth-of-type(3) { border-right: 0; }
  .search-console label:nth-of-type(4) { border-bottom: 0; }
  .search-console label:nth-of-type(2),
  .search-console label:nth-of-type(3) { gap: 7px; padding-right: 8px; padding-left: 8px; overflow: hidden; }
  .search-console label:nth-of-type(2) > svg,
  .search-console label:nth-of-type(3) > svg { display: none; }
  .search-console input[type='date'] { font-size: 0.72rem; }
  .search-button { grid-row: 3; grid-column: 2; min-width: 0; min-height: 58px; margin: 8px 0 0 8px; }
  .listing-list,
  .skeleton-list { grid-template-columns: 1fr; }
  .results-heading { align-items: flex-start; flex-direction: column; gap: 10px; }
  .results-heading > div > span { display: block; margin: 7px 0 0; }
  .results-heading .trip-summary { order: -1; }
  .facility-filters { width: 100%; overflow-x: auto; flex-wrap: nowrap; padding-bottom: 4px; }
  .facility-filters button { flex: 0 0 auto; }
  .select-filters { display: grid; grid-template-columns: 1fr 1fr; }
  .select-filters label:last-of-type { grid-column: 1 / -1; }
  .select-filters select { width: 100%; }
  .trust-strip { grid-template-columns: 1fr; }
  .site-footer { align-items: flex-start; flex-direction: column; }
}
</style>
