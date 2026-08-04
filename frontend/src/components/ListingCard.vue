<script setup lang="ts">
import { computed } from 'vue'
import type { ListingSummary } from '../types/listings'
import { formatCurrency } from '../utils/format'

const props = defineProps<{
  listing: ListingSummary
  nights: number
  index: number
  favorite: boolean
  favoritePending?: boolean
  compared: boolean
}>()

defineEmits<{
  compare: [listing: ListingSummary]
  toggleFavorite: [listing: ListingSummary]
  toggleComparison: [listing: ListingSummary]
}>()

const imageUrl = computed(() => `/images/stays/stay-${String((props.index % 3) + 1).padStart(2, '0')}.jpg`)
const visibleFacilities = computed(() => props.listing.facilities.slice(0, 4))
const nightlyAmount = computed(() => {
  const total = Number(props.listing.lowest_total_amount)
  return Number.isFinite(total) ? total / Math.max(props.nights, 1) : 0
})
const freshnessLabel = computed(() => props.listing.freshness_status === 'fresh'
  ? `价格已更新 · ${props.listing.age_minutes} 分钟前`
  : `价格可能已变动 · ${props.listing.age_minutes} 分钟前`)
</script>

<template>
  <article class="listing-card" :style="{ '--delay': `${index * 90}ms` }">
    <div class="listing-visual">
      <img :src="imageUrl" :alt="`${listing.name}住宿环境`" />
      <span class="visual-rank">{{ index + 1 }}</span>
      <button
        class="favorite-button"
        :class="{ selected: favorite }"
        type="button"
        :aria-label="`${favorite ? '取消收藏' : '收藏'} ${listing.name}`"
        :aria-pressed="favorite"
        :aria-busy="favoritePending || undefined"
        :disabled="favoritePending"
        @click.stop="$emit('toggleFavorite', listing)"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1.1L12 21l7.8-7.5 1.1-1.1a5.5 5.5 0 0 0-.1-7.8Z" /></svg>
      </button>
      <span class="rating-chip">{{ listing.best_rating ?? '新上架' }}</span>
    </div>

    <div class="listing-copy">
      <div class="title-row">
        <div>
          <p class="listing-address">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s7-6 7-12a7 7 0 1 0-14 0c0 6 7 12 7 12Zm0-9a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z" /></svg>
            {{ listing.city }} · {{ listing.district }}
          </p>
          <h2>{{ listing.name }}</h2>
        </div>
        <span class="score-copy">{{ listing.offer_count }} 条报价</span>
      </div>

      <p class="listing-summary">{{ listing.summary || '多平台房源已完成标准化，可直接查看总价与优惠条件。' }}</p>

      <div class="facility-row" aria-label="民宿设施">
        <span v-for="facility in visibleFacilities" :key="facility.code">{{ facility.name }}</span>
        <span v-if="listing.facilities.length > visibleFacilities.length">
          +{{ listing.facilities.length - visibleFacilities.length }} 项
        </span>
      </div>
    </div>

    <div class="listing-price">
      <div class="coverage">
        <span>跨平台价格对比</span>
        <strong>{{ listing.platform_count }} 个平台</strong>
      </div>
      <div class="price-copy">
        <span>约 {{ formatCurrency(nightlyAmount, listing.currency) }} / 晚</span>
        <strong>{{ formatCurrency(listing.lowest_total_amount, listing.currency) }}</strong>
        <small>{{ nights }} 晚最低总价</small>
      </div>
      <p class="freshness-badge" :class="`freshness-badge--${listing.freshness_status}`">{{ freshnessLabel }}</p>
      <div class="card-actions">
        <button
          class="compare-list-button"
          :class="{ selected: compared }"
          type="button"
          :aria-label="`${compared ? '移出' : '加入'}比较清单 ${listing.name}`"
          :aria-pressed="compared"
          @click="$emit('toggleComparison', listing)"
        >
          {{ compared ? '已加入比较' : '加入比较' }}
        </button>
        <button class="offer-button" type="button" :aria-label="`查看 ${listing.name} 的平台报价`" @click="$emit('compare', listing)">
          查看平台报价
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 14 0m-5-5 5 5-5 5" /></svg>
        </button>
      </div>
    </div>
  </article>
</template>

<style scoped>
.listing-card {
  display: grid;
  grid-template-rows: 220px auto auto;
  min-width: 0;
  overflow: hidden;
  background: rgb(255 255 255 / 96%);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  box-shadow: 0 12px 34px rgb(22 50 79 / 8%);
  opacity: 0;
  animation: card-in 520ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: var(--delay);
  transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
}

.listing-card:hover {
  border-color: rgb(46 111 149 / 35%);
  box-shadow: 0 24px 48px rgb(22 50 79 / 13%);
  transform: translateY(-4px);
}

.listing-visual {
  position: relative;
  overflow: hidden;
  background: var(--color-seafoam);
}

.listing-visual::after {
  position: absolute;
  inset: 45% 0 0;
  content: '';
  background: linear-gradient(transparent, rgb(10 28 47 / 55%));
  pointer-events: none;
}

