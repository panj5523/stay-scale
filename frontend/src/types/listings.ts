export type ListingSort = 'price_asc' | 'price_desc' | 'rating_desc'

export interface ListingSearchParams {
  city: string
  checkIn: string
  checkOut: string
  guests: number
  district?: string
  keyword?: string
  facilities?: string[]
  minPrice?: number
  maxPrice?: number
  sort?: ListingSort
  page?: number
  pageSize?: number
}

export interface Facility {
  code: string
  name: string
  category: string
}

export interface ListingSummary {
  public_id: string
  name: string
  listing_type: string
  summary: string | null
  city: string
  district: string
  address: string
  latitude: string
  longitude: string
  facilities: Facility[]
  platform_count: number
  offer_count: number
  lowest_total_amount: string
  currency: string
  best_rating: string | null
}

export interface ListingSearchResponse {
  items: ListingSummary[]
  total: number
  page: number
  page_size: number
}

export interface PlatformOffer {
  platform_code: string
  platform_name: string
  platform_listing_name: string
  external_id: string
  rating: string | null
  review_count: number
  source_url: string
  room_name: string
  room_external_id: string
  bed_type: string
  max_guests: number
  cancellation_policy: string | null
  check_in: string
  check_out: string
  currency: string
  room_subtotal: string
  cleaning_fee: string
  service_fee: string
  other_fee: string
  discount_amount: string
  total_amount: string
  price_type: string
  promotion_conditions: string | null
  remaining_units: number | null
  captured_at: string
}

export interface ListingDetail {
  public_id: string
  name: string
  listing_type: string
  summary: string | null
  province: string
  city: string
  district: string
  address: string
  latitude: string
  longitude: string
  facilities: Facility[]
  offers: PlatformOffer[]
}
