// IFT Institutional Header
export function IftHeader() {
  return (
    <header className="ift-header text-white">
      {/* Top slim bar */}
      <div className="border-b border-white/10 bg-black/20">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-1 text-xs text-blue-100">
          <span>Instituto Federal de Telecomunicaciones</span>
          <a href="https://www.ift.org.mx" target="_blank" rel="noopener noreferrer" className="opacity-70 hover:opacity-100 transition-opacity">
            ift.org.mx ↗
          </a>
        </div>
      </div>

      {/* Main header */}
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-4">
        {/* IFT Logo mark */}
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white shadow-md">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" className="h-9 w-9">
              <rect width="48" height="48" rx="8" fill="white"/>
              <text x="24" y="32" textAnchor="middle" fontFamily="Montserrat, sans-serif" fontWeight="900" fontSize="20" fill="#1B3A6B">IFT</text>
            </svg>
          </div>
          <div>
            <div className="font-display text-lg font-bold leading-tight tracking-tight text-white">
              Comparador de Tarifas
            </div>
            <div className="text-xs font-medium text-blue-200 leading-tight">
              Servicios Móviles · Datos abiertos 2026
            </div>
          </div>
        </div>

        {/* Divider */}
        <div className="hidden h-10 w-px bg-white/20 sm:block" />

        {/* Tagline */}
        <div className="hidden sm:block text-sm text-blue-100 leading-snug max-w-xs">
          Consulta y compara planes de telefonía móvil de todos los operadores registrados ante el IFT.
        </div>

        {/* Right side badge */}
        <div className="ml-auto shrink-0">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1.5 text-xs font-semibold text-white backdrop-blur-sm">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            Datos actualizados
          </span>
        </div>
      </div>
    </header>
  );
}
