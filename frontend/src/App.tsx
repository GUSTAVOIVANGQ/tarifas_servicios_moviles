import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  LayoutGrid,
  List,
  LoaderCircle,
  RotateCcw,
  Search as SearchIcon,
  X,
  ArrowDownUp,
  Filter,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

import { IftHeader } from "@/components/ift-header";
import { ProviderFilter } from "@/components/provider-filter";
import { ResultsTable } from "@/components/results-table";
import { TarifaCards } from "@/components/tarifa-cards";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { fetchFilters, searchTarifas } from "@/lib/api";
import type { SearchFilters, SortBy, SortDir } from "@/lib/types";
import { cn } from "@/lib/utils";

type DisplayMode = "cards" | "table";

const PRICE_PRESETS = [
  { label: "Hasta $100", min: null, max: 100 },
  { label: "$100 – $250", min: 100, max: 250 },
  { label: "$250 – $500", min: 250, max: 500 },
  { label: "$500+", min: 500, max: null },
];

const PAYMENT_OPTIONS = [
  { value: "todos", label: "Todos los tipos" },
  { value: "prepago", label: "Prepago / Recargas" },
  { value: "pospago", label: "Pospago / Mensual" },
] as const;

function createEmptyFilters(): SearchFilters {
  return { 
    operador: [], 
    concesionario: [], 
    tipo_pago: "todos", 
    min_precio: null, 
    max_precio: null, 
    min_gigas: null,
    redes_sociales: false,
    min_vigencia_dias: null,
    q: "" 
  };
}

const moneyFormatter = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 });

