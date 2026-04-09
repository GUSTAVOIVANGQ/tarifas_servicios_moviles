export type PaymentType = "todos" | "prepago" | "pospago";
export type SortBy = "precio" | "nombre" | "operador";
export type SortDir = "asc" | "desc";

export interface PriceRange {
  min: number | null;
  max: number | null;
}

export interface FiltersResponse {
  operadores: number[];
  concesionarios: string[];
  tipos_pago: PaymentType[];
  estatus: string[];
  rango_precio: PriceRange;
}

export interface TarifaItem {
  id_tarifa: number;
  id_operador: number | null;
  concesionario: string | null;
  marca_comercial: string | null;
  nombre_tarifa: string | null;
  denominacion: string | null;
  descripcion: string | null;
  servicios: string | null;
  estatus: string | null;
  es_prepago: number;
  es_pospago: number;
  renta_mensual_con_impuestos: number | null;
  renta_mensual_sin_impuestos: number | null;
  monto_recarga: number | null;
  precio_real: number | null;
  capacidad_incluida: string | number | null;
  capacidad_unidad_movil: string | null;
  redes_sociales: string | null;
  lineas_incluidas: string | number | null;
  vigencia_saldo_recarga: string | number | null;
  fecha_inicio_vigencia: string | null;
  fecha_fin_vigencia: string | null;
  fecha_cancelacion: string | null;
}

export interface SearchFilters {
  operador: number[];
  concesionario: string[];
  tipo_pago: "prepago" | "pospago" | "todos";
  min_precio: number | null;
  max_precio: number | null;
  min_gigas: number | null;
  redes_sociales: boolean;
  min_vigencia_dias: number | null;
  q: string;
}

export interface SearchRequest extends SearchFilters {
  page: number;
  page_size: number;
  sort_by: SortBy;
  sort_dir: SortDir;
}

export interface SearchResponse {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  items: TarifaItem[];
}

export interface Top10Response {
  total: number;
  items: TarifaItem[];
}
