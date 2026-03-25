import type { ChangeEvent, FormEvent } from 'react'

import type { Book } from '../types/catalog'
import type {
  ImportBatch,
  ImportErrorRow,
  InventoryItem,
  InventorySummary,
} from '../types/inventory'

const modelCards = [
  {
    title: 'InventoryItem',
    description:
      'Entidad operativa que representa una unidad de inventario enlazada por referencia al catalogo.',
    fields: [
      'id',
      'external_code',
      'book_reference',
      'quantity_available',
      'quantity_reserved',
      'condition',
      'defects',
      'observations',
      'import_batch_id',
    ],
  },
  {
    title: 'ImportBatch',
    description:
      'Traza cada carga masiva y permite auditar cuantas filas se procesaron, aceptaron o rechazaron.',
    fields: [
      'id',
      'file_name',
      'upload_date',
      'processed_rows',
      'valid_rows',
      'invalid_rows',
      'status',
    ],
  },
  {
    title: 'ImportError',
    description:
      'Registra errores por fila para que el administrador corrija el archivo sin perder visibilidad del lote.',
    fields: ['id', 'batch_id', 'row_number', 'error_type', 'message'],
  },
]

const csvChecklist = [
  'Columnas requeridas: external_code, book_reference, quantity_available, quantity_reserved, condition.',
  'defects y observations son opcionales y ayudan a reflejar la condicion fisica real.',
  'quantity_reserved no puede superar quantity_available.',
  'book_reference queda listo para enlazarse al Catalog Service sin acoplar esquemas.',
]

