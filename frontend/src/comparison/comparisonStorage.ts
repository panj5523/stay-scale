import type { ListingSearchParams, ListingSummary } from '../types/listings'

const STORAGE_KEY = 'stay_scale_comparisons'
export const MAX_COMPARISONS = 3

export interface ComparisonEntry {
  listing: ListingSummary
  search: Pick<ListingSearchParams, 'checkIn' | 'checkOut' | 'guests'>
}

function isComparisonEntry(value: unknown): value is ComparisonEntry {
  if (!value || typeof value !== 'object') return false
  const entry = value as Partial<ComparisonEntry>
  return Boolean(
    entry.listing?.public_id
      && entry.listing.name
      && entry.search?.checkIn
      && entry.search.checkOut
      && Number.isFinite(entry.search.guests),
  )
}

export function getComparisons(): ComparisonEntry[] {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '[]') as unknown
    if (!Array.isArray(stored)) return []
    return stored.filter(isComparisonEntry).slice(0, MAX_COMPARISONS)
  } catch {
    return []
  }
}

function saveComparisons(entries: ComparisonEntry[]): ComparisonEntry[] {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries))
  return entries
}

export function addComparison(entry: ComparisonEntry): 'added' | 'exists' | 'full' {
  const entries = getComparisons()
  if (entries.some((item) => item.listing.public_id === entry.listing.public_id)) return 'exists'
  if (entries.length >= MAX_COMPARISONS) return 'full'
  saveComparisons([...entries, entry])
  return 'added'
}

export function removeComparison(publicId: string): ComparisonEntry[] {
  return saveComparisons(
    getComparisons().filter((entry) => entry.listing.public_id !== publicId),
  )
}

export function clearComparisons(): void {
  localStorage.removeItem(STORAGE_KEY)
}