export default function App() {
  const [draft, setDraft] = useState<SearchFilters>(() => createEmptyFilters());
  const [applied, setApplied] = useState<SearchFilters>(() => createEmptyFilters());
  const [displayMode, setDisplayMode] = useState<DisplayMode>("cards");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [sortBy, setSortBy] = useState<SortBy>("precio");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [activePricePreset, setActivePricePreset] = useState<number | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const debouncedText = useDebouncedValue(draft.q, 300);

  useEffect(() => {
    setApplied((p) => ({ ...p, q: debouncedText.trim() }));
    setPage(1);
  }, [debouncedText]);

  const filtersQuery = useQuery({ queryKey: ["filters"], queryFn: fetchFilters });

  const searchQuery = useQuery({
    queryKey: ["search", applied, page, pageSize, sortBy, sortDir],
    queryFn: () => searchTarifas({ ...applied, page, page_size: pageSize, sort_by: sortBy, sort_dir: sortDir }),
    placeholderData: (p) => p,
  });

  const totalShown = searchQuery.data?.total ?? 0;
  const isRefreshing = searchQuery.isFetching && !searchQuery.isLoading;

  function applyFilters() {
    setApplied({ ...draft, q: debouncedText.trim() });
    setPage(1);
  }

  function clearAll() {
    const empty = createEmptyFilters();
    setDraft(empty);
    setApplied(empty);
    setPage(1);
    setSortBy("precio");
    setSortDir("asc");
    setActivePricePreset(null);
  }

  function applyPreset(idx: number | string) {
    if (idx === "all") {
      setActivePricePreset(null);
      setDraft((p) => ({ ...p, min_precio: null, max_precio: null }));
      setApplied((p) => ({ ...p, min_precio: null, max_precio: null }));
      setPage(1);
      return;
    }
    
    const index = Number(idx);
    const preset = PRICE_PRESETS[index];
    setActivePricePreset(index);
    setDraft((p) => ({ ...p, min_precio: preset.min, max_precio: preset.max }));
    setApplied((p) => ({ ...p, min_precio: preset.min, max_precio: preset.max }));
    setPage(1);
  }

  function handleProviderChange(concesionarios: string[]) {
    setDraft((p) => ({ ...p, concesionario: concesionarios }));
    setApplied((p) => ({ ...p, concesionario: concesionarios }));
    setPage(1);
  }

  function handlePaymentType(value: string) {
    setDraft((p) => ({ ...p, tipo_pago: value as SearchFilters["tipo_pago"] }));
    setApplied((p) => ({ ...p, tipo_pago: value as SearchFilters["tipo_pago"] }));
    setPage(1);
  }

  // Active filter chips (for top bar)
  const activeChips = useMemo(() => {
    const chips: { id: string; label: string; clear: () => void }[] = [];
    if (applied.concesionario.length > 0) chips.push({ id: "prov", label: `${applied.concesionario.length} proveedor(es)`, clear: () => handleProviderChange([]) });
    if (applied.tipo_pago !== "todos") chips.push({ id: "tipo", label: applied.tipo_pago.charAt(0).toUpperCase() + applied.tipo_pago.slice(1), clear: () => handlePaymentType("todos") });
    if (applied.min_precio !== null || applied.max_precio !== null) {
      const mn = applied.min_precio !== null ? moneyFormatter.format(applied.min_precio) : "—";
      const mx = applied.max_precio !== null ? moneyFormatter.format(applied.max_precio) : "—";
      chips.push({ id: "price", label: `Precio ${mn} – ${mx}`, clear: () => applyPreset("all") });
    }
    if (applied.min_gigas !== null) {
      chips.push({ id: "gigas", label: `${applied.min_gigas}GB+`, clear: () => { setDraft((p) => ({ ...p, min_gigas: null })); setApplied((p) => ({ ...p, min_gigas: null })); setPage(1); } });
    }
    if (applied.redes_sociales) {
      chips.push({ id: "redes", label: "Redes Soc.", clear: () => { setDraft((p) => ({ ...p, redes_sociales: false })); setApplied((p) => ({ ...p, redes_sociales: false })); setPage(1); } });
    }
    if (applied.min_vigencia_dias !== null) {
      chips.push({ id: "vigencia", label: `${applied.min_vigencia_dias} Días+`, clear: () => { setDraft((p) => ({ ...p, min_vigencia_dias: null })); setApplied((p) => ({ ...p, min_vigencia_dias: null })); setPage(1); } });
    }
    if (applied.q.trim()) chips.push({ id: "q", label: `"${applied.q.trim()}"`, clear: () => { setDraft((p) => ({ ...p, q: "" })); setApplied((p) => ({ ...p, q: "" })); setPage(1); } });
    return chips;
  }, [applied]);

  const searchItems = searchQuery.data?.items || [];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Institutional header */}
      <IftHeader />

      {/* Hero Search Section - ULTRA CLEAN */}
      <section className="search-hero py-12 px-4 shadow-sm border-b border-blue-900/50">
        <div className="mx-auto max-w-4xl space-y-8">
          <div className="text-center">
            <h1 className="font-display text-4xl font-black text-white drop-shadow-sm lg:text-5xl">
              ¿Qué plan móvil estás buscando?
            </h1>
            <p className="mt-4 text-base text-blue-200">
              {filtersQuery.isSuccess
                ? `Explora más de ${totalShown.toLocaleString("es-MX")} tarifas vigentes de ${filtersQuery.data.concesionarios.length} proveedores registrados`
                : "Cargando datos del registro IFT..."}
            </p>
          </div>

          <form
            onSubmit={(e) => { e.preventDefault(); applyFilters(); }}
            className="relative flex items-center mx-auto max-w-2xl"
          >
            <SearchIcon className="pointer-events-none absolute left-6 h-6 w-6 text-slate-400" />
            <input
              id="hero-search"
              className="w-full rounded-2xl border-0 bg-white py-4 pl-16 pr-32 text-lg font-medium text-slate-900 shadow-xl placeholder:text-slate-400 focus:outline-none focus:ring-4 focus:ring-blue-500/30"
              value={draft.q}
              onChange={(e) => setDraft((p) => ({ ...p, q: e.target.value }))}
              placeholder="Ej. Plan ilimitado, Telcel, Redes Sociales..."
              autoComplete="off"
            />
            <button
              type="submit"
              className="absolute right-3 rounded-xl bg-blue-700 px-6 py-2.5 text-sm font-bold text-white transition hover:bg-blue-800 active:scale-95 shadow-md"
            >
              Buscar
            </button>
          </form>
        </div>
      </section>

      {/* Main Layout: Sidebar + Results */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <div className="grid grid-cols-1 items-start gap-8 lg:grid-cols-[280px_1fr]">
          
          {/* LEFT SIDEBAR: Filters */}
          <aside className="w-full shrink-0">
            <div className="sticky top-6 space-y-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center gap-2 border-b border-slate-100 pb-4">
                <Filter className="h-5 w-5 text-slate-400" />
                <h2 className="font-display text-lg font-bold text-slate-800">Filtrar Búsqueda</h2>
              </div>

              {/* Provider dropdown */}
              <div>
                <label className="mb-2 block text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  Compañía Proveedora
                </label>
                {filtersQuery.isSuccess ? (
                  <ProviderFilter
                    selected={applied.concesionario}
                    onChange={handleProviderChange}
                    concesionarios={filtersQuery.data.concesionarios}
                  />
                ) : (
                  <div className="h-10 w-full animate-pulse rounded-lg bg-slate-100" />
                )}
              </div>

              {/* Payment Type dropdown */}
              <div>
                <label className="mb-2 block text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  Modalidad de Pago
                </label>
                <Select
                  value={applied.tipo_pago}
                  onChange={(e) => handlePaymentType(e.target.value)}
                  className="font-medium text-slate-700 bg-white"
                >
                  {PAYMENT_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </Select>
              </div>

              {/* Price Preset dropdown */}
              <div>
                <label className="mb-2 block text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  Rango de Precio
                </label>
                <Select
                  value={activePricePreset === null ? "all" : activePricePreset.toString()}
                  onChange={(e) => applyPreset(e.target.value)}
                  className="font-medium text-slate-700 bg-white"
                >
                  <option value="all">Cualquier precio</option>
                  {PRICE_PRESETS.map((preset, idx) => (
                    <option key={idx} value={idx.toString()}>
                      {preset.label}
                    </option>
                  ))}
                </Select>
              </div>

              {/* Advanced Filters Toggle */}
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex w-full items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-xs font-bold uppercase tracking-wide text-slate-600 transition-colors hover:bg-slate-100"
                >
                  Opciones Avanzadas
                  {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>
              </div>

              {/* Advanced Filters Content */}
              {showAdvanced && (
                <div className="space-y-5 rounded-xl border border-slate-100 bg-slate-50 p-4 animate-slide-in">
                  
                  {/* Min Gigas */}
                  <div>
                    <label className="mb-2 block text-[11px] font-bold uppercase tracking-wider text-slate-500">
                      Internet Incluido
                    </label>
                    <Select
                      value={draft.min_gigas === null ? "all" : draft.min_gigas.toString()}
                      onChange={(e) => {
                        const val = e.target.value === "all" ? null : Number(e.target.value);
                        setDraft((p) => ({ ...p, min_gigas: val }));
                        setApplied((p) => ({ ...p, min_gigas: val }));
                        setPage(1);
                      }}
                      className="text-sm shadow-sm"
                    >
                      <option value="all">Ver todas</option>
                      <option value="1">1 GB o más</option>
                      <option value="3">3 GB o más</option>
                      <option value="5">5 GB o más</option>
                      <option value="10">10 GB o más</option>
                      <option value="999">Plan Ilimitado</option>
                    </Select>
                  </div>

                  {/* Redes Sociales */}
                  <div>
                    <label className="flex cursor-pointer items-center gap-3">
                      <div className="relative flex items-center">
                        <input
                          type="checkbox"
                          className="peer h-5 w-5 cursor-pointer appearance-none rounded border-2 border-slate-300 bg-white transition-all checked:border-blue-600 checked:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
                          checked={draft.redes_sociales}
                          onChange={(e) => {
                            setDraft((p) => ({ ...p, redes_sociales: e.target.checked }));
                            setApplied((p) => ({ ...p, redes_sociales: e.target.checked }));
                            setPage(1);
                          }}
                        />
                        <div className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-white opacity-0 transition-opacity peer-checked:opacity-100">
                          <svg className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        </div>
                      </div>
                      <span className="text-sm font-semibold text-slate-700">Incluye Redes Sociales</span>
                    </label>
                  </div>

                  {/* Vigencia */}
                  {applied.tipo_pago !== "pospago" && (
                    <div>
                      <label className="mb-2 block text-[11px] font-bold uppercase tracking-wider text-slate-500">
                        Vigencia mínima (Días)
                      </label>
                      <Select
                        value={draft.min_vigencia_dias === null ? "all" : draft.min_vigencia_dias.toString()}
                        onChange={(e) => {
                          const val = e.target.value === "all" ? null : Number(e.target.value);
                          setDraft((p) => ({ ...p, min_vigencia_dias: val }));
                          setApplied((p) => ({ ...p, min_vigencia_dias: val }));
                          setPage(1);
                        }}
                        className="text-sm shadow-sm"
                      >
                        <option value="all">Cualquier vigencia</option>
                        <option value="7">7 días o más</option>
                        <option value="15">15 días o más</option>
                        <option value="30">30 días o más</option>
                      </Select>
                    </div>
                  )}

                </div>
              )}

              <div className="pt-4 mt-2 border-t border-slate-100">
                <Button 
                  variant="outline" 
                  className="w-full text-slate-600 hover:text-slate-900 shadow-sm" 
                  onClick={clearAll}
                >
                  <RotateCcw className="mr-2 h-4 w-4" />
                  Restablecer
                </Button>
              </div>
            </div>
          </aside>

          {/* RIGHT COLUMN: Results Section */}
          <div className="min-w-0 flex-1 space-y-6">
            
            {/* Sorting & Stats Top Bar */}
            <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white px-5 py-3.5 shadow-sm">
              <div className="flex flex-wrap items-center gap-3">
                <h3 className="font-bold text-slate-800 text-base">
                  {totalShown.toLocaleString("es-MX")} <span className="text-slate-500 font-medium">tarifas encontradas</span>
                </h3>
                {isRefreshing && (
                  <LoaderCircle className="h-4 w-4 animate-spin text-blue-600" />
                )}

                {/* Micro active filter chips */}
                <div className="hidden md:flex gap-1.5 ml-2">
                  {activeChips.map((chip) => (
                    <button
                      key={chip.id}
                      type="button"
                      onClick={chip.clear}
                      className="flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-200"
                    >
                      {chip.label}
                      <X className="h-3 w-3" />
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-4">
                {/* Inline Sorting Controls */}
                <div className="hidden lg:flex items-center gap-2 text-sm">
                  <ArrowDownUp className="h-4 w-4 text-slate-400" />
                  <Select
                    value={sortBy}
                    onChange={(e) => { setSortBy(e.target.value as SortBy); setPage(1); }}
                    className="h-8 w-[110px] rounded-md border-transparent bg-slate-50 text-xs font-semibold text-slate-700 hover:bg-slate-100 focus:border-slate-300"
                  >
                    <option value="precio">Precio</option>
                    <option value="nombre">Nombre</option>
                    <option value="operador">Proveedor</option>
                  </Select>
                  <Select
                    value={sortDir}
                    onChange={(e) => { setSortDir(e.target.value as SortDir); setPage(1); }}
                    className="h-8 w-[110px] rounded-md border-transparent bg-slate-50 text-xs font-semibold text-slate-700 hover:bg-slate-100 focus:border-slate-300"
                  >
                    <option value="asc">Menor a mayor</option>
                    <option value="desc">Mayor a menor</option>
                  </Select>
                </div>

                <div className="h-6 w-px bg-slate-200 hidden lg:block"></div>

                {/* Display Mode toggle */}
                <div className="flex items-center gap-0.5 rounded-lg bg-slate-100 p-0.5">
                  <button
                    type="button"
                    onClick={() => setDisplayMode("cards")}
                    className={cn("rounded-md p-1.5 transition-colors", displayMode === "cards" ? "bg-white text-blue-700 shadow-sm" : "text-slate-400 hover:text-slate-700")}
                    title="Vista tarjetas"
                  >
                    <LayoutGrid className="h-[18px] w-[18px]" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setDisplayMode("table")}
                    className={cn("rounded-md p-1.5 transition-colors", displayMode === "table" ? "bg-white text-blue-700 shadow-sm" : "text-slate-400 hover:text-slate-700")}
                    title="Vista lista"
                  >
                    <List className="h-[18px] w-[18px]" />
                  </button>
                </div>
              </div>
            </div>

            {/* Loading / Error / Content */}
            {searchQuery.isLoading && (
              <div className="flex flex-col items-center justify-center py-24 bg-white rounded-2xl border border-slate-200">
                <LoaderCircle className="h-10 w-10 animate-spin text-blue-600" />
                <p className="mt-4 text-sm font-medium text-slate-500">Analizando miles de tarifas...</p>
              </div>
            )}

            {searchQuery.isError && (
              <div className="animate-fade-up rounded-2xl border border-red-200 bg-red-50 p-8 text-center shadow-sm">
                <p className="text-lg font-bold text-red-700">No se pudo conectar con el servidor</p>
                <p className="mt-2 text-sm text-red-500">
                  {searchQuery.error instanceof Error ? searchQuery.error.message : "Verifica que los servicios estén en línea."}
                </p>
                <button
                  type="button"
                  onClick={() => searchQuery.refetch()}
                  className="mt-4 inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 transition"
                >
                  <RotateCcw className="h-4 w-4" />
                  Reintentar
                </button>
              </div>
            )}

            {!searchQuery.isLoading && !searchQuery.isError && (
              <div className="space-y-6">
                {displayMode === "cards" && (
                  <TarifaCards items={searchItems} />
                )}

                {displayMode === "table" && (
                  <ResultsTable items={searchItems} />
                )}

                {/* Bottom Pagination */}
                {searchQuery.data && searchQuery.data.total_pages > 1 && (
                  <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
                    <span className="text-sm font-medium text-slate-500">
                      Página <strong className="text-slate-800">{searchQuery.data.page}</strong> de <strong className="text-slate-800">{searchQuery.data.total_pages}</strong>
                    </span>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={page <= 1}
                        onClick={() => { setPage((p) => Math.max(1, p - 1)); window.scrollTo({ top: 300, behavior: 'smooth' }); }}
                        className="bg-slate-50 text-slate-700"
                      >
                        ← Anterior
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={page >= (searchQuery.data.total_pages || 1)}
                        onClick={() => { setPage((p) => Math.min(searchQuery.data!.total_pages, p + 1)); window.scrollTo({ top: 300, behavior: 'smooth' }); }}
                        className="bg-slate-50 text-slate-700"
                      >
                        Siguiente →
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-8 border-t border-slate-200 bg-white py-8 text-center text-xs text-slate-500">
        <p className="font-medium text-slate-700">Instituto Federal de Telecomunicaciones (IFT) · Comparador de Tarifas Móviles 2026</p>
        <p className="mt-1">Los datos provienen del Registro Público de Concesiones y se actualizan periódicamente.</p>
      </footer>
    </div>
  );
}
