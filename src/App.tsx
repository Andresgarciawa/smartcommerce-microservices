import {
  startTransition,
  useCallback,
  useEffect,
  useState,
  type ChangeEvent,
  type FormEvent,
} from 'react'

import './App.css'
import {
  createBook,
  createCategory,
  deleteBook,
  deleteCategory,
  getBooks,
  getCatalogSummary,
  getCategories,
} from './api/catalog'
import {
  deleteInventoryBatch,
  deleteInventoryItem,
  getBatchErrors,
  getBatches,
  getItems,
  getSummary,
  importInventoryCsv,
} from './api/inventory'
import { CatalogSection } from './components/CatalogSection'
import { InventorySection } from './components/InventorySection'
import {
  inventorySampleContent,
  inventorySampleName,
} from './lib/inventoryDefaults'
import type { Book, CatalogSummary, Category } from './types/catalog'
import type {
  ImportBatch,
  ImportErrorRow,
  InventoryItem,
  InventorySummary,
} from './types/inventory'

type ActiveService = 'inventory' | 'catalog'

function App() {
  const [activeService, setActiveService] = useState<ActiveService>('inventory')

  const [inventorySummary, setInventorySummary] = useState<InventorySummary | null>(
    null,
  )
  const [inventoryItems, setInventoryItems] = useState<InventoryItem[]>([])
  const [inventoryBatches, setInventoryBatches] = useState<ImportBatch[]>([])
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null)
  const [selectedBatchErrors, setSelectedBatchErrors] = useState<ImportErrorRow[]>(
    [],
  )
  const [inventoryFileName, setInventoryFileName] =
    useState(inventorySampleName)
  const [inventoryCsvContent, setInventoryCsvContent] =
    useState(inventorySampleContent)
  const [inventoryLoading, setInventoryLoading] = useState(true)
  const [inventorySubmitting, setInventorySubmitting] = useState(false)
  const [inventoryErrorsLoading, setInventoryErrorsLoading] = useState(false)
  const [inventoryErrorMessage, setInventoryErrorMessage] = useState<string | null>(
    null,
  )
  const [inventorySuccessMessage, setInventorySuccessMessage] = useState<
    string | null
  >(null)

  const [catalogSummary, setCatalogSummary] = useState<CatalogSummary | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [books, setBooks] = useState<Book[]>([])
  const [catalogLoading, setCatalogLoading] = useState(true)
  const [catalogCreatingCategory, setCatalogCreatingCategory] = useState(false)
  const [catalogCreatingBook, setCatalogCreatingBook] = useState(false)
  const [catalogErrorMessage, setCatalogErrorMessage] = useState<string | null>(
    null,
  )
  const [catalogSuccessMessage, setCatalogSuccessMessage] = useState<string | null>(
    null,
  )
  const [categoryForm, setCategoryForm] = useState({
    name: '',
    description: '',
  })
  const [bookForm, setBookForm] = useState({
    title: '',
    subtitle: '',
    author: '',
    publisher: '',
    publication_year: '2024',
    volume: '',
    isbn: '',
    issn: '',
    category_id: '',
    description: '',
    cover_url: '',
    enriched_flag: false,
    published_flag: false,
  })

  const refreshInventory = useCallback(
    async (preferredBatchId?: string) => {
      setInventoryLoading(true)

      try {
        const [nextSummary, nextItems, nextBatches] = await Promise.all([
          getSummary(),
          getItems(),
          getBatches(),
        ])

        const batchIdToLoad =
          preferredBatchId ??
          (selectedBatchId &&
          nextBatches.some((batch) => batch.id === selectedBatchId)
            ? selectedBatchId
            : nextBatches[0]?.id) ??
          null

        const nextErrors = batchIdToLoad
          ? await getBatchErrors(batchIdToLoad)
          : []

        startTransition(() => {
          setInventorySummary(nextSummary)
          setInventoryItems(nextItems)
          setInventoryBatches(nextBatches)
          setSelectedBatchId(batchIdToLoad)
          setSelectedBatchErrors(nextErrors)
          setInventoryErrorMessage(null)
        })
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : 'No se pudo cargar el Inventory Service.'
        setInventoryErrorMessage(message)
      } finally {
        setInventoryLoading(false)
      }
    },
    [selectedBatchId],
  )

  const refreshCatalog = useCallback(async () => {
    setCatalogLoading(true)

    try {
      const [nextSummary, nextCategories, nextBooks] = await Promise.all([
        getCatalogSummary(),
        getCategories(),
        getBooks(),
      ])

      startTransition(() => {
        setCatalogSummary(nextSummary)
        setCategories(nextCategories)
        setBooks(nextBooks)
        setCatalogErrorMessage(null)
        setBookForm((current) => ({
          ...current,
          category_id:
            current.category_id ||
            nextCategories[0]?.id ||
            '',
        }))
      })
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'No se pudo cargar el Catalog Service.'
      setCatalogErrorMessage(message)
    } finally {
      setCatalogLoading(false)
    }
  }, [])

  useEffect(() => {
    void Promise.all([refreshInventory(), refreshCatalog()])
  }, [refreshCatalog, refreshInventory])

  async function handleInventoryBatchSelection(batchId: string) {
    setSelectedBatchId(batchId)
    setInventoryErrorsLoading(true)

    try {
      const errors = await getBatchErrors(batchId)
      startTransition(() => {
        setSelectedBatchErrors(errors)
      })
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'No se pudieron cargar los errores del lote.'
      setInventoryErrorMessage(message)
    } finally {
      setInventoryErrorsLoading(false)
    }
  }

  async function handleInventoryFileChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0]

    if (!file) {
      return
    }

    const text = await file.text()
    setInventoryFileName(file.name)
    setInventoryCsvContent(text)
    setInventorySuccessMessage(`Archivo ${file.name} cargado en la vista previa.`)
  }

  async function handleInventoryImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setInventorySubmitting(true)
    setInventorySuccessMessage(null)
    setInventoryErrorMessage(null)

    try {
      const result = await importInventoryCsv({
        file_name: inventoryFileName.trim() || `inventory-${Date.now()}.csv`,
        csv_content: inventoryCsvContent,
      })

      setInventorySuccessMessage(
        `Lote ${result.batch.id.slice(0, 8)} procesado con ${result.batch.valid_rows} filas validas y ${result.batch.invalid_rows} invalidas.`,
      )
      await refreshInventory(result.batch.id)
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'La importacion fallo.'
      setInventoryErrorMessage(message)
    } finally {
      setInventorySubmitting(false)
    }
  }

  function handleResetInventorySample() {
    setInventoryFileName(inventorySampleName)
    setInventoryCsvContent(inventorySampleContent)
  }

  async function handleCreateCategory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setCatalogCreatingCategory(true)
    setCatalogErrorMessage(null)
    setCatalogSuccessMessage(null)

    try {
      const created = await createCategory(categoryForm)
      setCategoryForm({ name: '', description: '' })
      setBookForm((current) => ({
        ...current,
        category_id: current.category_id || created.id,
      }))
      setCatalogSuccessMessage(`Categoria ${created.name} creada correctamente.`)
      await refreshCatalog()
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'No se pudo crear la categoria.'
      setCatalogErrorMessage(message)
    } finally {
      setCatalogCreatingCategory(false)
    }
  }

  async function handleCreateBook(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setCatalogCreatingBook(true)
    setCatalogErrorMessage(null)
    setCatalogSuccessMessage(null)

    try {
      const created = await createBook({
        ...bookForm,
        publication_year: Number(bookForm.publication_year),
      })

      setCatalogSuccessMessage(`Libro ${created.title} registrado correctamente.`)
      setBookForm((current) => ({
        ...current,
        title: '',
        subtitle: '',
        author: '',
        publisher: '',
        publication_year: current.publication_year,
        volume: '',
        isbn: '',
        issn: '',
        description: '',
        cover_url: '',
        enriched_flag: false,
        published_flag: false,
      }))
      await refreshCatalog()
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'No se pudo crear el libro.'
      setCatalogErrorMessage(message)
    } finally {
      setCatalogCreatingBook(false)
    }
  }

  async function handleDeleteCategory(categoryId: string) {
    setCatalogErrorMessage(null)
    setCatalogSuccessMessage(null)

    try {
      const result = await deleteCategory(categoryId)
      setCatalogSuccessMessage(result.message)
      await refreshCatalog()
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'No se pudo eliminar la categoria.'
      setCatalogErrorMessage(message)
    }
  }

  async function handleDeleteBook(bookId: string) {
    setCatalogErrorMessage(null)
    setCatalogSuccessMessage(null)

    try {
      const result = await deleteBook(bookId)
      setCatalogSuccessMessage(result.message)
      await Promise.all([refreshCatalog(), refreshInventory()])
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'No se pudo eliminar el libro.'
      setCatalogErrorMessage(message)
    }
  }

  async function handleDeleteInventoryItem(itemId: string) {
    setInventoryErrorMessage(null)
    setInventorySuccessMessage(null)

    try {
      const result = await deleteInventoryItem(itemId)
      setInventorySuccessMessage(result.message)
      await Promise.all([refreshInventory(), refreshCatalog()])
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'No se pudo eliminar el item de inventario.'
      setInventoryErrorMessage(message)
    }
  }

  async function handleDeleteInventoryBatch(batchId: string) {
    setInventoryErrorMessage(null)
    setInventorySuccessMessage(null)

    try {
      const result = await deleteInventoryBatch(batchId)
      setInventorySuccessMessage(result.message)
      await Promise.all([refreshInventory(), refreshCatalog()])
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'No se pudo eliminar el lote.'
      setInventoryErrorMessage(message)
    }
  }

  return (
    <div className="app-shell">
      <header className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">BookFlow - Microservicios</p>
          <h1>Inventory y Catalog listos para operar en React, FastAPI y Docker</h1>
          <p className="hero-text">
            El frontend consume dos servicios separados por dominio:
            inventario fisico y catalogo comercial. Ambos quedan preparados para
            ejecutarse juntos con <code>docker compose</code>.
          </p>
        </div>

        <div className="boundary-card">
          <span className="boundary-label">Arquitectura distribuida</span>
          <strong>Frontend + 2 servicios</strong>
          <p>
            Cada dominio tiene su propia persistencia, su propio modelo de datos y
            sus propios endpoints REST sobre FastAPI.
          </p>
          <div className="boundary-tags">
            <span>React + TypeScript</span>
            <span>Inventory Service</span>
            <span>Catalog Service</span>
            <span>Docker Compose</span>
          </div>
        </div>
      </header>

      <section className="service-switcher">
        <button
          type="button"
          className={activeService === 'inventory' ? 'switch-active' : ''}
          onClick={() => setActiveService('inventory')}
        >
          Inventory Service
        </button>
        <button
          type="button"
          className={activeService === 'catalog' ? 'switch-active' : ''}
          onClick={() => setActiveService('catalog')}
        >
          Catalog Service
        </button>
      </section>

      <main className="dashboard">
        {activeService === 'inventory' ? (
          <InventorySection
            books={books}
            summary={inventorySummary}
            items={inventoryItems}
            batches={inventoryBatches}
            selectedBatchId={selectedBatchId}
            selectedBatchErrors={selectedBatchErrors}
            fileName={inventoryFileName}
            csvContent={inventoryCsvContent}
            isLoading={inventoryLoading}
            isSubmitting={inventorySubmitting}
            isLoadingErrors={inventoryErrorsLoading}
            errorMessage={inventoryErrorMessage}
            successMessage={inventorySuccessMessage}
            onFileNameChange={setInventoryFileName}
            onCsvContentChange={setInventoryCsvContent}
            onFileChange={handleInventoryFileChange}
            onImport={handleInventoryImport}
            onSelectBatch={handleInventoryBatchSelection}
            onResetSample={handleResetInventorySample}
            onDeleteItem={handleDeleteInventoryItem}
            onDeleteBatch={handleDeleteInventoryBatch}
          />
        ) : (
          <CatalogSection
            summary={catalogSummary}
            categories={categories}
            books={books}
            categoryForm={categoryForm}
            bookForm={bookForm}
            isLoading={catalogLoading}
            isCreatingCategory={catalogCreatingCategory}
            isCreatingBook={catalogCreatingBook}
            errorMessage={catalogErrorMessage}
            successMessage={catalogSuccessMessage}
            onCategoryFieldChange={(field, value) =>
              setCategoryForm((current) => ({ ...current, [field]: value }))
            }
            onBookFieldChange={(field, value) =>
              setBookForm((current) => ({ ...current, [field]: value }))
            }
            onCreateCategory={handleCreateCategory}
            onCreateBook={handleCreateBook}
            onDeleteCategory={handleDeleteCategory}
            onDeleteBook={handleDeleteBook}
          />
        )}
      </main>
    </div>
  )
}

export default App
