import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getListingDetail, searchListings } from '../api/listings'
import type { ListingDetail, ListingSearchResponse } from '../types/listings'
import ListingSearchView from './ListingSearchView.vue'

vi.mock('../api/listings', () => ({
  searchListings: vi.fn(),
  getListingDetail: vi.fn(),
}))

const searchResponse: ListingSearchResponse = {
  items: [
    {
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
      currency: 'CNY',
      best_rating: '4.83',
    },
  ],
  total: 1,
  page: 1,
  page_size: 20,
}

const listingDetail: ListingDetail = {
  public_id: 'DL_000001',
  name: '云栖·洱海庭院民宿',
  listing_type: 'homestay',
  summary: '靠近才村码头的安静庭院。',
  province: '云南省',
  city: '大理市',
  district: '大理镇',
  address: '演示地址',
  latitude: '25.7072310',
  longitude: '100.1798420',
  facilities: [],
  offers: [
    {
      platform_code: 'meituan',
      platform_name: '美团',
      platform_listing_name: '演示平台民宿',
      external_id: 'MT-DL-1001',
      rating: '4.83',
      review_count: 328,
      source_url: 'https://demo.stay-scale.local/meituan/MT-DL-1001',
      room_name: '庭院大床房',
      room_external_id: 'MT-R-101',
      bed_type: '1张1.8米大床',
      max_guests: 2,
      cancellation_policy: '入住前24小时可免费取消',
      check_in: '2026-10-02',
      check_out: '2026-10-05',
      currency: 'CNY',
      room_subtotal: '1287.00',
      cleaning_fee: '0.00',
      service_fee: '45.00',
      other_fee: '0.00',
      discount_amount: '30.00',
      total_amount: '1302.00',
      price_type: 'member',
      promotion_conditions: '需美团会员',
      remaining_units: 2,
      captured_at: '2026-07-31T12:00:00',
    },
  ],
}

function mountView() {
  return mount(ListingSearchView, {
    global: {
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
      },
    },
  })
}

beforeEach(() => {
  vi.mocked(searchListings).mockReset().mockResolvedValue(searchResponse)
  vi.mocked(getListingDetail).mockReset().mockResolvedValue(listingDetail)
})

describe('ListingSearchView', () => {
  it('loads the default comparison on mount', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(searchListings).toHaveBeenCalledWith(
      expect.objectContaining({
        city: '大理市',
        checkIn: '2026-10-02',
        checkOut: '2026-10-05',
        guests: 2,
      }),
    )
    expect(wrapper.text()).toContain('找到 1 家可比价民宿')
    expect(wrapper.text()).toContain('云栖·洱海庭院民宿')
    expect(wrapper.text()).toContain('¥1,302')
  })

  it('applies a facility filter immediately', async () => {
    const wrapper = mountView()
    await flushPromises()
    vi.mocked(searchListings).mockClear()

    const wifiButton = wrapper.findAll('button').find((button) => button.text() === '无线网络')
    await wifiButton?.trigger('click')
    await flushPromises()

    expect(searchListings).toHaveBeenCalledWith(
      expect.objectContaining({ facilities: ['wifi'] }),
    )
    expect(wifiButton?.attributes('aria-pressed')).toBe('true')
  })

  it('opens the platform offer drawer', async () => {
    const wrapper = mountView()
    await flushPromises()

    const compareButton = wrapper
      .findAll('button')
      .find((button) => button.text().includes('比较平台报价'))
    await compareButton?.trigger('click')
    await flushPromises()

    expect(getListingDetail).toHaveBeenCalledWith(
      'DL_000001',
      expect.objectContaining({ checkIn: '2026-10-02', checkOut: '2026-10-05' }),
    )
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('美团')
    expect(wrapper.text()).toContain('需美团会员')
  })

  it('keeps checkout later than check-in', async () => {
    const wrapper = mountView()
    await flushPromises()
    const checkIn = wrapper.find('input[name="check-in"]')
    const checkOut = wrapper.find('input[name="check-out"]')

    await checkIn.setValue('2026-10-06')

    expect(checkOut.attributes('min')).toBe('2026-10-07')
    expect((checkOut.element as HTMLInputElement).value).toBe('2026-10-07')
  })
})
