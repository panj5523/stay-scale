<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import type { ListingDetail } from '../types/listings'
import { formatCurrency, formatShortDate, stayNights } from '../utils/format'

const props = defineProps<{
  detail: ListingDetail | null
  loading: boolean
  error: string
  checkIn: string
  checkOut: string
}>()

const emit = defineEmits<{
  close: []
}>()

const nights = computed(() => stayNights(props.checkIn, props.checkOut))

function closeOnEscape(event: KeyboardEvent) {
  if (event.key === 'Escape') emit('close')
}

onMounted(() => {
  document.body.classList.add('drawer-open')
  window.addEventListener('keydown', closeOnEscape)
})

onBeforeUnmount(() => {
  document.body.classList.remove('drawer-open')
  window.removeEventListener('keydown', closeOnEscape)
})
</script>

<template>
  <div class="drawer-shell" role="presentation" @mousedown.self="$emit('close')">
    <section class="offer-drawer" role="dialog" aria-modal="true" aria-labelledby="offer-title">
      <header class="drawer-header">
        <div>
          <p class="drawer-kicker">Across the platforms</p>
          <h2 id="offer-title">{{ detail?.name ?? '正在整理平台报价' }}</h2>
          <p v-if="detail" class="stay-line">
            {{ formatShortDate(checkIn) }} — {{ formatShortDate(checkOut) }} · {{ nights }} 晚
          </p>
        </div>
        <button class="close-button" type="button" aria-label="关闭报价详情" @click="$emit('close')">
          ×
        </button>
      </header>

      <div v-if="loading" class="drawer-state" aria-live="polite">
        <span class="loading-orbit"></span>
        <strong>正在对齐各平台价格</strong>
        <p>核对房型、费用和优惠条件…</p>
      </div>

      <div v-else-if="error" class="drawer-state error-state" role="alert">
        <strong>报价暂时没有加载出来</strong>
        <p>{{ error }}</p>
      </div>

      <template v-else-if="detail">
        <div class="drawer-intro">
          <div>
            <span>{{ detail.city }} · {{ detail.district }}</span>
            <p>{{ detail.address }}</p>
          </div>
          <span class="offer-count">{{ detail.offers.length }} 条可用报价</span>
        </div>

        <div v-if="detail.offers.length" class="offer-list">
          <article v-for="(offer, index) in detail.offers" :key="`${offer.platform_code}-${offer.room_external_id}-${offer.price_type}`" class="offer-card">
            <div class="offer-rank">{{ String(index + 1).padStart(2, '0') }}</div>
            <div class="platform-cell">
              <div class="platform-name">
                <span :class="`platform-mark mark-${offer.platform_code}`">
                  {{ offer.platform_name.slice(0, 1) }}
                </span>
                <div>
                  <strong>{{ offer.platform_name }}</strong>
                  <span v-if="index === 0" class="best-badge">当前最低</span>
                </div>
              </div>
              <p v-if="offer.rating">★ {{ offer.rating }} · {{ offer.review_count }} 条评价</p>
              <p v-else>暂无平台评分</p>
            </div>

            <div class="room-cell">
              <strong>{{ offer.room_name }}</strong>
              <p>{{ offer.bed_type }} · 最多 {{ offer.max_guests }} 人</p>
              <span v-if="offer.promotion_conditions" class="promotion">
                {{ offer.promotion_conditions }}
              </span>
              <span v-else class="policy">{{ offer.cancellation_policy }}</span>
            </div>

            <div class="breakdown-cell">
              <span>房费 {{ formatCurrency(offer.room_subtotal, offer.currency) }}</span>
              <span v-if="Number(offer.cleaning_fee)">清洁费 {{ formatCurrency(offer.cleaning_fee, offer.currency) }}</span>
              <span v-if="Number(offer.service_fee)">服务费 {{ formatCurrency(offer.service_fee, offer.currency) }}</span>
              <span v-if="Number(offer.discount_amount)" class="discount">优惠 -{{ formatCurrency(offer.discount_amount, offer.currency) }}</span>
            </div>

            <div class="total-cell">
              <span>{{ nights }} 晚总价</span>
              <strong>{{ formatCurrency(offer.total_amount, offer.currency) }}</strong>
              <small>{{ offer.price_type === 'standard' ? '标准价' : '含条件优惠' }}</small>
            </div>
          </article>
        </div>

        <div v-else class="drawer-state">
          <strong>当前条件下暂无报价</strong>
          <p>可以调整日期或入住人数后重新查询。</p>
        </div>

        <footer class="drawer-footer">
          <p>价格来自项目演示数据，实际预订前请以平台结算页为准。</p>
          <button type="button" @click="$emit('close')">返回搜索结果</button>
        </footer>
      </template>
    </section>
  </div>
