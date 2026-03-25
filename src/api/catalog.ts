import type {
  Book,
  BookPayload,
  CatalogSummary,
  Category,
  CategoryPayload,
} from '../types/catalog'

const API_BASE = '/api/catalog'

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
    throw new Error(data?.detail ?? 'La solicitud al Catalog Service fallo.')
  }

  return data as T
}

export function getCatalogSummary() {
  return request<CatalogSummary>('/summary')
}

export function getCategories() {
  return request<Category[]>('/categories')
}

export function createCategory(payload: CategoryPayload) {
  return request<Category>('/categories', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getBooks() {
  return request<Book[]>('/books')
}

export function createBook(payload: BookPayload) {
  return request<Book>('/books', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function deleteCategory(categoryId: string) {
  return request<{ status: string; message: string }>(`/categories/${categoryId}`, {
    method: 'DELETE',
  })
}

export function deleteBook(bookId: string) {
  return request<{ status: string; message: string }>(`/books/${bookId}`, {
    method: 'DELETE',
  })
}
