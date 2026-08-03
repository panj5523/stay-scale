import { beforeEach, describe, expect, it } from 'vitest'
import type { ListingSummary } from '../types/listings'
import { MAX_COMPARISONS, addComparison, getComparisons } from './comparisonStorage'

const listing: ListingSummary = {
  public_id: 'DL_000001',
  name: '云栖·洱海庭院民宿',
  listing_type: 'homestay',
  summary: null,
  city: '大理市',
  district: '大理镇',
  address: '演示地址',
  latitude: '25.7072310',
  longitude: '100.1798420',
  facilities: [],
  platform_count: 3,
  offer_count: 4,
  lowest_total_amount: '1302.00',
  currency: 'CNY',
  best_rating: '4.83',
}

const search = { checkIn: '2026-10-02', checkOut: '2026-10-05', guests: 2 }

beforeEach(() => localStorage.clear())

describe('comparisonStorage', () => {
  it('recovers safely from malformed browser data', () => {
    localStorage.setItem('stay_scale_comparisons', '{broken')

    expect(getComparisons()).toEqual([])
  })

  it(`limits the shortlist to ${MAX_COMPARISONS} unique stays`, () => {
    for (let index = 1; index <= MAX_COMPARISONS; index += 1) {
      expect(addComparison({
        listing: { ...listing, public_id: `DL_00000${index}`, name: `候选民宿 ${index}` },
        search,
      })).toBe('added')
    }

    expect(addComparison({
      listing: { ...listing, public_id: 'DL_000004', name: '第 4 家民宿' },
      search,
    })).toBe('full')
    expect(getComparisons()).toHaveLength(MAX_COMPARISONS)
  })
})
