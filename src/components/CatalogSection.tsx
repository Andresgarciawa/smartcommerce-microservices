import type { FormEvent } from 'react'

import type { Book, CatalogSummary, Category } from '../types/catalog'

const modelCards = [
  {
    title: 'Book',
    description:
      'Ficha comercial base del producto bibliografico disponible para consulta, publicacion y consumo desde frontend o asistente.',
    fields: [
      'id',
      'title',
      'subtitle',
      'author',
      'publisher',
      'publication_year',
      'volume',
      'isbn',
      'issn',
      'category_id',
      'description',
      'cover_url',
      'enriched_flag',
      'published_flag',
    ],
  },
  {
    title: 'Category',
    description:
      'Clasificacion navegable del catalogo para organizar los productos bibliograficos por dominio o linea editorial.',
    fields: ['id', 'name', 'description'],
  },
]

function formatNumber(value: number) {
  return new Intl.NumberFormat('es-CO').format(value)
}

interface CatalogSectionProps {
  summary: CatalogSummary | null
  categories: Category[]
  books: Book[]
  categoryForm: {
    name: string
    description: string
  }
  bookForm: {
    title: string
    subtitle: string
    author: string
    publisher: string
    publication_year: string
    volume: string
    isbn: string
    issn: string
    category_id: string
    description: string
    cover_url: string
    enriched_flag: boolean
    published_flag: boolean
  }
  isLoading: boolean
  isCreatingCategory: boolean
  isCreatingBook: boolean
  errorMessage: string | null
  successMessage: string | null
  onCategoryFieldChange: (field: 'name' | 'description', value: string) => void
  onBookFieldChange: (field: string, value: string | boolean) => void
  onCreateCategory: (event: FormEvent<HTMLFormElement>) => Promise<void>
  onCreateBook: (event: FormEvent<HTMLFormElement>) => Promise<void>
  onDeleteCategory: (categoryId: string) => Promise<void>
  onDeleteBook: (bookId: string) => Promise<void>
}

