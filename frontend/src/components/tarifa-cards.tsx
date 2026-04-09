import { Clock, Share2, Wifi, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { getBrandColor, getBrandName, ProviderLogo } from "@/components/provider-filter";
import type { TarifaItem } from "@/lib/types";

const moneyFormatter = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  maximumFractionDigits: 2,
});

function formatMoney(value: number | null | undefined) {
  if (typeof value !== "number" || isNaN(value)) return "Sin precio";
  return moneyFormatter.format(value);
}

function paymentLabel(item: TarifaItem): { label: string; color: string } {
  if (item.es_prepago && item.es_pospago) return { label: "Prepago / Pospago", color: "bg-purple-100 text-purple-700" };
  if (item.es_prepago) return { label: "Prepago · Recarga", color: "bg-amber-100 text-amber-700" };
  if (item.es_pospago) return { label: "Pospago · Mensual", color: "bg-blue-100 text-blue-700" };
  return { label: "No especificado", color: "bg-slate-100 text-slate-600" };
}

function DataBadge({ value, unit }: { value: string | number | null; unit: string | null }) {
  if (!value || String(value).trim() === "") {
    return (
      <div className="flex items-center gap-1.5 text-slate-400">
        <Wifi className="h-4 w-4" />
        <span className="text-sm">No especificado</span>
      </div>
    );
  }
  const numStr = String(value).replace(/[^0-9.]/g, "");
  const num = parseFloat(numStr);
  const isBig = !isNaN(num) && (num >= 1024 || (unit ?? "").toUpperCase().includes("GB"));

  return (
    <div className="flex items-baseline gap-1">
      <span className={`font-display font-black tracking-tight leading-none ${isBig ? "text-4xl text-blue-700" : "text-2xl text-slate-800"}`}>
        {value}
      </span>
      {unit && (
        <span className="text-sm font-semibold text-slate-500 uppercase">{unit}</span>
      )}
    </div>
  );
}

function SocialNetworks({ value }: { value: string | null }) {
  if (!value || String(value).trim() === "") return null;
  const networks = String(value).split(/[,;]/);
  return (
    <div className="flex items-start gap-1.5">
      <Share2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-400" />
      <div className="flex flex-wrap gap-1">
        {networks.map((net, i) => (
          <span
            key={i}
            className="inline-block rounded-full bg-blue-50 px-2 py-0.5 text-[10px] font-semibold text-blue-700 border border-blue-100"
          >
            {net.trim()}
          </span>
        ))}
      </div>
    </div>
  );
}

interface TarifaCardsProps {
  items: TarifaItem[];
  topMode?: boolean;
}

export function TarifaCards({ items, topMode = false }: TarifaCardsProps) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-white px-6 py-16 text-center shadow-sm animate-fade-up">
        <AlertCircle className="mb-4 h-12 w-12 text-slate-300" />
        <p className="text-lg font-semibold text-slate-500">Sin resultados</p>
        <p className="mt-1 text-sm text-slate-400">Intenta ajustar los filtros de búsqueda.</p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {items.map((item, index) => {
        const brand = getBrandName(item.concesionario);
        const { bg } = getBrandColor(item.concesionario);
        const { label: payLabel, color: payColor } = paymentLabel(item);
        const price = item.precio_real;
        const hasPrice = typeof price === "number" && !isNaN(price);

        return (
          <article
            key={item.id_tarifa}
            className="tarifa-card animate-fade-up shadow-card"
            style={{ animationDelay: `${Math.min(index * 40, 400)}ms` }}
          >
            {/* Brand stripe */}
            <div
              className="flex items-center justify-between px-4 py-2.5"
              style={{ backgroundColor: `${bg}18`, borderBottom: `3px solid ${bg}` }}
            >
              <div className="flex items-center gap-2.5">
                <ProviderLogo concesionario={item.concesionario} size="sm" />
                <span className="text-sm font-bold" style={{ color: bg }}>{brand}</span>
              </div>
              {topMode && (
                <span className="font-display text-2xl font-black" style={{ color: bg }}>
                  #{index + 1}
                </span>
              )}
            </div>

            {/* Plan name */}
            <div className="px-4 pt-3 pb-2">
              <h3 className="line-clamp-2 text-sm font-semibold text-slate-800 leading-snug" title={item.nombre_tarifa || ""}>
                {item.nombre_tarifa || "Tarifa sin nombre"}
              </h3>
              <span className={`mt-1 inline-block rounded-full px-2 py-0.5 text-[10px] font-bold ${payColor}`}>
                {payLabel}
              </span>
            </div>

            {/* Internet capacity — the hero element */}
            <div className="border-y border-slate-100 bg-slate-50/60 px-4 py-4 text-center">
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
                Internet incluido
              </p>
              <DataBadge value={item.capacidad_incluida} unit={item.capacidad_unidad_movil} />
            </div>

            {/* Details */}
            <div className="flex-1 space-y-2.5 px-4 py-3">
              {/* Social networks */}
              <SocialNetworks value={item.redes_sociales} />

              {/* Validity */}
              {item.vigencia_saldo_recarga && String(item.vigencia_saldo_recarga).trim() && (
                <div className="flex items-center gap-1.5 text-xs text-slate-500">
                  <Clock className="h-3.5 w-3.5 text-slate-400" />
                  <span>Vigencia: <strong className="text-slate-700">{item.vigencia_saldo_recarga} días</strong></span>
                </div>
              )}
            </div>

            {/* Price footer */}
            <div className="border-t border-slate-100 bg-slate-50 px-4 py-3 flex items-center justify-between">
              <div>
                {hasPrice ? (
                  <>
                    <span className="font-display text-2xl font-black text-slate-900">
                      {formatMoney(price)}
                    </span>
                    <span className="ml-1.5 text-xs font-medium text-slate-500">
                      {item.es_prepago ? "recarga" : "/mes"}
                    </span>
                  </>
                ) : (
                  <span className="text-sm text-slate-400 italic">Precio no disponible</span>
                )}
              </div>
              {item.estatus === "VIGENTE" ? (
                <span className="flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200">
                  <CheckCircle className="h-3 w-3" />
                  Vigente
                </span>
              ) : (
                <span className="flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-[10px] font-bold text-red-600 border border-red-200">
                  <XCircle className="h-3 w-3" />
                  No vigente
                </span>
              )}
            </div>
          </article>
        );
      })}
    </div>
  );
}
