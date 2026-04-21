import type {
  ImportBatch,
  ImportErrorRow,
  ImportPayload,
  ImportResponse,
  InventoryItem,
  InventorySummary,
} from '../types/inventory'

const API_BASE = import.meta.env.VITE_INVENTORY_API_URL ?? '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  const data = (await response.json().catch(() => null)) as
    | { detail?: string }
    | null

  if (!response.ok) {
    throw new Error(data?.detail ?? 'La solicitud al Inventory Service fallo.')
  }

  return data as T
}

export function getSummary() {
  return request<InventorySummary>('/inventory/summary')
}

export function getItems() {
  return request<InventoryItem[]>('/inventory/items')
}

export function getBatches() {
  return request<ImportBatch[]>('/inventory/batches')
}

export function getBatchErrors(batchId: string) {
  return request<ImportErrorRow[]>(`/inventory/batches/${batchId}/errors`)
}

export function importInventoryCsv(payload: ImportPayload) {
  return request<ImportResponse>('/inventory/imports', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function deleteInventoryItem(itemId: string) {
  return request<{ status: string; message: string }>(`/inventory/items/${itemId}`, {
    method: 'DELETE',
  })
}

export function deleteInventoryBatch(batchId: string) {
  return request<{ status: string; message: string }>(`/inventory/batches/${batchId}`, {
    method: 'DELETE',
  })
}
