import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { confirmPreferenceParse, parsePreferences } from '../api/preferenceParsing'
import { createRecommendation } from '../api/recommendations'
import type { PreferenceParseResponse } from '../types/preferenceParsing'
import type { RecommendationResponse } from '../types/recommendations'
import RecommendationView from './RecommendationView.vue'

vi.mock('../api/recommendations', () => ({
  createRecommendation: vi.fn(),
}))

vi.mock('../api/preferenceParsing', () => ({
  parsePreferences: vi.fn(),
  confirmPreferenceParse: vi.fn(),
}))

const completedResponse: RecommendationResponse = {
  session_id: 'session-001',
  status: 'completed',
  algorithm_version: 'explainable-v1',
  request: {
    city: '大理市',
    check_in: '2026-10-02',
    check_out: '2026-10-05',
    guests: 2,
    budget_total: '1600',
    preferred_facilities: [],
    preferred_districts: [],
    travel_style: 'value',
    top_k: 3,
  },
  results: [
    {
      rank: 1,
      listing_public_id: 'DL_000002',
      listing_name: '古城南门设计师民宿',
      district: '大理镇',
      total_amount: '1128.00',
      currency: 'CNY',
      best_rating: '4.72',
      platform_count: 2,
      total_score: '90.91',
      score_breakdown: {
        price: '100.00',
        rating: '94.40',
        facilities: '75.00',
        platform_coverage: '66.67',
        location: '50.00',
      },
      reasons: ['入住总价在你的预算内。', '在当前可订候选中总价更有优势。'],
    },
  ],
  generated_at: '2026-08-01T02:00:00',
}

const parseResponse: PreferenceParseResponse = {
  session_id: 'parse-001',
  status: 'needs_confirmation',
  parser_name: 'local-rule-parser',
  parser_version: 'zh-rules-v1',
  confidence: '0.930',
  original_text: '三人去大理看海',
  draft: {
    city: '大理市',
    check_in: '2026-10-02',
    check_out: '2026-10-05',
    guests: 3,
    budget_total: '2200',
    preferred_facilities: ['sea_view'],
    preferred_districts: ['双廊镇'],
    travel_style: 'scenery',
    risk_aversion: 'medium',
  },
  evidence: [
    { field: 'city', matched_text: '大理', normalized_value: '大理市' },
    { field: 'travel_style', matched_text: '看海', normalized_value: 'scenery' },
  ],
  missing_fields: [],
  warnings: [],
  created_at: '2026-08-01T03:00:00',
  confirmed_at: null,
}

function mountView() {
  return mount(RecommendationView, {
    global: {
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
      },
    },
  })
}

beforeEach(() => {
  vi.mocked(createRecommendation).mockReset().mockResolvedValue(completedResponse)
  vi.mocked(parsePreferences).mockReset().mockResolvedValue(parseResponse)
  vi.mocked(confirmPreferenceParse)
    .mockReset()
    .mockResolvedValue({ ...parseResponse, status: 'confirmed' })
})

describe('RecommendationView', () => {
  it('submits the default preferences and renders explainable results', async () => {
    const wrapper = mountView()

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createRecommendation).toHaveBeenCalledWith({
      city: '大理市',
      checkIn: '2026-10-02',
      checkOut: '2026-10-05',
      guests: 2,
      budgetTotal: 1600,
      preferredFacilities: [],
      preferredDistricts: [],
      travelStyle: 'value',
      topK: 3,
    })
    expect(wrapper.text()).toContain('为你排出的 1 个选择')
    expect(wrapper.text()).toContain('古城南门设计师民宿')
    expect(wrapper.text()).toContain('90.91')
    expect(wrapper.text()).toContain('入住总价在你的预算内。')
  })

  it('sends selected travel style, facilities and districts', async () => {
    const wrapper = mountView()
    const scenery = wrapper.find('input[value="scenery"]')
    await scenery.setValue(true)
    const seaView = wrapper.findAll('button').find((button) => button.text() === '海景')
    const daliTown = wrapper.findAll('button').find((button) => button.text() === '大理镇')
    await seaView?.trigger('click')
    await daliTown?.trigger('click')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createRecommendation).toHaveBeenCalledWith(
      expect.objectContaining({
        travelStyle: 'scenery',
        preferredFacilities: ['sea_view'],
        preferredDistricts: ['大理镇'],
      }),
    )
    expect(seaView?.attributes('aria-pressed')).toBe('true')
  })

  it('shows a clear state when no listing is available', async () => {
    vi.mocked(createRecommendation).mockResolvedValue({
      ...completedResponse,
      session_id: 'session-empty',
      status: 'no_candidates',
      results: [],
    })
    const wrapper = mountView()

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('这组条件下暂无可订民宿')
    expect(wrapper.text()).toContain('没有用无报价房源凑数')
  })

  it('rejects an invalid date range before calling the API', async () => {
    const wrapper = mountView()
    await wrapper.find('input[name="check-out"]').setValue('2026-10-01')

    await wrapper.find('form').trigger('submit')

    expect(createRecommendation).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('离店日期必须晚于入住日期。')
  })

  it('limits checkout to the day after check-in and repairs a reversed range', async () => {
    const wrapper = mountView()
    const checkIn = wrapper.find('input[name="check-in"]')
    const checkOut = wrapper.find('input[name="check-out"]')

    await checkIn.setValue('2026-10-06')

    expect(checkOut.attributes('min')).toBe('2026-10-07')
    expect((checkOut.element as HTMLInputElement).value).toBe('2026-10-07')
  })

  it('parses natural language, fills the form and confirms before recommending', async () => {
    const wrapper = mountView()
    const parseButton = wrapper
      .findAll('button')
      .find((button) => button.text().includes('识别并填入条件'))

    await parseButton?.trigger('click')
    await flushPromises()

    expect(parsePreferences).toHaveBeenCalledOnce()
    expect((wrapper.find('select[name="guests"]').element as HTMLSelectElement).value).toBe('3')
    expect((wrapper.find('input[name="budget"]').element as HTMLInputElement).value).toBe('2200')
    expect(wrapper.text()).toContain('已识别 2 项信息')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(confirmPreferenceParse).toHaveBeenCalledWith(
      'parse-001',
      expect.objectContaining({
        guests: 3,
        budget_total: '2200',
        preferred_facilities: ['sea_view'],
        preferred_districts: ['双廊镇'],
        travel_style: 'scenery',
      }),
    )
    expect(createRecommendation).toHaveBeenCalledWith(
      expect.objectContaining({ guests: 3, travelStyle: 'scenery' }),
    )
  })
})
