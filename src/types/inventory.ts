export interface InventoryItem {
  id: string
  external_code: string
  book_reference: string
  quantity_available: number
  quantity_reserved: number
  condition: string
  defects: string
  observations: string
  import_batch_id: string
}

export interface ImportBatch {
  id: string
  file_name: string
  upload_date: string
  processed_rows: number
  valid_rows: number
  invalid_rows: number
  status: string
}

export interface ImportErrorRow {
  id: string
  batch_id: string
  row_number: number
  error_type: string
  message: string
}

export interface InventorySummary {
  total_items: number
  total_units_available: number
  total_units_reserved: number
  total_batches: number
  batches_with_errors: number
}

export interface ImportResponse {
  batch: ImportBatch
  errors: ImportErrorRow[]
}
