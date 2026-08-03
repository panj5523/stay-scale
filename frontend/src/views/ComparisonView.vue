<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  MAX_COMPARISONS,
  clearComparisons,
  getComparisons,
  removeComparison,
  type ComparisonEntry,
} from '../comparison/comparisonStorage'
import { formatCurrency, formatShortDate, stayNights } from '../utils/format'

const entries = ref(getComparisons())

const bestPriceId = computed(() => {
  if (!entries.value.length) return ''
  return entries.value.reduce((best, entry) =>
    Number(entry.listing.lowest_total_amount) < Number(best.listing.lowest_total_amount)
      ? entry
      : best,
  ).listing.public_id
})

function imageUrl(index: number): string {
  return `/images/stays/stay-${String((index % 3) + 1).padStart(2, '0')}.jpg`
}

function nights(entry: ComparisonEntry): number {
  return stayNights(entry.search.checkIn, entry.search.checkOut)
}

function nightlyPrice(entry: ComparisonEntry): number {
  return Number(entry.listing.lowest_total_amount) / Math.max(nights(entry), 1)
}

function remove(publicId: string) {
  entries.value = removeComparison(publicId)
}

function clearAll() {
  clearComparisons()
  entries.value = []
}
</script>

<template>
  <main class="comparison-page">
    <header class="comparison-header">
      <RouterLink class="brand" to="/">Stay Scale</RouterLink>
      <nav aria-label="比较页导航">
        <RouterLink to="/">返回首页</RouterLink>
        <RouterLink to="/account">收藏夹</RouterLink>
        <span>我的比较</span>
      </nav>
    </header>

    <section class="comparison-hero">
      <div>
        <p>STAY SIDE BY SIDE</p>
        <h1>把合适的住处<br />放在一起看</h1>
        <span>比较总价、评分、平台覆盖和设施，最多同时保留 {{ MAX_COMPARISONS }} 家。</span>
      </div>
      <strong>{{ entries.length }}<small>/{{ MAX_COMPARISONS }}</small></strong>
    </section>

    <section v-if="!entries.length" class="empty-comparison">
      <span>◇</span>
      <h2>比较清单还是空的</h2>
      <p>返回首页，在感兴趣的房源卡片中点击“加入比较”。</p>
      <RouterLink to="/">去挑选民宿</RouterLink>
    </section>

    <section v-else class="comparison-content">
      <div class="section-heading">
        <div>
          <p>YOUR SHORTLIST</p>
          <h2>候选民宿对照</h2>
        </div>
        <button type="button" @click="clearAll">清空比较</button>
      </div>

      <div
        class="comparison-grid"
        :class="{ full: entries.length === MAX_COMPARISONS }"
        :style="{ '--column-count': entries.length }"
      >
        <article v-for="(entry, index) in entries" :key="entry.listing.public_id">
          <div class="stay-image">
            <img :src="imageUrl(index)" :alt="`${entry.listing.name}住宿环境`" />
            <span v-if="entry.listing.public_id === bestPriceId">当前低价</span>
            <button type="button" :aria-label="`移出比较 ${entry.listing.name}`" @click="remove(entry.listing.public_id)">×</button>
          </div>
          <div class="stay-title">
            <small>{{ entry.listing.city }} · {{ entry.listing.district }}</small>
            <h3>{{ entry.listing.name }}</h3>
            <p>{{ formatShortDate(entry.search.checkIn) }} — {{ formatShortDate(entry.search.checkOut) }} · {{ nights(entry) }} 晚</p>
          </div>
          <dl>
            <div>
              <dt>最低总价</dt>
              <dd class="price">{{ formatCurrency(entry.listing.lowest_total_amount, entry.listing.currency) }}</dd>
            </div>
            <div>
              <dt>每晚约</dt>
              <dd>{{ formatCurrency(nightlyPrice(entry), entry.listing.currency) }}</dd>
            </div>
            <div>
              <dt>住客评分</dt>
              <dd>{{ entry.listing.best_rating ?? '暂无' }}</dd>
            </div>
            <div>
              <dt>报价覆盖</dt>
              <dd>{{ entry.listing.platform_count }} 个平台 · {{ entry.listing.offer_count }} 条报价</dd>
            </div>
            <div class="facilities">
              <dt>主要设施</dt>
              <dd>
                <span v-for="facility in entry.listing.facilities.slice(0, 5)" :key="facility.code">{{ facility.name }}</span>
                <em v-if="!entry.listing.facilities.length">暂无设施信息</em>
              </dd>
            </div>
          </dl>
          <RouterLink class="search-again" :to="{ path: '/', hash: '#results' }">返回首页查看报价</RouterLink>
        </article>

        <RouterLink v-if="entries.length < MAX_COMPARISONS" class="add-column" to="/#results">
          <span>＋</span>
          <strong>再加入一家</strong>
          <small>让差异更直观</small>
        </RouterLink>
      </div>
    </section>
  </main>
