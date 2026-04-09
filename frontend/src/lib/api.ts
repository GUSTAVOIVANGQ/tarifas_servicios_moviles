import type {
  FiltersResponse,
  SearchFilters,
  SearchRequest,
  SearchResponse,
  Top10Response,
} from "./types";

const RAW_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ||
  "http://localhost:8000/api/v1";

const API_BASE_URL = RAW_BASE_URL.replace(/\/$/, "");

function appendMany(params: URLSearchParams, key: string, values: Array<string | number>) {
  values.forEach((value) => {
    params.append(key, String(value));
  });
}

function baseFilterParams(filters: SearchFilters): URLSearchParams {
  const params = new URLSearchParams();

  if (filters.operador.length > 0) {
    appendMany(params, "operador", filters.operador);
  }

  if (filters.concesionario.length > 0) {
    appendMany(params, "concesionario", filters.concesionario);
  }

  if (filters.tipo_pago && filters.tipo_pago !== "todos") {
    params.set("tipo_pago", filters.tipo_pago);
  }

  if (typeof filters.min_precio === "number") {
    params.set("min_precio", String(filters.min_precio));
  }

  if (typeof filters.max_precio === "number") {
    params.set("max_precio", String(filters.max_precio));
  }

  if (typeof filters.min_gigas === "number") {
    params.set("min_gigas", String(filters.min_gigas));
  }

  if (filters.redes_sociales) {
    params.set("redes_sociales", "true");
  }

  if (typeof filters.min_vigencia_dias === "number") {
    params.set("min_vigencia_dias", String(filters.min_vigencia_dias));
  }

  if (filters.q.trim()) {
    params.set("q", filters.q.trim());
  }

  return params;
}

async function request<T>(path: string, params?: URLSearchParams): Promise<T> {
  const query = params?.toString();
  const url = query ? `${API_BASE_URL}${path}?${query}` : `${API_BASE_URL}${path}`;
  const response = await fetch(url);

  if (!response.ok) {
    const details = await response.text();
    throw new Error(`Error ${response.status}: ${details || "No se pudo consultar la API"}`);
  }

  return (await response.json()) as T;
}

export function fetchFilters() {
  return request<FiltersResponse>("/filters");
}

export function searchTarifas(payload: SearchRequest) {
  const params = baseFilterParams(payload);
  params.set("page", String(payload.page));
  params.set("page_size", String(payload.page_size));
  params.set("sort_by", payload.sort_by);
  params.set("sort_dir", payload.sort_dir);
  return request<SearchResponse>("/search", params);
}

export function fetchTop10(payload: SearchFilters) {
  const params = baseFilterParams(payload);
  params.set("limit", "10");
  return request<Top10Response>("/top10", params);
}
