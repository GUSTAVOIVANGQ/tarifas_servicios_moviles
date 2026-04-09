import { cn } from "@/lib/utils";

export interface ProviderOption {
  id: string;    // concesionario key (empty = "Todos")
  label: string; // display name
  color: string; // brand color hex
  textColor?: string;
  initials: string;
  emoji?: string;
}

// Known operators with brand identities
export const KNOWN_PROVIDERS: ProviderOption[] = [
  { id: "", label: "Todos", color: "#1B3A6B", textColor: "#fff", initials: "★", emoji: "⭐" },
  { id: "RADIOMÓVIL DIPSA, S.A. DE C.V.", label: "Telcel", color: "#0080C9", textColor: "#fff", initials: "T" },
  { id: "PEGASO PCS, S.A. DE C.V.", label: "Movistar", color: "#009900", textColor: "#fff", initials: "M" },
  { id: "AT&T OPCO UNE MEX, S.DE R.L. DE C.V.", label: "AT&T", color: "#00A8E0", textColor: "#fff", initials: "A" },
  { id: "AT&T DESARROLLO EN COMUNICACIONES DE MEXICO, S.DE R.L. DE C.V.", label: "AT&T", color: "#00A8E0", textColor: "#fff", initials: "A" },
  { id: "AT&T DIGITAL, S. DE R.L. DE C.V.", label: "AT&T / Nextel", color: "#005EB8", textColor: "#fff", initials: "N" },
  { id: "VIRGIN MOBILE MEXICO, S. DE R.L. DE C.V.", label: "Virgin", color: "#DA0914", textColor: "#fff", initials: "V" },
];

// Map concesionario → brand name
export function getBrandName(concesionario: string | null): string {
  if (!concesionario) return "Desconocido";
  const upper = concesionario.toUpperCase();
  if (upper.includes("DIPSA") || upper.includes("RADIOM")) return "Telcel";
  if (upper.includes("PEGASO")) return "Movistar";
  if (upper.includes("VIRGIN")) return "Virgin";
  if (upper.includes("AT&T") || upper.includes("IUSACELL")) {
    if (upper.includes("DIGITAL") || upper.includes("NEXTEL")) return "AT&T / Nextel";
    return "AT&T";
  }
  if (upper.includes("ALTAN") || upper.includes("ALTÁN")) return "Altán";
  if (upper.includes("CFE")) return "CFE Internet";
  if (upper.includes("KUBO")) return "Kubo Cel";
  if (upper.includes("QUICKLY")) return "Quickly Phone";
  if (upper.includes("TELECOMMERCE") || upper.includes("RADIOCOMUNICACIONES")) return "Regional";
  return concesionario
    .replace(/, S\.[A-Z]\. DE [A-Z]\.V\./g, "")
    .replace(/, S\.A\. DE C\.V\./g, "")
    .replace(/, S\. DE R\.L\. DE C\.V\./g, "")
    .trim()
    .split(" ")
    .slice(0, 2)
    .join(" ");
}

export function getBrandColor(brand: string | null): { bg: string; text: string } {
  const name = getBrandName(brand);
  switch (name) {
    case "Telcel":    return { bg: "#0080C9", text: "#fff" };
    case "Movistar": return { bg: "#009900", text: "#fff" };
    case "AT&T":     return { bg: "#00A8E0", text: "#fff" };
    case "AT&T / Nextel": return { bg: "#005EB8", text: "#fff" };
    case "Virgin":   return { bg: "#DA0914", text: "#fff" };
    case "Altán":    return { bg: "#E04E1B", text: "#fff" };
    case "CFE Internet": return { bg: "#006400", text: "#fff" };
    default:         return { bg: "#64748b", text: "#fff" };
  }
}

interface ProviderLogoProps {
  concesionario: string | null;
  size?: "sm" | "md" | "lg";
}

