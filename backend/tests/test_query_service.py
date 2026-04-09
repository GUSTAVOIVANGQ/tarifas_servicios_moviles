from datetime import date
from pathlib import Path

import polars as pl
import pytest

from app.query_service import QueryService, SearchFilters


@pytest.fixture
def query_service(tmp_path: Path) -> QueryService:
    dataframe = pl.DataFrame(
        {
            "id_tarifa": [1, 2, 3, 4],
            "id_operador": [10, 10, 20, 30],
            "concesionario": ["Operador A", "Operador A", "Operador B", "Operador C"],
            "nombre_tarifa": ["Plan 200", "Plan 150", "Plan 300", "Plan sin precio"],
            "denominacion": ["BASICO", "PROMO", "PLUS", "SIN PRECIO"],
            "descripcion": ["Datos basicos", "Promo internet", "Mas datos", "No aplica"],
            "servicios": ["Internet", "Internet + Voz", "Datos", "SMS"],
            "estatus": ["VIGENTE", "VIGENTE", "VIGENTE", "VIGENTE"],
            "es_prepago": [1, 0, 1, 0],
            "es_pospago": [0, 1, 0, 1],
            "renta_mensual_con_impuestos": [200.0, 150.0, 300.0, None],
            "renta_mensual_sin_impuestos": [172.41, 129.31, 258.62, None],
            "fecha_inicio_vigencia": [
                date(2025, 1, 1),
                date(2025, 1, 1),
                date(2025, 1, 1),
                date(2025, 1, 1),
            ],
            "fecha_fin_vigencia": [None, None, None, None],
            "fecha_cancelacion": [None, None, None, None],
        }
    )
    parquet_path = tmp_path / "sample.parquet"
    dataframe.write_parquet(parquet_path)
    return QueryService(parquet_path)


def _default_filters() -> SearchFilters:
    return SearchFilters(
        operadores=[],
        concesionarios=[],
        tipo_pago="todos",
        min_precio=None,
        max_precio=None,
        texto=None,
    )


def test_get_filters_returns_expected_catalogs(query_service: QueryService) -> None:
    payload = query_service.get_filters()

    assert payload["operadores"] == [10, 20, 30]
    assert payload["concesionarios"] == ["Operador A", "Operador B", "Operador C"]
    assert payload["rango_precio"]["min"] == 150.0
    assert payload["rango_precio"]["max"] == 300.0


def test_search_applies_prepago_filter(query_service: QueryService) -> None:
    filters = _default_filters()
    filters.tipo_pago = "prepago"

    result = query_service.search(
        filters=filters,
        page=1,
        page_size=20,
        sort_by="precio",
        sort_dir="asc",
    )

    assert result["total"] == 2
    assert all(item["es_prepago"] == 1 for item in result["items"])


def test_search_supports_pagination_and_sort_desc(query_service: QueryService) -> None:
    result = query_service.search(
        filters=_default_filters(),
        page=1,
        page_size=2,
        sort_by="precio",
        sort_dir="desc",
    )

    assert result["total"] == 3
    assert result["total_pages"] == 2
    assert [item["id_tarifa"] for item in result["items"]] == [3, 1]


def test_search_filters_with_text_token(query_service: QueryService) -> None:
    filters = _default_filters()
    filters.texto = "promo"

    result = query_service.search(
        filters=filters,
        page=1,
        page_size=20,
        sort_by="precio",
        sort_dir="asc",
    )

    assert result["total"] == 1
    assert result["items"][0]["id_tarifa"] == 2


def test_top_cheapest_returns_sorted_rows(query_service: QueryService) -> None:
    result = query_service.top_cheapest(_default_filters(), limit=2)

    assert result["total"] == 2
    assert [item["id_tarifa"] for item in result["items"]] == [2, 1]


def test_get_by_id_returns_none_when_missing(query_service: QueryService) -> None:
    assert query_service.get_by_id(999) is None
