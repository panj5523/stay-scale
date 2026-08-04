import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'
import { addComparison } from '../comparison/comparisonStorage'
import type { ListingSummary } from '../types/listings'
import ComparisonView from './ComparisonView.vue'

const listing: ListingSummary = {
  public_id: 'DL_000001',
  name: '云栖·洱海庭院民宿',
  listing_type: 'homestay',
  summary: '靠近才村码头的安静庭院。',
  city: '大理市',
  district: '大理镇',
  address: '演示地址',
  latitude: '25.7072310',
  longitude: '100.1798420',
  facilities: [{ code: 'wifi', name: '无线网络', category: '基础设施' }],
  platform_count: 3,
  offer_count: 4,
  lowest_total_amount: '1302.00',
  oldest_price_captured_at: '2026-08-04T10:00:00',
  freshness_status: 'fresh',
  age_minutes: 30,
  currency: 'CNY',
  best_rating: '4.83',
}

function mountView() {
  return mount(ComparisonView, {
    global: {
      stubs: { RouterLink: { template: '<a><slot /></a>' } },
    },
  })
}

beforeEach(() => localStorage.clear())

describe('ComparisonView', () => {
  it('shows an empty-state link when no stays are selected', () => {
    const wrapper = mountView()

    expect(wrapper.text()).toContain('比较清单还是空的')
    expect(wrapper.text()).toContain('去挑选民宿')
  })

  it('renders saved comparison details and removes an entry', async () => {
    addComparison({
      listing,
      search: { checkIn: '2026-10-02', checkOut: '2026-10-05', guests: 2 },
    })
    const wrapper = mountView()

    expect(wrapper.text()).toContain('云栖·洱海庭院民宿')
    expect(wrapper.text()).toContain('¥1,302')
    expect(wrapper.text()).toContain('3 个平台 · 4 条报价')
    expect(wrapper.text()).toContain('无线网络')

    await wrapper.find('button[aria-label^="移出比较"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('比较清单还是空的')
    expect(localStorage.getItem('stay_scale_comparisons')).toBe('[]')
  })
})
