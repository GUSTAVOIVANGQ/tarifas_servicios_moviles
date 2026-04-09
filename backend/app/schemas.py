from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class PriceRange(BaseModel):
    min: float | None = None
    max: float | None = None


class FiltersResponse(BaseModel):
    operadores: list[int] = Field(default_factory=list)
    concesionarios: list[str] = Field(default_factory=list)
    tipos_pago: list[str] = Field(default_factory=lambda: ["prepago", "pospago", "todos"])
    estatus: list[str] = Field(default_factory=list)
    rango_precio: PriceRange = Field(default_factory=PriceRange)


class TarifaItem(BaseModel):
    id_tarifa: int
    id_operador: int | None = None
    concesionario: str | None = None
    marca_comercial: str | None = None
    nombre_tarifa: str | None = None
    denominacion: str | None = None
    descripcion: str | None = None
    servicios: str | None = None
    estatus: str | None = None
    es_prepago: int = 0
    es_pospago: int = 0
    renta_mensual_con_impuestos: float | None = None
    renta_mensual_sin_impuestos: float | None = None
    monto_recarga: float | None = None
    precio_real: float | None = None
    capacidad_incluida: str | float | None = None
    capacidad_unidad_movil: str | None = None
    redes_sociales: str | None = None
    lineas_incluidas: str | int | None = None
    vigencia_saldo_recarga: str | int | None = None
    fecha_inicio_vigencia: date | None = None
    fecha_fin_vigencia: date | None = None
    fecha_cancelacion: date | None = None


class SearchResponse(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    items: list[TarifaItem] = Field(default_factory=list)


class Top10Response(BaseModel):
    total: int
    items: list[TarifaItem] = Field(default_factory=list)
