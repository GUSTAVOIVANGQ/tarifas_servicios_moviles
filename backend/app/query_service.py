from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb


SORT_FIELD_MAP = {
    "precio": "renta_mensual_con_impuestos",
    "nombre": "nombre_tarifa",
    "operador": "id_operador",
}

SELECT_COLUMNS = [
    "id_tarifa",
    "id_operador",
    "concesionario",
    "nombre_tarifa",
    "denominacion",
    "descripcion",
    "servicios",
    "estatus",
    "es_prepago",
    "es_pospago",
    "renta_mensual_con_impuestos",
    "renta_mensual_sin_impuestos",
    "monto_recarga",
    "capacidad_incluida",
    "capacidad_unidad_movil",
    "redes_sociales",
    "lineas_incluidas",
    "vigencia_saldo_recarga",
    "fecha_inicio_vigencia",
    "fecha_fin_vigencia",
    "fecha_cancelacion",
]

def map_marca_comercial(concesionario: str | None) -> str:
    if not concesionario:
        return "Desconocido"
    upper_name = concesionario.upper()
    if "RADIOMÓVIL" in upper_name or "TELCEL" in upper_name or "AMÉRICA MÓVIL" in upper_name or "DIPSA" in upper_name:
        return "Telcel"
    if "PEGASO" in upper_name or "MOVISTAR" in upper_name or "TELEFONICA" in upper_name:
        return "Movistar"
    if "AT&T" in upper_name or "IUSACELL" in upper_name or "NEXTEL" in upper_name or "UNEFON" in upper_name:
        return "AT&T"
    if "VIRGIN" in upper_name:
        return "Virgin Mobile"
    if "ALTÁN" in upper_name or "ALTAN" in upper_name:
        return "Altán Redes"
    if "CFE" in upper_name:
        return "CFE Internet"
    if "MEGACABLE" in upper_name:
        return "Megacable"
    if "TOTAL PLAY" in upper_name or "TOTALPLAY" in upper_name:
        return "Totalplay"
    if "PILLOFON" in upper_name or "DIRA" in upper_name:
        return "Pillofon"
    if "OXXO" in upper_name:
        return "Oxxo Cel"
    if "BAIT" in upper_name or "WALMART" in upper_name:
        return "Bait"
    return concesionario.title()


@dataclass(slots=True)
class SearchFilters:
    operadores: list[int]
    concesionarios: list[str]
    tipo_pago: str
    min_precio: float | None
    max_precio: float | None
    texto: str | None
    min_gigas: float | None = None
    redes_sociales: bool = False
    min_vigencia_dias: int | None = None