</template>

<style scoped>
.drawer-shell {
  position: fixed;
  z-index: 50;
  inset: 0;
  display: flex;
  justify-content: flex-end;
  padding-left: 24px;
  background: rgb(20 36 32 / 48%);
  backdrop-filter: blur(5px);
  animation: veil-in 220ms ease-out;
}

.offer-drawer {
  width: min(980px, 92vw);
  height: 100%;
  overflow-y: auto;
  background:
    linear-gradient(90deg, rgb(36 90 80 / 5%) 1px, transparent 1px) 0 0 / 64px 64px,
    var(--color-surface);
  box-shadow: -24px 0 80px rgb(20 36 32 / 22%);
  animation: drawer-in 420ms cubic-bezier(0.22, 1, 0.36, 1);
}

.drawer-header {
  position: sticky;
  z-index: 3;
  top: 0;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 34px 42px 28px;
  background: rgb(255 252 246 / 92%);
  border-bottom: 1px solid var(--color-border);
  backdrop-filter: blur(15px);
}

.drawer-kicker {
  margin: 0 0 8px;
  color: var(--color-accent);
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.15em;
  text-transform: uppercase;
}

h2 {
  margin: 0;
  color: var(--color-primary-deep);
  font-family: 'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', serif;
  font-size: clamp(1.7rem, 3vw, 2.55rem);
  font-weight: 600;
}

.stay-line {
  margin: 9px 0 0;
  color: var(--color-muted);
  font-size: 0.82rem;
}

.close-button {
  width: 42px;
  height: 42px;
  color: var(--color-primary-deep);
  font-size: 1.8rem;
  line-height: 1;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 50%;
}

.close-button:hover {
  color: var(--color-surface);
  background: var(--color-primary);
}

.drawer-intro {
  display: flex;
  gap: 24px;
  align-items: center;
  justify-content: space-between;
  padding: 28px 42px;
}

.drawer-intro span {
  color: var(--color-primary);
  font-size: 0.76rem;
  font-weight: 800;
}

.drawer-intro p {
  margin: 6px 0 0;
  color: var(--color-muted);
  font-size: 0.84rem;
}

.offer-count {
  flex: 0 0 auto;
  padding: 7px 11px;
  background: rgb(36 90 80 / 8%);
  border-radius: 999px;
}

.offer-list {
  display: grid;
  gap: 12px;
  padding: 0 42px 36px;
}

.offer-card {
  position: relative;
  display: grid;
  grid-template-columns: 120px minmax(190px, 1.3fr) minmax(130px, 0.8fr) 130px;
  gap: 18px;
  align-items: center;
  padding: 24px 22px 24px 54px;
  overflow: hidden;
  background: rgb(245 240 230 / 76%);
  border: 1px solid transparent;
  border-radius: 16px;
}

.offer-card:first-child {
  background: rgb(255 252 246 / 95%);
  border-color: rgb(216 107 61 / 42%);
  box-shadow: 0 14px 34px rgb(36 90 80 / 8%);
}

.offer-rank {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  display: grid;
  width: 34px;
  color: rgb(36 90 80 / 35%);
  font-family: Georgia, serif;
  font-size: 0.75rem;
  background: rgb(36 90 80 / 6%);
  place-items: center;
  writing-mode: vertical-rl;
}