export function CatalogSection({
  summary,
  categories,
  books,
  categoryForm,
  bookForm,
  isLoading,
  isCreatingCategory,
  isCreatingBook,
  errorMessage,
  successMessage,
  onCategoryFieldChange,
  onBookFieldChange,
  onCreateCategory,
  onCreateBook,
  onDeleteCategory,
  onDeleteBook,
}: CatalogSectionProps) {
  return (
    <section className="service-section">
      <header className="service-header">
        <div>
          <p className="eyebrow">Sprint 1 - Dev3</p>
          <h2>Catalog Service</h2>
          <p className="service-copy">
            Registro y consulta de productos bibliograficos con persistencia
            propia, categorias navegables y metadatos listos para publicacion.
          </p>
        </div>
        <div className="boundary-card compact">
          <span className="boundary-label">Dominio</span>
          <strong>Catalog</strong>
          <p>Modelo autonomo del producto, separado del inventario fisico.</p>
        </div>
      </header>

      <section className="summary-grid">
        <article className="summary-card">
          <span>Categorias</span>
          <strong>{formatNumber(summary?.total_categories ?? 0)}</strong>
          <p>Clasificaciones disponibles en el catalogo.</p>
        </article>
        <article className="summary-card">
          <span>Libros</span>
          <strong>{formatNumber(summary?.total_books ?? 0)}</strong>
          <p>Productos bibliograficos registrados.</p>
        </article>
        <article className="summary-card">
          <span>Publicados</span>
          <strong>{formatNumber(summary?.published_books ?? 0)}</strong>
          <p>Listos para consumo por clientes o asistentes.</p>
        </article>
        <article className="summary-card">
          <span>Enriquecidos</span>
          <strong>{formatNumber(summary?.enriched_books ?? 0)}</strong>
          <p>Con metadatos enriquecidos en el flujo editorial.</p>
        </article>
      </section>

      {(errorMessage || successMessage) && (
        <section className="feedback-strip">
          {errorMessage && <p className="feedback-error">{errorMessage}</p>}
          {successMessage && <p className="feedback-success">{successMessage}</p>}
        </section>
      )}

      <section className="workspace-grid">
        <article className="panel stacked-panel">
          <div className="panel-heading">
            <div>
              <p className="panel-kicker">Registro</p>
              <h3>Crear categoria</h3>
            </div>
            <span className="inline-chip">Persistencia propia</span>
          </div>

          <form className="import-form compact-form" onSubmit={onCreateCategory}>
            <label>
              Nombre
              <input
                type="text"
                value={categoryForm.name}
                onChange={(event) =>
                  onCategoryFieldChange('name', event.target.value)
                }
                placeholder="Narrativa latinoamericana"
              />
            </label>

            <label>
              Descripcion
              <textarea
                value={categoryForm.description}
                onChange={(event) =>
                  onCategoryFieldChange('description', event.target.value)
                }
                spellCheck={false}
              />
            </label>

            <div className="form-actions">
              <button type="submit" disabled={isCreatingCategory}>
                {isCreatingCategory ? 'Guardando...' : 'Crear categoria'}
              </button>
            </div>
          </form>

          <div className="divider" />

          <div className="panel-heading">
            <div>
              <p className="panel-kicker">Registro</p>
              <h3>Crear libro</h3>
            </div>
            <span className="inline-chip">
              {categories.length} categorias disponibles
            </span>
          </div>

          <form className="book-form" onSubmit={onCreateBook}>
            <div className="field-grid">
              <label>
                Titulo
                <input
                  type="text"
                  value={bookForm.title}
                  onChange={(event) => onBookFieldChange('title', event.target.value)}
                  placeholder="Cien anos de soledad"
                />
              </label>
              <label>
                Subtitulo
                <input
                  type="text"
                  value={bookForm.subtitle}
                  onChange={(event) =>
                    onBookFieldChange('subtitle', event.target.value)
                  }
                />
              </label>
              <label>
                Autor
                <input
                  type="text"
                  value={bookForm.author}
                  onChange={(event) => onBookFieldChange('author', event.target.value)}
                  placeholder="Gabriel Garcia Marquez"
                />
              </label>
              <label>
                Editorial
                <input
                  type="text"
                  value={bookForm.publisher}
                  onChange={(event) =>
                    onBookFieldChange('publisher', event.target.value)
                  }
                  placeholder="Sudamericana"
                />
              </label>
              <label>
                Anio de publicacion
                <input
                  type="number"
                  value={bookForm.publication_year}
                  onChange={(event) =>
                    onBookFieldChange('publication_year', event.target.value)
                  }
                  min="1000"
                  max="2100"
                />
              </label>
              <label>
                Volumen
                <input
                  type="text"
                  value={bookForm.volume}
                  onChange={(event) => onBookFieldChange('volume', event.target.value)}
                />
              </label>
              <label>
                ISBN
                <input
                  type="text"
                  value={bookForm.isbn}
                  onChange={(event) => onBookFieldChange('isbn', event.target.value)}
                />
              </label>
              <label>
                ISSN
                <input
                  type="text"
                  value={bookForm.issn}
                  onChange={(event) => onBookFieldChange('issn', event.target.value)}
                />
              </label>
              <label className="field-span-2">
                Categoria
                <select
                  value={bookForm.category_id}
                  onChange={(event) =>
                    onBookFieldChange('category_id', event.target.value)
                  }
                  disabled={categories.length === 0}
                >
                  <option value="">Selecciona una categoria</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field-span-2">
                Cover URL
                <input
                  type="url"
                  value={bookForm.cover_url}
                  onChange={(event) =>
                    onBookFieldChange('cover_url', event.target.value)
                  }
                  placeholder="https://..."
                />
              </label>
              <label className="field-span-2">
                Descripcion
                <textarea
                  value={bookForm.description}
                  onChange={(event) =>
                    onBookFieldChange('description', event.target.value)
                  }
                  spellCheck={false}
                />
              </label>
            </div>

            <div className="toggle-row">
              <label className="toggle-field">
                <input
                  type="checkbox"
                  checked={bookForm.enriched_flag}
                  onChange={(event) =>
                    onBookFieldChange('enriched_flag', event.target.checked)
                  }
                />
                Enriquecido
              </label>
              <label className="toggle-field">
                <input
                  type="checkbox"
                  checked={bookForm.published_flag}
                  onChange={(event) =>
                    onBookFieldChange('published_flag', event.target.checked)
                  }
                />
                Publicado
              </label>
            </div>

            <div className="form-actions">
              <button
                type="submit"
                disabled={isCreatingBook || categories.length === 0}
              >
                {isCreatingBook ? 'Guardando libro...' : 'Crear libro'}
              </button>
            </div>
          </form>
        </article>

        <article className="panel model-panel">
          <div className="panel-heading">
            <div>
              <p className="panel-kicker">Modelo de datos</p>
              <h3>Entidades del catalogo</h3>
            </div>
            <span className="inline-chip">Consulta y publicacion</span>
          </div>

          <div className="model-grid catalog-model-grid">
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
              <p className="panel-kicker">Categorias</p>
              <h3>Category</h3>
            </div>
            <span className="inline-chip">
              {isLoading ? 'Cargando...' : `${categories.length} registros`}
            </span>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Descripcion</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {categories.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="empty-cell">
                      Aun no hay categorias registradas.
                    </td>
                  </tr>
                ) : (
                  categories.map((category) => (
                    <tr key={category.id}>
                      <td>{category.name}</td>
                      <td>{category.description || 'Sin descripcion'}</td>
                      <td>
                        <button
                          type="button"
                          className="danger-button"
                          onClick={() => void onDeleteCategory(category.id)}
                        >
                          Eliminar
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </article>

        <article className="panel table-panel">
          <div className="panel-heading">
            <div>
              <p className="panel-kicker">Catalogo persistido</p>
              <h3>Book</h3>
            </div>
            <span className="inline-chip">
              {isLoading ? 'Cargando...' : `${books.length} registros`}
            </span>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Titulo</th>
                  <th>Autor</th>
                  <th>Editorial</th>
                  <th>Anio</th>
                  <th>Categoria</th>
                  <th>Inventario</th>
                  <th>Flags</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {books.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="empty-cell">
                      Aun no hay libros registrados.
                    </td>
                  </tr>
                ) : (
                  books.map((book) => (
                    <tr key={book.id}>
                      <td>{book.title}</td>
                      <td>{book.author}</td>
                      <td>{book.publisher}</td>
                      <td>{book.publication_year}</td>
                      <td>{book.category_name}</td>
                      <td>
                        <div className="inventory-badge-stack">
                          <span className="inline-chip">
                            Disp. {book.quantity_available_total}
                          </span>
                          <span className="inline-chip">
                            Res. {book.quantity_reserved_total}
                          </span>
                          <span className="inline-chip">
                            Reg. {book.inventory_records}
                          </span>
                          <span
                            className={`inline-chip${
                              book.inventory_sync ? '' : ' warning-chip'
                            }`}
                          >
                            {book.inventory_sync ? 'Sincronizado' : 'Sin sync'}
                          </span>
                        </div>
                      </td>
                      <td>
                        <div className="flag-row">
                          {book.enriched_flag && <span className="inline-chip">Enriquecido</span>}
                          {book.published_flag && <span className="inline-chip">Publicado</span>}
                          {!book.enriched_flag && !book.published_flag && (
                            <span className="inline-chip">Base</span>
                          )}
                        </div>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="danger-button"
                          onClick={() => void onDeleteBook(book.id)}
                        >
                          Eliminar
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </article>
      </section>
    </section>
  )
}
