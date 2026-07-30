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
}

/** Bordered table shell — pass columns + rows, cells render whatever you give (e.g. Badge). */
export function DataTable<T>({
  columns,
  rows,
  rowKey,
  onRowClick,
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
          {rows.map((row, index) => (
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