.platform-name {
  display: flex;
  gap: 10px;
  align-items: center;
}

.platform-name > div {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.platform-mark {
  display: grid;
  flex: 0 0 auto;
  width: 34px;
  height: 34px;
  color: white;
  font-size: 0.8rem;
  font-weight: 900;
  background: var(--color-primary);
  border-radius: 10px 10px 10px 3px;
  place-items: center;
}

.mark-meituan {
  color: #2c453b;
  background: #ffd343;
}

.mark-tujia {
  background: #e27945;
}

.mark-muniao {
  background: #51a883;
}

.platform-cell strong,
.room-cell strong {
  color: var(--color-primary-deep);
  font-size: 0.9rem;
}

.platform-cell p,
.room-cell p,
.policy {
  margin: 7px 0 0;
  color: var(--color-muted);
  font-size: 0.7rem;
  line-height: 1.5;
}

.best-badge,
.promotion {
  display: inline-block;
  padding: 3px 6px;
  margin-top: 4px;
  color: var(--color-accent);
  font-size: 0.62rem;
  font-weight: 800;
  background: rgb(216 107 61 / 9%);
  border-radius: 5px;
}

.breakdown-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: var(--color-muted);
  font-size: 0.68rem;
}

.breakdown-cell .discount {
  color: var(--color-success);
  font-weight: 700;
}

.total-cell {
  text-align: right;
}

.total-cell span,
.total-cell small {
  display: block;
  color: var(--color-muted);
  font-size: 0.65rem;
}

.total-cell strong {
  display: block;
  margin: 5px 0 3px;
  color: var(--color-primary-deep);
  font-family: Georgia, serif;
  font-size: 1.45rem;
  font-weight: 500;
}

.drawer-state {
  display: grid;
  min-height: 420px;
  padding: 48px;
  text-align: center;
  place-content: center;
}

.drawer-state strong {
  margin-top: 18px;
  color: var(--color-primary-deep);
  font-family: 'Noto Serif SC', serif;
  font-size: 1.4rem;
}

.drawer-state p {
  margin: 8px 0 0;
  color: var(--color-muted);
}

.loading-orbit {
  width: 48px;
  height: 48px;
  margin: auto;
  border: 2px solid rgb(36 90 80 / 12%);
  border-top-color: var(--color-accent);
  border-radius: 50%;
  animation: spin 800ms linear infinite;
}

.error-state strong {
  color: var(--color-danger);
}

.drawer-footer {
  display: flex;
  gap: 24px;
  align-items: center;
  justify-content: space-between;
  padding: 25px 42px 40px;
  border-top: 1px solid var(--color-border);
}

.drawer-footer p {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.72rem;
}

.drawer-footer button {
  flex: 0 0 auto;
  padding: 10px 14px;
  color: var(--color-primary);
  font-size: 0.76rem;
  font-weight: 800;
  background: transparent;
  border: 1px solid var(--color-primary);
  border-radius: 9px;
}

@keyframes veil-in {
  from { background: transparent; }
}

@keyframes drawer-in {
  from { transform: translateX(100%); }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 800px) {
  .offer-drawer {
    width: 100%;
  }

  .offer-card {
    grid-template-columns: 1fr 1fr;
  }

  .total-cell {
    text-align: left;
  }
}

@media (max-width: 540px) {
  .drawer-shell {
    padding-left: 0;
  }

  .drawer-header,
  .drawer-intro,
  .drawer-footer {
    padding-right: 20px;
    padding-left: 20px;
  }

  .offer-list {
    padding-right: 14px;
    padding-left: 14px;
  }

  .offer-card {
    grid-template-columns: 1fr;
    gap: 14px;
  }

  .breakdown-cell {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }

  .total-cell {
    padding-top: 12px;
    border-top: 1px dashed var(--color-border);
  }

  .drawer-footer {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