function formatNumber(value: number) {
  return new Intl.NumberFormat('es-CO').format(value)
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('es-CO', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function shortId(value: string) {
  return value.slice(0, 8)
}

function statusLabel(status: string) {
  switch (status) {
    case 'completed':
      return 'Completado'
    case 'completed_with_errors':
      return 'Completado con errores'
    case 'failed':
      return 'Fallido'
    case 'processing':
      return 'Procesando'
    default:
      return status
  }
}

interface InventorySectionProps {
  books: Book[]
  summary: InventorySummary | null
  items: InventoryItem[]
  batches: ImportBatch[]
  selectedBatchId: string | null
  selectedBatchErrors: ImportErrorRow[]
  fileName: string
  csvContent: string
  isLoading: boolean
  isSubmitting: boolean
  isLoadingErrors: boolean
  errorMessage: string | null
  successMessage: string | null
  onFileNameChange: (value: string) => void
  onCsvContentChange: (value: string) => void
  onFileChange: (event: ChangeEvent<HTMLInputElement>) => Promise<void>
  onImport: (event: FormEvent<HTMLFormElement>) => Promise<void>
  onSelectBatch: (batchId: string) => Promise<void>
  onResetSample: () => void
  onDeleteItem: (itemId: string) => Promise<void>
  onDeleteBatch: (batchId: string) => Promise<void>
}

export function InventorySection({
  books,
  summary,
  items,
  batches,
  selectedBatchId,
  selectedBatchErrors,
  fileName,
  csvContent,
  isLoading,
  isSubmitting,
  isLoadingErrors,
  errorMessage,
  successMessage,
  onFileNameChange,
  onCsvContentChange,
  onFileChange,
  onImport,
  onSelectBatch,
  onResetSample,
  onDeleteItem,
  onDeleteBatch,
}: InventorySectionProps) {
  const highlightedBatch =
    batches.find((batch) => batch.id === selectedBatchId) ?? batches[0] ?? null
  const catalogBookById = new Map(books.map((book) => [book.id, book]))

  return (
    <section className="service-section">
      <header className="service-header">
        <div>
          <p className="eyebrow">Sprint 1 - Dev2</p>
          <h2>Inventory Service</h2>
          <p className="service-copy">
            Carga masiva de inventario, disponibilidad real y trazabilidad por
            lote con persistencia propia.
          </p>
        </div>
        <div className="boundary-card compact">
          <span className="boundary-label">Dominio</span>
          <strong>Inventory</strong>
          <p>Acoplado por referencias, no por un esquema global unico.</p>
        </div>
      </header>

      <section className="summary-grid">
        <article className="summary-card">
          <span>Items</span>
          <strong>{formatNumber(summary?.total_items ?? 0)}</strong>
          <p>Registros persistidos en el servicio.</p>
        </article>
        <article className="summary-card">
          <span>Disponibles</span>
          <strong>{formatNumber(summary?.total_units_available ?? 0)}</strong>
          <p>Unidades listas para oferta o consulta.</p>
        </article>
        <article className="summary-card">
          <span>Reservadas</span>
          <strong>{formatNumber(summary?.total_units_reserved ?? 0)}</strong>
          <p>Separadas para flujos posteriores.</p>
        </article>
        <article className="summary-card">
          <span>Lotes</span>
          <strong>{formatNumber(summary?.total_batches ?? 0)}</strong>
          <p>{formatNumber(summary?.batches_with_errors ?? 0)} con errores.</p>
        </article>
      </section>

      {(errorMessage || successMessage) && (
        <section className="feedback-strip">
          {errorMessage && <p className="feedback-error">{errorMessage}</p>}
          {successMessage && <p className="feedback-success">{successMessage}</p>}
        </section>
      )}

      <section className="workspace-grid">
        <article className="panel import-panel">
          <div className="panel-heading">
            <div>
              <p className="panel-kicker">Carga masiva</p>
              <h3>Registrar inventario en lote</h3>
            </div>
            <label className="file-button">
              <input type="file" accept=".csv,text/csv" onChange={onFileChange} />
              Subir CSV
            </label>
          </div>

          <form className="import-form" onSubmit={onImport}>
            <label>
              Nombre del archivo
              <input
                type="text"
                value={fileName}
                onChange={(event) => onFileNameChange(event.target.value)}
                placeholder="inventory-sprint-1.csv"
              />
            </label>

            <label>
              Contenido CSV
              <textarea
                value={csvContent}
                onChange={(event) => onCsvContentChange(event.target.value)}
                spellCheck={false}
              />
            </label>

            <div className="form-actions">
              <button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Procesando lote...' : 'Importar inventario'}
              </button>
              <button className="ghost-button" type="button" onClick={onResetSample}>
                Restablecer ejemplo
              </button>
            </div>
          </form>

            <ul className="checklist">
              {csvChecklist.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>

            <div className="catalog-reference-box">
              <div className="panel-heading">
                <div>
                  <p className="panel-kicker">Relacion con Catalog</p>
                  <h4>Libros disponibles para book_reference</h4>
                </div>
                <span className="inline-chip">{books.length} libros</span>
              </div>
              {books.length === 0 ? (
                <p className="empty-copy">
                  Primero registra libros en Catalog Service. Inventory ahora valida
                  cada <code>book_reference</code> contra esos IDs.
                </p>
              ) : (
                <div className="catalog-reference-list">
                  {books.slice(0, 6).map((book) => (
                    <article key={book.id} className="reference-card">
                      <strong>{book.title}</strong>
                      <span>{book.author}</span>
                      <code>{book.id}</code>
                    </article>
                  ))}
                </div>
              )}
            </div>
          </article>

        <article className="panel model-panel">
          <div className="panel-heading">
            <div>
              <p className="panel-kicker">Modelo de datos</p>
              <h3>Entidades minimas del dominio</h3>
            </div>
            <span className="inline-chip">Persistencia propia</span>
          </div>

          <div className="model-grid">
            {modelCards.map((card) => (
              <section className="model-card" key={card.title}>
                <h4>{card.title}</h4>
                <p>{card.description}</p>
                <ul>
                  {card.fields.map((field) => (
                    <li key={field}>{field}</li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
        </article>
      </section>

      <section className="workspace-grid">
        <article className="panel table-panel">
          <div className="panel-heading">
            <div>
              <p className="panel-kicker">Inventario persistido</p>
              <h3>InventoryItem</h3>
            </div>
            <span className="inline-chip">
              {isLoading ? 'Cargando...' : `${items.length} registros`}
            </span>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>External code</th>
                  <th>Titulo</th>
                  <th>Book reference</th>
                  <th>Disponible</th>
                  <th>Reservado</th>
                  <th>Condicion</th>
                  <th>Lote</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {items.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="empty-cell">
                      Aun no hay inventario registrado.
                    </td>
                  </tr>
                ) : (
                  items.map((item) => {
                    const linkedBook = catalogBookById.get(item.book_reference)

                    return (
                    <tr key={item.id}>
                      <td>{item.external_code}</td>
                      <td>
                        {linkedBook ? linkedBook.title : 'Libro no encontrado'}
                      </td>
                      <td>{item.book_reference}</td>
                      <td>{formatNumber(item.quantity_available)}</td>
                      <td>{formatNumber(item.quantity_reserved)}</td>
                      <td>{item.condition}</td>
                      <td>{shortId(item.import_batch_id)}</td>
                      <td>
                        <button
                          type="button"
                          className="danger-button"
                          onClick={() => void onDeleteItem(item.id)}
                        >
                          Eliminar
                        </button>
                      </td>
                    </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </article>

        <article className="panel table-panel">
          <div className="panel-heading">
            <div>
              <p className="panel-kicker">Trazabilidad</p>
              <h3>ImportBatch e ImportError</h3>
            </div>
            {highlightedBatch && (
              <span className={`status-chip status-${highlightedBatch.status}`}>
                {statusLabel(highlightedBatch.status)}
              </span>
            )}
          </div>

          <div className="batch-list">
            {batches.length === 0 ? (
              <div className="empty-batches">No hay lotes procesados todavia.</div>
            ) : (
              batches.map((batch) => (
                <div
                  key={batch.id}
                  className={`batch-card${
                    batch.id === selectedBatchId ? ' batch-card-active' : ''
                  }`}
                >
                  <button
                    type="button"
                    className="batch-card-main"
                    onClick={() => void onSelectBatch(batch.id)}
                  >
                    <div>
                      <strong>{batch.file_name}</strong>
                      <p>{formatDate(batch.upload_date)}</p>
                    </div>
                    <div className="batch-metrics">
                      <span>{batch.valid_rows} validas</span>
                      <span>{batch.invalid_rows} invalidas</span>
                    </div>
                  </button>
                  <div className="batch-card-actions">
                      <button
                        type="button"
                        className="danger-button inline-danger"
                        onClick={() => void onDeleteBatch(batch.id)}
                      >
                        Eliminar lote
                      </button>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="error-box">
            <div className="error-box-header">
              <h4>Errores del lote seleccionado</h4>
              {selectedBatchId && <span>{shortId(selectedBatchId)}</span>}
            </div>

            {isLoadingErrors ? (
              <p className="empty-copy">Cargando errores...</p>
            ) : selectedBatchErrors.length === 0 ? (
              <p className="empty-copy">Este lote no tiene errores registrados.</p>
            ) : (
              <ul className="error-list">
                {selectedBatchErrors.map((error) => (
                  <li key={error.id}>
                    <strong>Fila {error.row_number}</strong>
                    <span>{error.error_type}</span>
                    <p>{error.message}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </article>
      </section>
    </section>
  )
}
