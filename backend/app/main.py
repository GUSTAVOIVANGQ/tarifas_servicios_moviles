from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.data_pipeline import PreparationStats, prepare_dataset
from app.query_service import QueryService, SearchFilters
from app.schemas import FiltersResponse, SearchResponse, TarifaItem, Top10Response


app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _normalize_tipo_pago(tipo_pago: str) -> str:
    normalized = tipo_pago.strip().lower()
    if normalized not in {"prepago", "pospago", "todos"}:
        return "todos"
    return normalized


@app.on_event("startup")
def on_startup() -> None:
    prep_stats = prepare_dataset(
        csv_path=settings.csv_path,
        parquet_path=settings.parquet_path,
        allowed_statuses=settings.allowed_statuses,
    )
    app.state.prep_stats = prep_stats
    app.state.query_service = QueryService(settings.parquet_path)


def get_query_service() -> QueryService:
    return app.state.query_service


def get_prep_stats() -> PreparationStats:
    return app.state.prep_stats


@app.get("/health")
def health(stats: PreparationStats = Depends(get_prep_stats)) -> dict[str, object]:
    return {
        "status": "ok",
        "dataset_rows": stats.rows,
        "parquet_path": stats.parquet_path,
        "allowed_statuses": stats.statuses,
    }


@app.get("/api/v1/filters", response_model=FiltersResponse)
def filters(query_service: QueryService = Depends(get_query_service)) -> FiltersResponse:
    return FiltersResponse(**query_service.get_filters())


@app.get("/api/v1/search", response_model=SearchResponse)
def search(
    operador: list[int] | None = Query(default=None),
    concesionario: list[str] | None = Query(default=None),
    tipo_pago: str = Query(default="todos"),
    min_precio: float | None = Query(default=None, ge=0),
    max_precio: float | None = Query(default=None, ge=0),
    min_gigas: float | None = Query(default=None, ge=0),
    redes_sociales: bool = Query(default=False),
    min_vigencia_dias: int | None = Query(default=None, ge=0),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.default_page_size, ge=1),
    sort_by: str = Query(default="precio"),
    sort_dir: str = Query(default="asc"),
    query_service: QueryService = Depends(get_query_service),
) -> SearchResponse:
    safe_page_size = min(page_size, settings.max_page_size)
    filters_payload = SearchFilters(
        operadores=operador or [],
        concesionarios=concesionario or [],
        tipo_pago=_normalize_tipo_pago(tipo_pago),
        min_precio=min_precio,
        max_precio=max_precio,
        min_gigas=min_gigas,
        redes_sociales=redes_sociales,
        min_vigencia_dias=min_vigencia_dias,
        texto=(q or "").strip() or None,
    )
    return SearchResponse(
        **query_service.search(
            filters=filters_payload,
            page=page,
            page_size=safe_page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
    )


@app.get("/api/v1/top10", response_model=Top10Response)
def top10(
    operador: list[int] | None = Query(default=None),
    concesionario: list[str] | None = Query(default=None),
    tipo_pago: str = Query(default="todos"),
    min_precio: float | None = Query(default=None, ge=0),
    max_precio: float | None = Query(default=None, ge=0),
    min_gigas: float | None = Query(default=None, ge=0),
    redes_sociales: bool = Query(default=False),
    min_vigencia_dias: int | None = Query(default=None, ge=0),
    q: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=25),
    query_service: QueryService = Depends(get_query_service),
) -> Top10Response:
    filters_payload = SearchFilters(
        operadores=operador or [],
        concesionarios=concesionario or [],
        tipo_pago=_normalize_tipo_pago(tipo_pago),
        min_precio=min_precio,
        max_precio=max_precio,
        min_gigas=min_gigas,
        redes_sociales=redes_sociales,
        min_vigencia_dias=min_vigencia_dias,
        texto=(q or "").strip() or None,
    )
    return Top10Response(**query_service.top_cheapest(filters_payload, limit=limit))


@app.get("/api/v1/products/{id_tarifa}", response_model=TarifaItem)
def get_product(
    id_tarifa: int,
    query_service: QueryService = Depends(get_query_service),
) -> TarifaItem:
    record = query_service.get_by_id(id_tarifa)
    if record is None:
        raise HTTPException(status_code=404, detail="Tarifa no encontrada")
    return TarifaItem(**record)