</template>

<style scoped>
.comparison-page {
  min-height: 100vh;
  color: var(--color-ink);
  background:
    radial-gradient(circle at 92% 4%, rgb(123 184 216 / 22%), transparent 27rem),
    linear-gradient(180deg, #f3f9fc 0, #fffdf8 38rem);
}

.comparison-header,
.comparison-hero,
.comparison-content,
.empty-comparison {
  width: min(1240px, calc(100% - 64px));
  margin-right: auto;
  margin-left: auto;
}

.comparison-header {
  display: flex;
  min-height: 76px;
  align-items: center;
  justify-content: space-between;
}

.brand {
  color: var(--color-primary-deep);
  font: 700 2rem Georgia, serif;
  letter-spacing: -0.04em;
  text-decoration: none;
}

nav { display: flex; gap: 28px; align-items: center; }
nav a, nav span { color: var(--color-muted); font-size: 0.8rem; text-decoration: none; }
nav span { color: var(--color-primary); font-weight: 800; }

.comparison-hero {
  display: flex;
  min-height: 300px;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid rgb(46 111 149 / 12%);
}

.comparison-hero p,
.section-heading p {
  margin: 0 0 13px;
  color: var(--color-accent-deep);
  font-size: 0.67rem;
  font-weight: 900;
  letter-spacing: 0.17em;
}

.comparison-hero h1 {
  margin: 0 0 18px;
  color: var(--color-primary-deep);
  font-family: 'Noto Serif SC', 'Songti SC', serif;
  font-size: clamp(2.5rem, 5vw, 4.8rem);
  line-height: 1.12;
  letter-spacing: -0.05em;
}

.comparison-hero > div > span { color: var(--color-muted); font-size: 0.86rem; }
.comparison-hero > strong {
  display: flex;
  width: 150px;
  height: 150px;
  align-items: baseline;
  justify-content: center;
  color: white;
  font: 700 4.5rem Georgia, serif;
  background: linear-gradient(145deg, var(--color-primary), var(--color-primary-deep));
  border: 8px solid rgb(255 255 255 / 70%);
  border-radius: 50%;
  box-shadow: 0 24px 55px rgb(22 50 79 / 20%);
}
.comparison-hero > strong small { font-size: 1.1rem; opacity: 0.68; }

.comparison-content { padding: 35px 0 80px; }
.section-heading { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 20px; }
.section-heading h2 { margin: 0; color: var(--color-primary-deep); font-family: 'Noto Serif SC', serif; font-size: 1.8rem; }
.section-heading button { padding: 8px 13px; color: var(--color-accent-deep); background: transparent; border: 1px solid rgb(226 109 90 / 35%); border-radius: 8px; }

.comparison-grid {
  display: grid;
  grid-template-columns: repeat(var(--column-count), minmax(0, 1fr)) minmax(150px, 0.46fr);
  gap: 15px;
  align-items: stretch;
}

.comparison-grid.full { grid-template-columns: repeat(var(--column-count), minmax(0, 1fr)); }

.comparison-grid article,
.add-column {
  overflow: hidden;
  background: rgb(255 255 255 / 94%);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  box-shadow: 0 16px 40px rgb(22 50 79 / 8%);
}

.stay-image { position: relative; height: 190px; overflow: hidden; }
.stay-image img { width: 100%; height: 100%; object-fit: cover; }
.stay-image > span { position: absolute; bottom: 12px; left: 12px; padding: 6px 9px; color: white; font-size: 0.65rem; font-weight: 800; background: var(--color-accent); border-radius: 6px; }
.stay-image button { position: absolute; top: 12px; right: 12px; display: grid; width: 32px; height: 32px; padding: 0; color: white; font-size: 1.15rem; background: rgb(10 28 47 / 45%); border: 1px solid rgb(255 255 255 / 55%); border-radius: 50%; backdrop-filter: blur(8px); place-items: center; }

.stay-title { min-height: 145px; padding: 20px 18px; border-bottom: 1px solid var(--color-border); }
.stay-title small { color: var(--color-primary-soft); font-size: 0.68rem; font-weight: 800; }
.stay-title h3 { margin: 8px 0 13px; color: var(--color-primary-deep); font-family: 'Noto Serif SC', serif; font-size: 1.1rem; line-height: 1.45; }
.stay-title p { margin: 0; color: var(--color-muted); font-size: 0.68rem; }

dl { margin: 0; padding: 4px 18px; }
dl > div { display: flex; min-height: 56px; gap: 12px; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--color-border); }
dt { color: var(--color-muted); font-size: 0.67rem; }
dd { margin: 0; color: var(--color-primary-deep); font-size: 0.75rem; font-weight: 800; text-align: right; }
dd.price { color: var(--color-accent-deep); font: 700 1.35rem Georgia, serif; }
.facilities { align-items: flex-start; flex-direction: column; padding: 15px 0; }
.facilities dd { display: flex; flex-wrap: wrap; gap: 5px; text-align: left; }
.facilities span { padding: 4px 7px; color: var(--color-primary); font-size: 0.62rem; background: var(--color-surface-tint); border-radius: 5px; }
.facilities em { color: var(--color-muted); font-size: 0.67rem; font-style: normal; }
.search-again { display: block; padding: 16px 18px 19px; color: var(--color-accent-deep); font-size: 0.72rem; font-weight: 800; text-align: center; text-decoration: none; }

