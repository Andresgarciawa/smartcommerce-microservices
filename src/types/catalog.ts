export interface Category {
  id: string
  name: string
  description: string
  created_at: string
}

export interface Book {
  id: string
  title: string
  subtitle: string
  author: string
  publisher: string
  publication_year: number
  volume: string
  isbn: string
  issn: string
  category_id: string
  category_name: string
  description: string
  cover_url: string
  enriched_flag: boolean
  published_flag: boolean
  quantity_available_total: number
  quantity_reserved_total: number
  inventory_records: number
  inventory_sync: boolean
}

export interface CategoryPayload {
  name: string
  description: string
}

export interface BookPayload {
  title: string
  subtitle: string
  author: string
  publisher: string
  publication_year: number
  volume: string
  isbn: string
  issn: string
  category_id: string
  description: string
  cover_url: string
  enriched_flag: boolean
  published_flag: boolean
}

export interface CatalogSummary {
  total_categories: number
  total_books: number
  published_books: number
  enriched_books: number
}
