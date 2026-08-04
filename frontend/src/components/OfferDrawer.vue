<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import type { ListingDetail, ReviewAnalysis, ReviewSentiment } from '../types/listings'
import { formatCurrency, formatShortDate, stayNights } from '../utils/format'

const props = defineProps<{
  detail: ListingDetail | null
  loading: boolean
  error: string
  checkIn: string
  checkOut: string
  reviewAnalysis: ReviewAnalysis | null
  reviewAnalysisError: string
}>()

const emit = defineEmits<{
  close: []
}>()

const nights = computed(() => stayNights(props.checkIn, props.checkOut))
const sentimentLabels: Record<ReviewSentiment, string> = {
  positive: '正面',
  neutral: '中性',
  negative: '负面',
}

function sentimentPercent(sentiment: ReviewSentiment): number {
  if (!props.reviewAnalysis?.review_count) return 0
  return Math.round(
    ((props.reviewAnalysis.sentiment_distribution[sentiment] ?? 0) /
      props.reviewAnalysis.review_count) *
      100,
  )
}

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
              <strong>{{ formatCurrency(offer.total_amount, offer.currency) }}</strong><small :class="['freshness', offer.freshness_status === 'stale' ? 'stale' : 'fresh']">{{ offer.freshness_status === 'stale' ? '价格可能已过期' : '价格较新' }} · {{ offer.age_minutes ?? 0 }} 分钟前</small>
              <small>{{ offer.price_type === 'standard' ? '标准价' : '含条件优惠' }}</small>
            </div>
          </article>
        </div>

        <div v-else class="drawer-state">
          <strong>当前条件下暂无报价</strong>
          <p>可以调整日期或入住人数后重新查询。</p>
        </div>

        <section class="review-insight" aria-labelledby="review-insight-title">
          <div class="review-heading">
            <div>
              <span>REVIEW SIGNALS · AI ASSISTED</span>
              <h3 id="review-insight-title">住客都在谈什么</h3>
            </div>
            <small v-if="reviewAnalysis">{{ reviewAnalysis.review_count }} 条评论样本</small>
          </div>

          <p v-if="reviewAnalysisError" class="review-empty">{{ reviewAnalysisError }}</p>
          <p v-else-if="!reviewAnalysis" class="review-empty">
            暂无已审核的评论分析。导入平台评论后，这里会展示主题、情绪和原文证据。
          </p>
          <template v-else>
            <p class="review-summary">{{ reviewAnalysis.summary }}</p>
            <div class="sentiment-grid">
              <div v-for="sentiment in (['positive', 'neutral', 'negative'] as ReviewSentiment[])" :key="sentiment">
                <span>{{ sentimentLabels[sentiment] }}</span>
                <strong>{{ sentimentPercent(sentiment) }}%</strong>
                <i><b :class="sentiment" :style="{ width: `${sentimentPercent(sentiment)}%` }"></b></i>
              </div>
            </div>
            <div class="topic-grid">
              <article v-for="topic in reviewAnalysis.topics" :key="`${topic.code}-${topic.sentiment}`">
                <div>
                  <strong>{{ topic.label }}</strong>
                  <span :class="`sentiment-${topic.sentiment}`">{{ sentimentLabels[topic.sentiment] }}</span>
                  <small>提及 {{ topic.mention_count }} 次</small>
                </div>
                <blockquote v-for="evidence in topic.evidence" :key="evidence">“{{ evidence }}”</blockquote>
              </article>
            </div>
            <p v-for="warning in reviewAnalysis.warnings" :key="warning" class="review-warning">
              {{ warning }}
            </p>
          </template>
        </section>

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
  background: rgb(10 28 47 / 48%);
  backdrop-filter: blur(5px);
  animation: veil-in 220ms ease-out;
}

