import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import App from "./App";

const BASE_ITEMS = [
  {
    id_tarifa: 10,
    id_operador: 1,
    concesionario: "Operador Uno",
    nombre_tarifa: "Plan 100",
    denominacion: "Plan 100",
    descripcion: "Plan basico",
    servicios: "Datos",
    estatus: "VIGENTE",
    es_prepago: 1,
    es_pospago: 0,
    renta_mensual_con_impuestos: 100,
    renta_mensual_sin_impuestos: 86,
    fecha_inicio_vigencia: "2025-01-01",
    fecha_fin_vigencia: null,
    fecha_cancelacion: null,
  },
  {
    id_tarifa: 20,
    id_operador: 1,
    concesionario: "Operador Uno",
    nombre_tarifa: "Plan 250",
    denominacion: "Plan 250",
    descripcion: "Plan medio",
    servicios: "Datos + Voz",
    estatus: "VIGENTE",
    es_prepago: 1,
    es_pospago: 0,
    renta_mensual_con_impuestos: 250,
    renta_mensual_sin_impuestos: 215,
    fecha_inicio_vigencia: "2025-01-01",
    fecha_fin_vigencia: null,
    fecha_cancelacion: null,
  },
  {
    id_tarifa: 30,
    id_operador: 2,
    concesionario: "Operador Dos",
    nombre_tarifa: "Plan 180 Pospago",
    denominacion: "Plan 180",
    descripcion: "Plan controlado",
    servicios: "Voz",
    estatus: "VIGENTE",
    es_prepago: 0,
    es_pospago: 1,
    renta_mensual_con_impuestos: 180,
    renta_mensual_sin_impuestos: 155,
    fecha_inicio_vigencia: "2025-01-01",
    fecha_fin_vigencia: null,
    fecha_cancelacion: null,
  },
];

function buildResponse(data: unknown) {
  return {
    ok: true,
    status: 200,
    json: async () => data,
    text: async () => JSON.stringify(data),
  } as Response;
}

function getSearchPayload(url: string) {
  const parsed = new URL(url);
  const sortDir = parsed.searchParams.get("sort_dir") ?? "asc";
  const tipoPago = parsed.searchParams.get("tipo_pago") ?? "todos";

  let items = [...BASE_ITEMS];
  if (tipoPago === "prepago") {
    items = items.filter((item) => item.es_prepago === 1);
  }
  if (tipoPago === "pospago") {
    items = items.filter((item) => item.es_pospago === 1);
  }

  items.sort((a, b) => {
    const delta = (a.renta_mensual_con_impuestos ?? 0) - (b.renta_mensual_con_impuestos ?? 0);
    return sortDir === "desc" ? -delta : delta;
  });

  return {
    page: 1,
    page_size: Number(parsed.searchParams.get("page_size") || 50),
    total: items.length,
    total_pages: 1,
    items,
  };
}

describe("App", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("aplica filtro de prepago y mantiene orden de precio ascendente", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);

      if (url.includes("/filters")) {
        return buildResponse({
          operadores: [1, 2],
          concesionarios: ["Operador Uno", "Operador Dos"],
          tipos_pago: ["prepago", "pospago", "todos"],
          estatus: ["VIGENTE"],
          rango_precio: { min: 100, max: 250 },
        });
      }

      if (url.includes("/search")) {
        return buildResponse(getSearchPayload(url));
      }

      if (url.includes("/top10")) {
        return buildResponse({ total: 2, items: BASE_ITEMS.slice(0, 2) });
      }

      return {
        ok: false,
        status: 404,
        json: async () => ({}),
        text: async () => "not found",
      } as Response;
    });

    vi.stubGlobal("fetch", fetchMock);

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>,
    );

    const user = userEvent.setup();

    const initialTable = await screen.findByRole("table");
    await waitFor(() => {
      expect(within(initialTable).getAllByText("Plan 100").length).toBeGreaterThan(0);
    });

    await user.selectOptions(screen.getByLabelText("Prepago / Pospago"), "prepago");
    await user.click(screen.getByRole("button", { name: "Buscar" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("tipo_pago=prepago"));
    });

    const table = screen.getByRole("table");
    const dataRows = within(table)
      .getAllByRole("row")
      .filter((row) => within(row).queryAllByRole("cell").length > 0);

    const prices = dataRows
      .map((row) => within(row).getAllByRole("cell")[3].textContent || "")
      .map((value) => Number(value.replace(/[^0-9.-]/g, "")))
      .filter((value) => Number.isFinite(value));

    expect(prices.length).toBeGreaterThan(1);
    expect(prices).toEqual([...prices].sort((a, b) => a - b));
  });
});
