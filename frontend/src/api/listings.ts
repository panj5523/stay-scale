import { apiClient } from './client'
import type {
  ListingDetail,
  ListingSearchParams,
  ListingSearchResponse,
} from '../types/listings'

function buildSearchParams(params: ListingSearchParams): URLSearchParams {
  const query = new URLSearchParams({
    city: params.city,
    check_in: params.checkIn,
    check_out: params.checkOut,
    guests: String(params.guests),
    sort: params.sort ?? 'price_asc',
    page: String(params.page ?? 1),
    page_size: String(params.pageSize ?? 20),
  })

  if (params.district) query.set('district', params.district)
  if (params.keyword) query.set('keyword', params.keyword)
  if (params.minPrice !== undefined) query.set('min_price', String(params.minPrice))
  if (params.maxPrice !== undefined) query.set('max_price', String(params.maxPrice))
  params.facilities?.forEach((facility) => query.append('facility', facility))
  return query
}

export async function searchListings(
  params: ListingSearchParams,
): Promise<ListingSearchResponse> {
  const response = await apiClient.get<ListingSearchResponse>('/v1/listings', {
    params: buildSearchParams(params),
  })
  return response.data
}

export async function getListingDetail(
  publicId: string,
  params: Pick<ListingSearchParams, 'checkIn' | 'checkOut' | 'guests'>,
): Promise<ListingDetail> {
  const response = await apiClient.get<ListingDetail>(`/v1/listings/${publicId}`, {
    params: {
      check_in: params.checkIn,
      check_out: params.checkOut,
      guests: params.guests,
    },
  })
  return response.data
}