.listing-visual img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 600ms cubic-bezier(0.22, 1, 0.36, 1);
}

.listing-card:hover .listing-visual img {
  transform: scale(1.045);
}

.visual-rank,
.rating-chip,
.favorite-button {
  position: absolute;
  z-index: 1;
}

.visual-rank {
  top: 0;
  left: 0;
  display: grid;
  width: 48px;
  height: 44px;
  color: white;
  font-family: Georgia, serif;
  font-size: 1.15rem;
  background: var(--color-primary-deep);
  border-radius: 0 0 13px;
  place-items: center;
}

.favorite-button {
  top: 14px;
  right: 14px;
  display: grid;
  width: 38px;
  height: 38px;
  padding: 0;
  color: white;
  background: rgb(22 50 79 / 18%);
  border: 1px solid rgb(255 255 255 / 65%);
  border-radius: 50%;
  backdrop-filter: blur(8px);
  place-items: center;
}

.favorite-button svg {
  width: 18px;
  fill: none;
  stroke: currentcolor;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.favorite-button.selected {
  color: white;
  background: var(--color-accent);
  border-color: rgb(255 255 255 / 82%);
  box-shadow: 0 6px 16px rgb(22 50 79 / 24%);
}

.favorite-button.selected svg { fill: currentcolor; }
.favorite-button:disabled { cursor: wait; opacity: 0.72; }

.rating-chip {
  right: 14px;
  bottom: 13px;
  padding: 6px 9px;
  color: white;
  font-size: 0.72rem;
  font-weight: 800;
  background: var(--color-primary-soft);
  border-radius: 7px;
}

.listing-copy {
  padding: 21px 20px 18px;
}

.title-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  justify-content: space-between;
}

.listing-address {
  display: flex;
  gap: 5px;
  align-items: center;
  margin: 0 0 7px;
  color: var(--color-muted);
  font-size: 0.7rem;
}

.listing-address svg {
  width: 13px;
  color: var(--color-primary-soft);
  fill: currentcolor;
}

h2 {
  margin: 0;
  color: var(--color-primary-deep);
  font-family: 'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', serif;
  font-size: 1.2rem;
  font-weight: 700;
  line-height: 1.35;
}

.score-copy {
  flex: 0 0 auto;
  margin-top: 26px;
  color: var(--color-primary-soft);
  font-size: 0.65rem;
  font-weight: 800;
}

.listing-summary {
  display: -webkit-box;
  min-height: 42px;
  margin: 12px 0 14px;
  overflow: hidden;
  color: var(--color-muted);
  font-size: 0.76rem;
  line-height: 1.65;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.facility-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.facility-row span {
  padding: 5px 8px;
  color: var(--color-primary);
  font-size: 0.65rem;
  font-weight: 700;
  background: rgb(221 236 232 / 65%);
  border-radius: 6px;
}

.listing-price {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 14px;
  align-items: end;
  padding: 17px 20px 20px;
  border-top: 1px solid var(--color-border);
}

.coverage {
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: var(--color-muted);
  font-size: 0.66rem;
}

.coverage strong {
  color: var(--color-primary-deep);
  font-size: 0.8rem;
}

.price-copy {
  text-align: right;
}

.price-copy span,
.price-copy small {
  display: block;
  color: var(--color-muted);
  font-size: 0.62rem;
}

.price-copy strong {
  display: block;
  margin: 3px 0;
  color: var(--color-accent);
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 1.45rem;
  font-weight: 700;
}

.card-actions {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: 0.82fr 1.18fr;
  gap: 8px;
}

.freshness-badge { grid-column: 1 / -1; margin: 0; padding: 7px 9px; color: #276557; font-size: .64rem; font-weight: 800; background: rgb(39 101 87 / 8%); border-radius: 7px; }
.freshness-badge--stale { color: #a44831; background: rgb(180 95 53 / 11%); }

.card-actions button {
  display: flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 11px 14px;
  color: var(--color-accent-deep);
  font-size: 0.76rem;
  font-weight: 800;
  background: transparent;
  border: 1px solid rgb(226 109 90 / 65%);
  border-radius: 9px;
  transition: color 180ms ease, background 180ms ease, transform 180ms ease;
}

.card-actions .offer-button:hover {
  color: white;
  background: var(--color-accent);
  transform: translateY(-1px);
}

.card-actions button svg {
  width: 16px;
  fill: none;
  stroke: currentcolor;
  stroke-linecap: round;
  stroke-width: 1.8;
}

.card-actions .compare-list-button {
  color: var(--color-primary);
  border-color: rgb(46 111 149 / 42%);
}

.card-actions .compare-list-button:hover,
.card-actions .compare-list-button.selected {
  color: white;
  background: var(--color-primary);
  border-color: var(--color-primary);
}

@keyframes card-in {
  from { opacity: 0; transform: translateY(18px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 980px) {
  .listing-card {
    grid-template-rows: 210px auto auto;
  }
}

@media (max-width: 680px) {
  .listing-card {
    grid-template-rows: 230px auto auto;
  }
}
</style>
