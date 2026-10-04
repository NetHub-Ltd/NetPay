import { useMemo, useState, type ReactNode } from 'react'

export type DataTableColumn<T> = {
  id: string
  header: string
  cell: (row: T) => ReactNode
  searchValue?: (row: T) => string
  className?: string
}

export type DataTableFilter = { id: string; label: string }

type Props<T> = {
  columns: DataTableColumn<T>[]
  rows: T[]
  getRowId: (row: T) => string
  searchPlaceholder?: string
  filters?: DataTableFilter[]
  filterFn?: (row: T, filterId: string) => boolean
  pageSizeOptions?: number[]
  defaultPageSize?: number
  maxHeight?: string
  emptyTitle?: string
  emptyHint?: string
  onRowClick?: (row: T) => void
  toolbarExtra?: ReactNode
}

const control = 'rounded-lg border border-[var(--border)] bg-[var(--panel)] px-3 py-2 text-sm text-[var(--text)] outline-none transition-shadow focus-visible:ring-2 focus-visible:ring-[var(--accent)]'

export function DataTable<T>({
  columns, rows, getRowId, searchPlaceholder = 'Search…', filters, filterFn,
  pageSizeOptions = [10, 25, 50], defaultPageSize = 10, maxHeight = 'min(420px, 55vh)',
  emptyTitle = 'No rows', emptyHint, onRowClick, toolbarExtra,
}: Props<T>) {
  const [q, setQ] = useState('')
  const [filterId, setFilterId] = useState('')
  const [pageSize, setPageSize] = useState(defaultPageSize)
  const [page, setPage] = useState(0)

  const filtered = useMemo(() => {
    let list = rows
    if (filterId && filterFn) list = list.filter((r) => filterFn(r, filterId))
    const needle = q.trim().toLowerCase()
    if (needle) {
      list = list.filter((r) => columns.some((c) => {
        const v = c.searchValue ? c.searchValue(r) : String(c.cell(r) ?? '')
        return v.toLowerCase().includes(needle)
      }))
    }
    return list
  }, [rows, q, filterId, filterFn, columns])

  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize))
  const safePage = Math.min(page, pageCount - 1)
  const slice = filtered.slice(safePage * pageSize, safePage * pageSize + pageSize)
  const from = filtered.length === 0 ? 0 : safePage * pageSize + 1
  const to = Math.min(filtered.length, safePage * pageSize + pageSize)

  return (
    <div className="overflow-hidden rounded-[var(--radius)] border border-[var(--border)] bg-[var(--panel)] shadow-[var(--shadow)]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] p-3">
        <input className={`${control} min-w-48 flex-1`} type="search" value={q}
          onChange={(e) => { setQ(e.target.value); setPage(0) }}
          placeholder={searchPlaceholder} aria-label="Search table" />
        <div className="flex flex-wrap items-center gap-2">
          {filters && filters.length > 0 && (
            <select className={control} value={filterId} onChange={(e) => { setFilterId(e.target.value); setPage(0) }} aria-label="Filter">
              <option value="">All</option>
              {filters.map((f) => <option key={f.id} value={f.id}>{f.label}</option>)}
            </select>
          )}
          <select className={control} value={pageSize} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(0) }} aria-label="Rows per page">
            {pageSizeOptions.map((n) => <option key={n} value={n}>{n} / page</option>)}
          </select>
          {toolbarExtra}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center px-6 py-12 text-center">
          <div className="text-sm font-semibold">{emptyTitle}</div>
          {emptyHint && <p className="mt-1 text-xs text-[var(--muted)]">{emptyHint}</p>}
        </div>
      ) : (
        <>
          <div className="overflow-auto" style={{ maxHeight }}>
            <table className="w-full border-collapse text-left text-sm">
              <thead className="sticky top-0 bg-[var(--panel-2)] text-xs uppercase tracking-wide text-[var(--muted)]">
                <tr>{columns.map((c) => <th key={c.id} className={`px-4 py-3 font-semibold ${c.className || ''}`}>{c.header}</th>)}</tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {slice.map((row) => (
                  <tr key={getRowId(row)}
                    className={`transition-colors hover:bg-[var(--panel-2)] ${onRowClick ? 'cursor-pointer focus-within:bg-[var(--panel-2)]' : ''}`}
                    onClick={onRowClick ? () => onRowClick(row) : undefined}>
                    {columns.map((c) => <td key={c.id} className={`px-4 py-3 align-middle ${c.className || ''}`}>{c.cell(row)}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--border)] px-4 py-3">
            <span className="text-xs text-[var(--muted)]">Showing {from}–{to} of {filtered.length}</span>
            <div className="flex items-center gap-3">
              <button type="button" className={`${control} font-medium disabled:cursor-not-allowed disabled:opacity-50`} disabled={safePage <= 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>Previous</button>
              <span className="text-xs text-[var(--muted)]">Page {safePage + 1} / {pageCount}</span>
              <button type="button" className={`${control} font-medium disabled:cursor-not-allowed disabled:opacity-50`} disabled={safePage >= pageCount - 1} onClick={() => setPage((p) => Math.min(pageCount - 1, p + 1))}>Next</button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