export function ProviderLogo({ concesionario, size = "md" }: ProviderLogoProps) {
  const brand = getBrandName(concesionario);
  const { bg, text } = getBrandColor(concesionario);
  const sizeClass = size === "sm" ? "h-8 w-8 text-xs" : size === "lg" ? "h-14 w-14 text-lg" : "h-10 w-10 text-sm";

  return (
    <div
      className={cn("flex items-center justify-center rounded-xl font-display font-black shadow-sm", sizeClass)}
      style={{ backgroundColor: bg, color: text }}
      title={concesionario || ""}
    >
      {brand.slice(0, 2).toUpperCase()}
    </div>
  );
}

interface ProviderFilterProps {
  selected: string[];                         // list of selected concesionario strings
  onChange: (selected: string[]) => void;
  concesionarios: string[];                   // all available concesionarios from API
}

// Deduplicate concesionarios into branded groups
function groupProviders(concesionarios: string[]): ProviderOption[] {
  const seen = new Set<string>();
  const result: ProviderOption[] = [
    { id: "", label: "Todos", color: "#1B3A6B", textColor: "#fff", initials: "★" },
  ];

  for (const c of concesionarios) {
    const brand = getBrandName(c);
    if (seen.has(brand)) continue;
    seen.add(brand);
    const { bg, text } = getBrandColor(c);
    result.push({ id: c, label: brand, color: bg, textColor: text, initials: brand.slice(0, 2).toUpperCase() });
  }
  return result;
}

import { useState, useRef, useEffect } from "react";
import { Check, ChevronDown } from "lucide-react";

export function ProviderFilter({ selected, onChange, concesionarios }: ProviderFilterProps) {
  const providers = groupProviders(concesionarios);
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function toggle(provider: ProviderOption) {
    if (provider.id === "") {
      onChange([]);
      setIsOpen(false);
      return;
    }
    const brand = provider.label;
    const matching = concesionarios.filter((c) => getBrandName(c) === brand);
    const allSelected = matching.every((m) => selected.includes(m));
    if (allSelected) {
      onChange(selected.filter((s) => !matching.includes(s)));
    } else {
      onChange([...new Set([...selected, ...matching])]);
    }
  }

  function isActive(provider: ProviderOption) {
    if (provider.id === "") return selected.length === 0;
    const matching = concesionarios.filter((c) => getBrandName(c) === provider.label);
    return matching.length > 0 && matching.some((m) => selected.includes(m));
  }

  // Display text in button
  const selectedCount = providers.filter(p => p.id !== "" && isActive(p)).length;
  let buttonLabel = "Todos los proveedores";
  if (selectedCount === 1) {
    buttonLabel = providers.find(p => p.id !== "" && isActive(p))?.label || buttonLabel;
  } else if (selectedCount > 1) {
    buttonLabel = `${selectedCount} proveedores`;
  }

  return (
    <div className="relative inline-block w-full text-left" ref={containerRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-800 shadow-sm transition-all hover:bg-slate-50 active:scale-95"
      >
        <span className="truncate">{buttonLabel}</span>
        <ChevronDown className="h-4 w-4 shrink-0 text-slate-400" />
      </button>

      {isOpen && (
        <div className="absolute left-0 top-full z-50 mt-1.5 w-full min-w-[240px] origin-top-left rounded-xl border border-slate-200 bg-white p-1.5 shadow-lg shadow-slate-200/50 animate-slide-in">
          <div className="max-h-[300px] overflow-y-auto space-y-1">
            {providers.map((provider) => {
              const active = isActive(provider);
              return (
                <button
                  key={provider.id || "todos"}
                  type="button"
                  onClick={() => toggle(provider)}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-lg px-2 py-2 text-left text-sm transition-colors hover:bg-slate-50",
                    active ? "bg-blue-50 text-blue-900" : "text-slate-700"
                  )}
                >
                  <div className="flex flex-1 items-center gap-2">
                    {/* Brand Badge */}
                    <span
                      className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-[9px] font-black shadow-sm"
                      style={{ backgroundColor: provider.color, color: provider.textColor || "#fff" }}
                    >
                      {provider.initials || provider.label.slice(0, 2)}
                    </span>
                    <span className="font-semibold">{provider.label}</span>
                  </div>

                  {/* Checked indicator */}
                  {active && <Check className="h-4 w-4 text-blue-600" />}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