.add-column { display: flex; min-height: 540px; align-items: center; justify-content: center; flex-direction: column; color: var(--color-primary); text-decoration: none; border-style: dashed; box-shadow: none; }
.add-column span { display: grid; width: 48px; height: 48px; margin-bottom: 12px; font-size: 1.6rem; border: 1px solid rgb(46 111 149 / 30%); border-radius: 50%; place-items: center; }
.add-column strong { font-size: 0.82rem; }
.add-column small { margin-top: 5px; color: var(--color-muted); font-size: 0.65rem; }

.empty-comparison { display: grid; min-height: 420px; text-align: center; place-content: center; }
.empty-comparison > span { color: var(--color-primary-soft); font: 4rem Georgia, serif; }
.empty-comparison h2 { margin: 8px 0; color: var(--color-primary-deep); font-family: 'Noto Serif SC', serif; font-size: 1.8rem; }
.empty-comparison p { margin: 0 0 22px; color: var(--color-muted); }
.empty-comparison a { width: fit-content; padding: 11px 18px; margin: auto; color: white; font-weight: 800; text-decoration: none; background: var(--color-primary); border-radius: 8px; }

@media (max-width: 900px) {
  .comparison-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .comparison-hero > strong { width: 110px; height: 110px; font-size: 3.2rem; }
  .add-column { min-height: 260px; }
}

@media (max-width: 620px) {
  .comparison-header, .comparison-hero, .comparison-content, .empty-comparison { width: calc(100% - 32px); }
  nav a:nth-child(2) { display: none; }
  .comparison-hero { min-height: 340px; }
  .comparison-hero > strong { display: none; }
  .comparison-grid { grid-template-columns: 1fr; }
  .section-heading { align-items: flex-start; flex-direction: column; gap: 15px; }
}
</style>