class QueryService:
    def __init__(self, parquet_path: Path, filters_cache_ttl: int = 300) -> None:
        self.parquet_path = parquet_path.resolve()
        self.filters_cache_ttl = filters_cache_ttl
        self._cached_filters: dict[str, Any] | None = None
        self._cache_created_at: float = 0.0
        self._lock = threading.Lock()

        parquet_ref = str(self.parquet_path).replace("'", "''")
        self._connection = duckdb.connect(database=":memory:")
        self._connection.execute("PRAGMA threads=4")
        self._connection.execute(
            f"CREATE OR REPLACE VIEW tarifas AS SELECT * FROM read_parquet('{parquet_ref}')"
        )

    def _execute_fetchall(
        self,
        query: str,
        params: list[Any] | None = None,
    ) -> tuple[list[str], list[tuple[Any, ...]]]:
        with self._lock:
            cursor = self._connection.execute(query, params or [])
            description = cursor.description or []
            columns = [column[0] for column in description]
            rows = cursor.fetchall()
            return columns, rows

    def _execute_fetchone(
        self,
        query: str,
        params: list[Any] | None = None,
    ) -> tuple[Any, ...] | None:
        with self._lock:
            cursor = self._connection.execute(query, params or [])
            return cursor.fetchone()

    @staticmethod
    def _rows_to_dicts(
        columns: list[str],
        rows: list[tuple[Any, ...]],
    ) -> list[dict[str, Any]]:
        results = []
        for row in rows:
            d = dict(zip(columns, row))
            d["marca_comercial"] = map_marca_comercial(d.get("concesionario"))
            d["precio_real"] = d.get("monto_recarga") if d.get("es_prepago") else d.get("renta_mensual_con_impuestos")
            if d["precio_real"] is None:
                d["precio_real"] = d.get("monto_recarga") or d.get("renta_mensual_con_impuestos")
            results.append(d)
        return results

    def _build_where(self, filters: SearchFilters) -> tuple[str, list[Any]]:
        clauses: list[str] = ["(renta_mensual_con_impuestos IS NOT NULL OR monto_recarga IS NOT NULL)"]
        params: list[Any] = []
        
        if filters.operadores:
            placeholders = ", ".join("?" for _ in filters.operadores)
            clauses.append(f"id_operador IN ({placeholders})")
            params.extend(filters.operadores)

        if filters.concesionarios:
            placeholders = ", ".join("?" for _ in filters.concesionarios)
            clauses.append(f"concesionario IN ({placeholders})")
            params.extend(filters.concesionarios)

        if filters.tipo_pago == "prepago":
            clauses.append("es_prepago = 1")
        elif filters.tipo_pago == "pospago":
            clauses.append("es_pospago = 1")

        if filters.min_precio is not None:
            clauses.append("COALESCE(monto_recarga, renta_mensual_con_impuestos) >= ?")
            params.append(filters.min_precio)

        if filters.max_precio is not None:
            clauses.append("COALESCE(monto_recarga, renta_mensual_con_impuestos) <= ?")
            params.append(filters.max_precio)

        if filters.texto:
            token = f"%{filters.texto.lower()}%"
            clauses.append(
                "("
                + " OR ".join(
                    [
                        "lower(coalesce(nombre_tarifa, '')) LIKE ?",
                        "lower(coalesce(denominacion, '')) LIKE ?",
                        "lower(coalesce(descripcion, '')) LIKE ?",
                        "lower(coalesce(servicios, '')) LIKE ?",
                    ]
                )
                + ")"
            )
            params.extend([token, token, token, token])

        if filters.min_gigas is not None:
            min_mb = filters.min_gigas * 1024
            duckdb_case = f"""
            (
                upper(capacidad_incluida) LIKE '%ILIMITADO%'
                OR
                (
                    TRY_CAST(REGEXP_EXTRACT(capacidad_incluida, '[0-9.]+') AS DOUBLE) * 
                    CASE upper(capacidad_unidad_movil) 
                        WHEN 'GB' THEN 1024 
                        WHEN 'MB' THEN 1 
                        WHEN 'TB' THEN 1048576 
                        ELSE 0 
                    END
                ) >= {min_mb}
            )
            """
            clauses.append(duckdb_case)

        if filters.redes_sociales:
            clauses.append("redes_sociales IS NOT NULL AND upper(redes_sociales) != 'NO' AND trim(redes_sociales) != ''")

        if filters.min_vigencia_dias is not None:
            # We assume "10 días", "30", etc. Regex extract first number.
            clauses.append(f"(TRY_CAST(REGEXP_EXTRACT(vigencia_saldo_recarga, '[0-9]+') AS DOUBLE) >= {filters.min_vigencia_dias})")

        return " AND ".join(clauses), params

    def get_filters(self) -> dict[str, Any]:
        now = time.time()
        if (
            self._cached_filters is not None
            and now - self._cache_created_at <= self.filters_cache_ttl
        ):
            return self._cached_filters

        _, operadores_rows = self._execute_fetchall(
            """
            SELECT DISTINCT id_operador
            FROM tarifas
            WHERE id_operador IS NOT NULL
            ORDER BY id_operador
            """
        )
        operadores = [row[0] for row in operadores_rows]

        _, concesionarios_rows = self._execute_fetchall(
            """
            SELECT DISTINCT concesionario
            FROM tarifas
            WHERE concesionario IS NOT NULL AND concesionario <> ''
            ORDER BY concesionario
            """
        )
        concesionarios = [row[0] for row in concesionarios_rows]

        _, estatus_rows = self._execute_fetchall(
            """
            SELECT DISTINCT estatus
            FROM tarifas
            WHERE estatus IS NOT NULL AND estatus <> ''
            ORDER BY estatus
            """
        )
        estatus = [row[0] for row in estatus_rows]

        min_max = self._execute_fetchone(
            """
            SELECT
                MIN(COALESCE(monto_recarga, renta_mensual_con_impuestos)) AS min_price,
                MAX(COALESCE(monto_recarga, renta_mensual_con_impuestos)) AS max_price
            FROM tarifas
            WHERE (renta_mensual_con_impuestos IS NOT NULL OR monto_recarga IS NOT NULL)
            """
        )
        min_price = min_max[0] if min_max else None
        max_price = min_max[1] if min_max else None

        payload = {
            "operadores": operadores,
            "concesionarios": concesionarios,
            "tipos_pago": ["prepago", "pospago", "todos"],
            "estatus": estatus,
            "rango_precio": {"min": min_price, "max": max_price},
        }

        self._cached_filters = payload
        self._cache_created_at = now
        return payload

    def search(
        self,
        filters: SearchFilters,
        page: int,
        page_size: int,
        sort_by: str,
        sort_dir: str,
    ) -> dict[str, Any]:
        where_clause, params = self._build_where(filters)
        
        # Override sort_column if user selects 'precio' to use our coalesced price
        if sort_by == "precio":
            sort_column = "COALESCE(monto_recarga, renta_mensual_con_impuestos)"
        else:
            sort_column = SORT_FIELD_MAP.get(sort_by, "COALESCE(monto_recarga, renta_mensual_con_impuestos)")

        sort_direction = "DESC" if sort_dir.lower() == "desc" else "ASC"
        offset = (page - 1) * page_size

        base_query = f"FROM tarifas WHERE {where_clause}"
        total_row = self._execute_fetchone(
            f"SELECT COUNT(*) AS total {base_query}",
            params,
        )
        total = int(total_row[0] if total_row else 0)

        columns, rows = self._execute_fetchall(
            f"""
            SELECT {", ".join(SELECT_COLUMNS)}
            {base_query}
            ORDER BY {sort_column} {sort_direction} NULLS LAST, id_tarifa ASC
            LIMIT ? OFFSET ?
            """,
            [*params, page_size, offset],
        )
        items = self._rows_to_dicts(columns, rows)

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "items": items,
        }

    def top_cheapest(self, filters: SearchFilters, limit: int = 10) -> dict[str, Any]:
        where_clause, params = self._build_where(filters)
        columns, rows = self._execute_fetchall(
            f"""
            SELECT {", ".join(SELECT_COLUMNS)}
            FROM tarifas
            WHERE {where_clause}
            ORDER BY COALESCE(monto_recarga, renta_mensual_con_impuestos) ASC NULLS LAST, id_tarifa ASC
            LIMIT ?
            """,
            [*params, limit],
        )
        items = self._rows_to_dicts(columns, rows)

        return {"total": len(items), "items": items}

    def get_by_id(self, id_tarifa: int) -> dict[str, Any] | None:
        columns, rows = self._execute_fetchall(
            f"""
            SELECT {", ".join(SELECT_COLUMNS)}
            FROM tarifas
            WHERE id_tarifa = ?
            LIMIT 1
            """,
            [id_tarifa],
        )
        rows_as_dicts = self._rows_to_dicts(columns, rows)
        if not rows_as_dicts:
            return None
        return rows_as_dicts[0]
