export interface PriceInfo {
  price: string | number
  price_range: string
  date_fetched: string
}

export interface UnitInfo {
  unit: string
  building: string
  size: string | number
  available_date: string
  floorplan_type: string
  floorplan_link: string
  floorplan_note: string
  prices: PriceInfo[]
}

export interface FilterOptions {
  building: string[]
  floorplanType: string[]
  minPrice: number | null
  maxPrice: number | null
  availableFrom: string | null
  availableTo: string | null
  searchQuery: string
}

export interface SortOptions {
  key: string
  order: 'asc' | 'desc'
}

export interface UnitStoreState {
  units: UnitInfo[]
  loading: boolean
  error: string | null
  filters: FilterOptions
  sort: SortOptions
}