.offer-drawer {
  width: min(980px, 92vw);
  height: 100%;
  overflow-y: auto;
  background:
    linear-gradient(90deg, rgb(46 111 149 / 5%) 1px, transparent 1px) 0 0 / 64px 64px,
    var(--color-surface);
  box-shadow: -24px 0 80px rgb(10 28 47 / 24%);
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
  background: rgb(255 253 248 / 94%);
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
  background: rgb(46 111 149 / 8%);
  border-radius: 999px;
}

.offer-list {
  display: grid;
  gap: 12px;
  padding: 0 42px 36px;
}

.review-insight { padding: 30px 42px; margin: 0 42px 36px; background: rgb(221 236 232 / 36%); border: 1px solid rgb(46 111 149 / 13%); border-radius: 18px; }
.review-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 18px; }
.review-heading span { color: var(--color-accent); font-size: .62rem; font-weight: 900; letter-spacing: .14em; }
.review-heading h3 { margin: 7px 0 0; color: var(--color-primary-deep); font-family: 'Noto Serif SC', serif; font-size: 1.45rem; }
.review-heading small { color: var(--color-muted); }
.review-summary { margin: 18px 0; color: var(--color-primary-deep); font-size: .82rem; line-height: 1.7; }
.review-empty { margin: 20px 0 0; color: var(--color-muted); font-size: .78rem; line-height: 1.7; }
.sentiment-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.sentiment-grid > div { display: grid; grid-template-columns: 1fr auto; gap: 7px; padding: 12px; background: var(--color-surface); border-radius: 10px; }
.sentiment-grid span { color: var(--color-muted); font-size: .68rem; }
.sentiment-grid strong { color: var(--color-primary-deep); font-family: Georgia, serif; }
.sentiment-grid i { grid-column: 1 / -1; height: 4px; overflow: hidden; background: var(--color-border); border-radius: 4px; }
.sentiment-grid b { display: block; height: 100%; border-radius: inherit; }
.sentiment-grid b.positive { background: var(--color-success); }
.sentiment-grid b.neutral { background: #b79b68; }
.sentiment-grid b.negative { background: var(--color-danger); }
.topic-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 16px; }
.topic-grid article { padding: 14px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: 11px; }
.topic-grid article > div { display: flex; gap: 8px; align-items: center; }
.topic-grid strong { color: var(--color-primary-deep); font-size: .8rem; }
.topic-grid span { padding: 3px 6px; font-size: .58rem; border-radius: 999px; }
.sentiment-positive { color: var(--color-success); background: rgb(50 125 93 / 9%); }
.sentiment-neutral { color: #8b6d39; background: rgb(183 155 104 / 13%); }
.sentiment-negative { color: var(--color-danger); background: rgb(170 70 58 / 9%); }
.topic-grid small { margin-left: auto; color: var(--color-muted); font-size: .6rem; }
.topic-grid blockquote { margin: 9px 0 0; color: var(--color-muted); font-size: .68rem; line-height: 1.55; }
.review-warning { margin: 14px 0 0; color: var(--color-muted); font-size: .64rem; }

.offer-card {
  position: relative;
  display: grid;
  grid-template-columns: 120px minmax(190px, 1.3fr) minmax(130px, 0.8fr) 130px;
  gap: 18px;
  align-items: center;
  padding: 24px 22px 24px 54px;
  overflow: hidden;
  background: rgb(238 247 247 / 72%);
  border: 1px solid transparent;
  border-radius: 16px;
}

.offer-card:first-child {
  background: rgb(255 253 248 / 96%);
  border-color: rgb(226 109 90 / 42%);
  box-shadow: 0 14px 34px rgb(22 50 79 / 10%);
}

.offer-rank {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  display: grid;
  width: 34px;
  color: rgb(22 50 79 / 35%);
  font-family: Georgia, serif;
  font-size: 0.75rem;
  background: rgb(46 111 149 / 6%);
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
  background: rgb(226 109 90 / 10%);
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
  border: 2px solid rgb(46 111 149 / 14%);
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
