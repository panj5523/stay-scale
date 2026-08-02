import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getOperationsDashboard } from '../api/operations'
import OperationsDashboardView from './OperationsDashboardView.vue'

const replace = vi.fn()

vi.mock('../api/operations', () => ({ getOperationsDashboard: vi.fn() }))
vi.mock('vue-router', () => ({ useRouter: () => ({ replace }) }))

beforeEach(() => {
  vi.mocked(getOperationsDashboard).mockReset().mockResolvedValue({
    generated_at: '2026-08-02T05:00:00',
    review_queue: { pending: 1, approved: 2, rejected: 0 },
    ingestion: {
      batches_24h: 3,
      completed_batches_24h: 3,
      failed_batches_24h: 0,
      records_24h: 7,
    },
    listing_quality: {
      active_canonical_listings: 3,
      active_platform_listings: 8,
      platform_coverage: [
        { platform_code: 'tujia', platform_name: '途家', active_listing_count: 3 },
      ],
    },
    ai_usage: {
      preference_parse_count: 2,
      recommendation_explanation_count: 1,
      travel_plan_count: 1,
      review_analysis_count: 3,
      total_tokens: 200,
    },
    warnings: ['还有 1 条导入记录等待人工审核。'],
  })
  replace.mockReset()
})

describe('OperationsDashboardView', () => {
  it('loads operational metrics and warnings', async () => {
    const wrapper = mount(OperationsDashboardView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })
    await flushPromises()

    expect(getOperationsDashboard).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('把数据健康度')
    expect(wrapper.text()).toContain('还有 1 条导入记录等待人工审核。')
    expect(wrapper.text()).toContain('200')
  })
})
