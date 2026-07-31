<script setup lang="ts">
import { computed } from 'vue'
import type { ListingSummary } from '../types/listings'
import { formatCurrency } from '../utils/format'

const props = defineProps<{
  listing: ListingSummary
  nights: number
  index: number
}>()

defineEmits<{
  compare: [listing: ListingSummary]
}>()

const visualClass = computed(() => `visual-${(props.index % 3) + 1}`)
const visibleFacilities = computed(() => props.listing.facilities.slice(0, 4))
</script>

<template>
  <article class="listing-card" :style="{ '--delay': `${index * 90}ms` }">
    <div class="listing-visual" :class="visualClass" aria-hidden="true">
      <span class="sun"></span>
      <span class="mountain mountain-back"></span>
      <span class="mountain mountain-front"></span>
      <span class="house"><i></i></span>
      <span class="visual-index">0{{ index + 1 }}</span>
      <span class="visual-location">{{ listing.district }}</span>
    </div>

    <div class="listing-copy">
      <div class="listing-meta">
        <span v-if="listing.best_rating" class="rating">★ {{ listing.best_rating }}</span>
        <span>{{ listing.platform_count }} 个平台</span>
        <span>{{ listing.offer_count }} 条报价</span>
      </div>

      <div>
        <p class="listing-address">{{ listing.city }} · {{ listing.district }}</p>
        <h2>{{ listing.name }}</h2>
        <p class="listing-summary">{{ listing.summary }}</p>
      </div>

      <div class="facility-row" aria-label="民宿设施">
        <span v-for="facility in visibleFacilities" :key="facility.code">
          {{ facility.name }}
        </span>
        <span v-if="listing.facilities.length > visibleFacilities.length">
          +{{ listing.facilities.length - visibleFacilities.length }}
        </span>
      </div>
    </div>

    <div class="listing-price">
      <p>当前最低总价</p>
      <strong>{{ formatCurrency(listing.lowest_total_amount, listing.currency) }}</strong>
      <span>{{ nights }} 晚 · 已含平台费用</span>
      <button type="button" :aria-label="`比较 ${listing.name} 的平台报价`" @click="$emit('compare', listing)">
        比较平台报价
        <span aria-hidden="true">↗</span>
      </button>
    </div>
  </article>
</template>

<style scoped>
.listing-card {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) 190px;
  min-height: 230px;
  overflow: hidden;
  background: rgb(255 252 246 / 88%);
  border: 1px solid var(--color-border);
  border-radius: 22px;
  box-shadow: 0 12px 40px rgb(31 58 51 / 6%);
  opacity: 0;
  animation: card-in 520ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: var(--delay);
}

.listing-visual {
  position: relative;
  min-height: 230px;
  overflow: hidden;
  background: #b8d3ca;
}

.visual-2 {
  background: #d7c9a9;
}

.visual-3 {
  background: #9dc8cf;
}

.sun {
  position: absolute;
  top: 30px;
  right: 36px;
  width: 46px;
  height: 46px;
  background: #efab69;
  border-radius: 50%;
  box-shadow: 0 0 0 14px rgb(255 252 246 / 14%);
}

.mountain {
  position: absolute;
  bottom: -65px;
  left: -30px;
  width: 240px;
  height: 190px;
  background: #527e72;
  border-radius: 48% 52% 0 0;
  transform: rotate(17deg);
}

.mountain-back {
  right: -80px;
  bottom: -90px;
  left: auto;
  width: 270px;
  background: rgb(255 252 246 / 35%);
  transform: rotate(-21deg);
}

.visual-2 .mountain {
  background: #91765a;
}

.visual-3 .mountain {
  background: #387b84;
}

.house {
  position: absolute;
  bottom: 37px;
  left: 74px;
  width: 96px;
  height: 64px;
  background: #fff8e9;
  box-shadow: 0 10px 24px rgb(25 70 63 / 18%);
}

