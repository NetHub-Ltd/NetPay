import { useMemo, useState, type ReactNode } from 'react'

export type DataTableColumn<T> = {
  id: string
  header: string
  cell: (row: T) => ReactNode
  /** Optional plain-text value for search */
  searchValue?: (row: T) => string
  className?: string
}

export type DataTableFilter = {
  id: string
  label: string
}

type Props<T> = {
  columns: DataTableColumn<T>[]
  rows: T[]
  getRowId: (row: T) => string
  searchPlaceholder?: string
  filters?: DataTableFilter[]
  /** Return true to keep row for active filter id ('' = all) */
  filterFn?: (row: T, filterId: string) => boolean
  pageSizeOptions?: number[]
  defaultPageSize?: number
  maxHeight?: string
  emptyTitle?: string
  emptyHint?: string
  onRowClick?: (row: T) => void
  toolbarExtra?: ReactNode
}

export function DataTable<T>({
  columns,
  rows,
  getRowId,
  searchPlaceholder = 'Search…',
  filters,
  filterFn,
  pageSizeOptions = [10, 25, 50],
  defaultPageSize = 10,
  maxHeight = 'min(420px, 55vh)',
  emptyTitle = 'No rows',
  emptyHint,
  onRowClick,
  toolbarExtra,
}: Props<T>) {
  const [q, setQ] = useState('')
  const [filterId, setFilterId] = useState('')
  const [pageSize, setPageSize] = useState(defaultPageSize)
  const [page, setPage] = useState(0)

  const filtered = useMemo(() => {
    let list = rows
    if (filterId && filterFn) {
      list = list.filter((r) => filterFn(r, filterId))
    }
    const needle = q.trim().toLowerCase()
    if (needle) {
      list = list.filter((r) =>
        columns.some((c) => {
          const v = c.searchValue ? c.searchValue(r) : String(c.cell(r) ?? '')
          return v.toLowerCase().includes(needle)
        }),
      )
    }
    return list
  }, [rows, q, filterId, filterFn, columns])

  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize))
  const safePage = Math.min(page, pageCount - 1)
  const slice = filtered.slice(safePage * pageSize, safePage * pageSize + pageSize)
  const from = filtered.length === 0 ? 0 : safePage * pageSize + 1
  const to = Math.min(filtered.length, safePage * pageSize + pageSize)

  return (
    <div className="data-table">
      <div className="data-table-toolbar">
        <input
          className="data-table-search"
          type="search"
          value={q}
          onChange={(e) => {
            setQ(e.target.value)
            setPage(0)
          }}
          placeholder={searchPlaceholder}
          aria-label="Search table"
        />
        <div className="data-table-toolbar-right">
          {filters && filters.length > 0 && (
            <select
              className="data-table-select"
              value={filterId}
              onChange={(e) => {
                setFilterId(e.target.value)
                setPage(0)
              }}
              aria-label="Filter"
            >
              <option value="">All</option>
              {filters.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.label}
                </option>
              ))}
            </select>
          )}
          <select
            className="data-table-select"
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value))
              setPage(0)
            }}
            aria-label="Rows per page"
          >
            {pageSizeOptions.map((n) => (
              <option key={n} value={n}>
                {n} / page
              </option>
            ))}
          </select>
          {toolbarExtra}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="data-table-empty">
          <div className="data-table-empty-title">{emptyTitle}</div>
          {emptyHint && <p className="muted tiny">{emptyHint}</p>}
        </div>
      ) : (
        <>
          <div className="data-table-scroll" style={{ maxHeight }}>
            <table>
              <thead>
                <tr>
                  {columns.map((c) => (
                    <th key={c.id} className={c.className}>
                      {c.header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {slice.map((row) => (
                  <tr
                    key={getRowId(row)}
                    className={onRowClick ? 'data-table-row-click' : undefined}
                    onClick={onRowClick ? () => onRowClick(row) : undefined}
                  >
                    {columns.map((c) => (
                      <td key={c.id} className={c.className}>
                        {c.cell(row)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="data-table-footer">
            <span className="muted tiny">
              Showing {from}–{to} of {filtered.length}
            </span>
            <div className="data-table-pager">
              <button
                type="button"
                className="btn"
                disabled={safePage <= 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                Previous
              </button>
              <span className="tiny muted">
                Page {safePage + 1} / {pageCount}
              </span>
              <button
                type="button"
                className="btn"
                disabled={safePage >= pageCount - 1}
                onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
