import type { ReactNode } from "react";

export interface DataTableColumn<T> {
  key: string;
  label: ReactNode;
  render?: (row: T) => ReactNode;
}

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  onRowClick?: (row: T) => void;
  loading?: boolean;
  loadingRows?: number;
}

/** Bordered table shell — pass columns + rows, cells render whatever you give (e.g. Badge). */
export function DataTable<T>({
  columns,
  rows,
  rowKey,
  onRowClick,
  loading = false,
  loadingRows = 6,
}: DataTableProps<T>) {
  return (
    <div className="overflow-hidden rounded-lg border border-border-subtle bg-surface-card">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-surface-sunken">
            {columns.map((column) => (
              <th
                key={column.key}
                className="whitespace-nowrap border-b border-border-subtle px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-text-muted"
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading && Array.from({ length: loadingRows }, (_, row) => (
            <tr key={`loading-${row}`} aria-hidden="true" className="border-b border-border-subtle">
              {columns.map((column, index) => (
                <td key={column.key} className="px-4 py-3">
                  <span className="table-cell-skeleton" style={{ width: `${55 + ((row + index) * 13) % 40}%` }} />
                </td>
              ))}
            </tr>
          ))}
          {loading && <tr className="sr-only"><td colSpan={columns.length} role="status">Loading table data…</td></tr>}
          {!loading && rows.map((row, index) => (
            <tr
              key={rowKey(row)}
              onClick={() => onRowClick?.(row)}
              className={
                (onRowClick ? "cursor-pointer hover:bg-surface-hover " : "") +
                (index === rows.length - 1
                  ? ""
                  : "border-b border-border-subtle")
              }
            >
              {columns.map((column) => (
                <td
                  key={column.key}
                  className="px-4 py-3 align-middle text-base text-text-primary"
                >
                  {column.render
                    ? column.render(row)
                    : String(
                        (row as Record<string, unknown>)[column.key] ?? "",
                      )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