.house::before {
  position: absolute;
  top: -32px;
  left: -10px;
  width: 0;
  height: 0;
  content: '';
  border-right: 58px solid transparent;
  border-bottom: 34px solid #bd6542;
  border-left: 58px solid transparent;
}

.house i {
  position: absolute;
  bottom: 0;
  left: 37px;
  width: 22px;
  height: 39px;
  background: #2f665d;
}

.visual-index,
.visual-location {
  position: absolute;
  z-index: 2;
  color: rgb(255 252 246 / 88%);
  font-weight: 800;
}

.visual-index {
  top: 18px;
  left: 20px;
  font-family: Georgia, serif;
  font-size: 1.25rem;
}

.visual-location {
  right: 18px;
  bottom: 14px;
  padding: 5px 9px;
  font-size: 0.7rem;
  letter-spacing: 0.08em;
  background: rgb(25 70 63 / 62%);
  border-radius: 999px;
}

.listing-copy {
  display: flex;
  flex-direction: column;
  gap: 20px;
  justify-content: space-between;
  padding: 26px 28px;
}

.listing-meta,
.facility-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.listing-meta {
  color: var(--color-muted);
  font-size: 0.76rem;
}

.listing-meta span:not(:last-child)::after {
  margin-left: 8px;
  content: '·';
}

.listing-meta .rating {
  color: #a65533;
  font-weight: 800;
}

.listing-address {
  margin: 0 0 8px;
  color: var(--color-accent);
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.08em;
}

h2 {
  margin: 0;
  color: var(--color-primary-deep);
  font-family: 'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', serif;
  font-size: clamp(1.35rem, 2vw, 1.75rem);
  font-weight: 600;
}

.listing-summary {
  display: -webkit-box;
  max-width: 580px;
  margin: 10px 0 0;
  overflow: hidden;
  color: var(--color-muted);
  font-size: 0.88rem;
  line-height: 1.65;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.facility-row span {
  padding: 5px 9px;
  color: var(--color-primary);
  font-size: 0.7rem;
  font-weight: 700;
  background: rgb(36 90 80 / 7%);
  border-radius: 999px;
}

.listing-price {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: center;
  padding: 26px;
  text-align: right;
  border-left: 1px dashed var(--color-border);
}

.listing-price p,
.listing-price span {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.72rem;
}

.listing-price strong {
  margin: 7px 0 3px;
  color: var(--color-primary-deep);
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 2rem;
  font-weight: 500;
}

.listing-price button {
  display: inline-flex;
  gap: 12px;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 12px 14px;
  margin-top: 24px;
  color: var(--color-surface);
  font-size: 0.82rem;
  font-weight: 800;
  background: var(--color-primary);
  border: 0;
  border-radius: 10px;
  transition: transform 180ms ease, background 180ms ease;
}

.listing-price button:hover {
  background: var(--color-primary-deep);
  transform: translateY(-2px);
}

@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 860px) {
  .listing-card {
    grid-template-columns: 180px minmax(0, 1fr);
  }

  .listing-price {
    grid-column: 1 / -1;
    flex-flow: row wrap;
    gap: 8px 14px;
    align-items: baseline;
    justify-content: flex-end;
    padding: 18px 22px;
    border-top: 1px dashed var(--color-border);
    border-left: 0;
  }

  .listing-price button {
    width: auto;
    margin: 0 0 0 auto;
  }
}

@media (max-width: 600px) {
  .listing-card {
    display: block;
  }

  .listing-visual {
    min-height: 190px;
  }

  .listing-copy {
    padding: 22px;
  }

  .listing-price {
    display: grid;
    grid-template-columns: 1fr auto;
    text-align: left;
  }

  .listing-price p,
  .listing-price strong {
    align-self: end;
  }

  .listing-price span {
    grid-column: 1;
  }

  .listing-price button {
    grid-row: 1 / 3;
    grid-column: 2;
    align-self: center;
  }
}
</style>
