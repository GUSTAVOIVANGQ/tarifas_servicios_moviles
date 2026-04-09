from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import polars as pl


DESCRIPTION_COLUMN = "DESCRIPCI\u00d3N"


@dataclass(slots=True)
class PreparationStats:
    rows: int
    statuses: list[str]
    parquet_path: str


def _normalize_money(column_name: str) -> pl.Expr:
    return (
        pl.col(column_name)
        .str.replace_all(r"[^0-9,.-]", "")
        .str.replace_all(",", "")
        .cast(pl.Float64, strict=False)
    )


def _resolve_csv_path(csv_path: Path) -> Path:
    if csv_path.exists():
        return csv_path
    fallback = Path(__file__).resolve().parents[2] / csv_path.name
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"CSV no encontrado en: {csv_path}")


def _needs_rebuild(csv_path: Path, parquet_path: Path) -> bool:
    if not parquet_path.exists():
        return True
    return parquet_path.stat().st_mtime < csv_path.stat().st_mtime


def _load_existing_stats(parquet_path: Path) -> PreparationStats:
    rows = int(
        pl.scan_parquet(parquet_path)
        .select(pl.len().alias("rows"))
        .collect()["rows"][0]
    )
    statuses = (
        pl.scan_parquet(parquet_path)
        .select(pl.col("estatus").drop_nulls().unique().sort())
        .collect()["estatus"]
        .to_list()
    )
    return PreparationStats(rows=rows, statuses=statuses, parquet_path=str(parquet_path))


def prepare_dataset(
    csv_path: Path,
    parquet_path: Path,
    allowed_statuses: list[str],
    force: bool = False,
) -> PreparationStats:
    source_path = _resolve_csv_path(csv_path)
    target_path = parquet_path.resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if not force and not _needs_rebuild(source_path, target_path):
        return _load_existing_stats(target_path)

    lazy_frame = pl.scan_csv(
        source_path,
        infer_schema_length=5000,
        ignore_errors=True,
        low_memory=True,
        encoding="utf8-lossy",
    )

    cleaned = (
        lazy_frame.select(
            [
                pl.col("ID_TARIFA").cast(pl.Int64, strict=False).alias("id_tarifa"),
                pl.col("ID_OPERADOR").cast(pl.Int64, strict=False).alias("id_operador"),
                pl.col("CONCESIONARIO").cast(pl.Utf8, strict=False).alias("concesionario"),
                pl.col("NOMBRE_TARIFA").cast(pl.Utf8, strict=False).alias("nombre_tarifa"),
                pl.col("DENOMINACION").cast(pl.Utf8, strict=False).alias("denominacion"),
                pl.col(DESCRIPTION_COLUMN).cast(pl.Utf8, strict=False).alias("descripcion"),
                pl.col("SERVICIOS").cast(pl.Utf8, strict=False).alias("servicios"),
                pl.col("ESTATUS").cast(pl.Utf8, strict=False).alias("estatus"),
                pl.col("FLAG_SERVICIO_PREPAGO").cast(pl.Int8, strict=False).alias("es_prepago"),
                pl.col("FLAG_SERVICIO_POSPAGO").cast(pl.Int8, strict=False).alias("es_pospago"),
                pl.col("RENTA_MENSUAL_CON_IMPUESTOS")
                .cast(pl.Utf8, strict=False)
                .alias("renta_mensual_con_impuestos_raw"),
                pl.col("RENTA_MENSUAL_SIN_IMPUESTOS")
                .cast(pl.Utf8, strict=False)
                .alias("renta_mensual_sin_impuestos_raw"),
                # New columns for richer UI display
                pl.col("MONTO_RECARGA")
                .cast(pl.Utf8, strict=False)
                .alias("monto_recarga_raw"),
                pl.col("VIGENCIA_SALDO_RECARGA")
                .cast(pl.Utf8, strict=False)
                .alias("vigencia_saldo_recarga"),
                pl.col("CAPACIDAD_INCLUIDA")
                .cast(pl.Utf8, strict=False)
                .alias("capacidad_incluida"),
                pl.col("CAPACIDAD_UNIDAD_MOVIL")
                .cast(pl.Utf8, strict=False)
                .alias("capacidad_unidad_movil"),
                pl.col("REDES_SOCIALES")
                .cast(pl.Utf8, strict=False)
                .alias("redes_sociales"),
                pl.col("LINEAS_INCLUIDAS")
                .cast(pl.Utf8, strict=False)
                .alias("lineas_incluidas"),
                pl.col("FECHA_INICIO_VIGENCIA")
                .cast(pl.Utf8, strict=False)
                .alias("fecha_inicio_vigencia_raw"),
                pl.col("FECHA_FIN_VIGENCIA")
                .cast(pl.Utf8, strict=False)
                .alias("fecha_fin_vigencia_raw"),
                pl.col("FECHA_CANCELACION")
                .cast(pl.Utf8, strict=False)
                .alias("fecha_cancelacion_raw"),
            ]
        )
        .with_columns(
            [
                pl.col("estatus").str.strip_chars().str.to_uppercase(),
                pl.col("es_prepago").fill_null(0),
                pl.col("es_pospago").fill_null(0),
                _normalize_money("renta_mensual_con_impuestos_raw").alias(
                    "renta_mensual_con_impuestos"
                ),
                _normalize_money("renta_mensual_sin_impuestos_raw").alias(
                    "renta_mensual_sin_impuestos"
                ),
                _normalize_money("monto_recarga_raw").alias("monto_recarga"),
                pl.col("capacidad_incluida").str.strip_chars(),
                pl.col("capacidad_unidad_movil").str.strip_chars(),
                pl.col("redes_sociales").str.strip_chars(),
                pl.col("lineas_incluidas").str.strip_chars(),
                pl.col("vigencia_saldo_recarga").str.strip_chars(),
                pl.col("fecha_inicio_vigencia_raw")
                .str.strptime(pl.Date, "%d/%m/%Y", strict=False)
                .alias("fecha_inicio_vigencia"),
                pl.col("fecha_fin_vigencia_raw")
                .str.strptime(pl.Date, "%d/%m/%Y", strict=False)
                .alias("fecha_fin_vigencia"),
                pl.col("fecha_cancelacion_raw")
                .str.strptime(pl.Date, "%d/%m/%Y", strict=False)
                .alias("fecha_cancelacion"),
            ]
        )
        .drop(
            [
                "renta_mensual_con_impuestos_raw",
                "renta_mensual_sin_impuestos_raw",
                "monto_recarga_raw",
                "fecha_inicio_vigencia_raw",
                "fecha_fin_vigencia_raw",
                "fecha_cancelacion_raw",
            ]
        )
        .filter(pl.col("id_tarifa").is_not_null())
        .filter(pl.col("estatus").is_in(allowed_statuses))
    )

    dataframe = cleaned.collect(engine="streaming")
    dataframe.write_parquet(target_path, compression="zstd")

    statuses = sorted(
        status
        for status in dataframe.get_column("estatus").drop_nulls().unique().to_list()
        if status
    )

    return PreparationStats(
        rows=dataframe.height,
        statuses=statuses,
        parquet_path=str(target_path),
    )
