import { useMemo, useRef } from "react";
import {
  type ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useVirtualizer } from "@tanstack/react-virtual";
import { CheckCircle, XCircle } from "lucide-react";
import { getBrandColor, getBrandName, ProviderLogo } from "@/components/provider-filter";
import type { TarifaItem } from "@/lib/types";

const moneyFormatter = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  maximumFractionDigits: 2,
});

function formatMoney(value: number | null | undefined) {
  if (typeof value !== "number" || isNaN(value)) return "-";
  return moneyFormatter.format(value);
}

function paymentType(item: TarifaItem) {
  if (item.es_prepago && item.es_pospago) return "Prepago/Pospago";
  if (item.es_prepago) return "Prepago";
  if (item.es_pospago) return "Pospago";
  return "-";
}

interface ResultsTableProps {
  items: TarifaItem[];
}

export function ResultsTable({ items }: ResultsTableProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const columns = useMemo<ColumnDef<TarifaItem>[]>(
    () => [
      {
        header: "Plan",
        accessorKey: "nombre_tarifa",
        cell: ({ row }) => (
          <div className="min-w-[180px] max-w-[220px]">
            <div className="truncate font-semibold text-slate-800 text-sm" title={row.original.nombre_tarifa || ""}>
              {row.original.nombre_tarifa || "Sin nombre"}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">{paymentType(row.original)}</div>
          </div>
        ),
      },
      {
        header: "Proveedor",
        id: "marca",
        cell: ({ row }) => {
          const brand = getBrandName(row.original.concesionario);
          const { bg } = getBrandColor(row.original.concesionario);
          return (
            <div className="flex items-center gap-2">
              <ProviderLogo concesionario={row.original.concesionario} size="sm" />
              <span className="text-sm font-semibold" style={{ color: bg }}>{brand}</span>
            </div>
          );
        },
      },
      {
        header: "Internet",
        id: "internet",
        cell: ({ row }) => {
          const cap = row.original.capacidad_incluida;
          const unit = row.original.capacidad_unidad_movil;
          if (cap && String(cap).trim() !== "") {
            return (
              <span className="font-bold text-blue-700 text-sm">
                {cap} {unit || ""}
              </span>
            );
          }
          return <span className="text-slate-300 text-sm">—</span>;
        },
      },
      {
        header: "Vigencia",
        id: "vigencia",
        cell: ({ row }) => {
          const v = row.original.vigencia_saldo_recarga;
          if (v && String(v).trim() && String(v).trim() !== "0") {
            return <span className="text-sm text-slate-700">{String(v)} días</span>;
          }
          return <span className="text-slate-300 text-sm">—</span>;
        },
      },
      {
        header: "Precio",
        accessorKey: "precio_real",
        cell: ({ row }) => (
          <div>
            <div className="font-bold text-slate-900">
              {formatMoney(row.original.precio_real)}
            </div>
            <div className="text-[10px] text-slate-400">
              {row.original.es_prepago ? "recarga" : row.original.es_pospago ? "/mes" : ""}
            </div>
          </div>
        ),
      },
      {
        header: "Estado",
        id: "estado",
        cell: ({ row }) =>
          row.original.estatus === "VIGENTE" ? (
            <span className="flex items-center gap-1 text-xs font-semibold text-emerald-600">
              <CheckCircle className="h-3.5 w-3.5" /> Vigente
            </span>
          ) : (
            <span className="flex items-center gap-1 text-xs font-semibold text-red-500">
              <XCircle className="h-3.5 w-3.5" /> No vigente
            </span>
          ),
      },
    ],
    [],
  );

  const table = useReactTable({
    data: items,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  const rows = table.getRowModel().rows;
  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => 68,
    overscan: 8,
  });

  const virtualRows = rowVirtualizer.getVirtualItems();
  const shouldVirtualize = rows.length > 0 && virtualRows.length > 0;
  const visibleRowIndexes = shouldVirtualize
    ? virtualRows.map((v) => v.index)
    : rows.map((_, i) => i);
  const topSpacer = shouldVirtualize ? virtualRows[0].index : 0;
  const bottomSpacer = shouldVirtualize
    ? rows.length - virtualRows[virtualRows.length - 1].index - 1
    : 0;

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
      <div ref={scrollRef} className="max-h-[560px] overflow-auto">
        <table className="min-w-full table-fixed text-left text-sm">
          <thead className="sticky top-0 z-10 bg-slate-50 text-xs uppercase tracking-widest text-slate-500 border-b border-slate-200">
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((header) => (
                  <th key={header.id} className="px-4 py-3 font-semibold">
                    {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {Array.from({ length: topSpacer }).map((_, i) => (
              <tr key={`ts-${i}`} className="h-[68px]"><td colSpan={6} /></tr>
            ))}

            {visibleRowIndexes.map((rowIndex) => {
              const row = rows[rowIndex];
              return (
                <tr
                  key={row.id}
                  className="h-[68px] border-t border-slate-100 transition-colors hover:bg-blue-50/40"
                  data-index={rowIndex}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3 align-middle">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              );
            })}

            {Array.from({ length: bottomSpacer }).map((_, i) => (
              <tr key={`bs-${i}`} className="h-[68px]"><td colSpan={6} /></tr>
            ))}

            {items.length === 0 && (
              <tr>
                <td className="px-4 py-12 text-center text-slate-400 italic" colSpan={6}>
                  No hay tarifas que coincidan con los filtros aplicados.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
