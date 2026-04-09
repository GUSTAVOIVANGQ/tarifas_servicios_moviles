# Tarifas de Servicios Moviles

MVP fase 1 con backend FastAPI + Polars + DuckDB y frontend React + Vite + Tailwind.

## Requisitos

- Docker Desktop con Docker Compose

## Levantar el proyecto

```bash
docker compose up --build
```

Aplicaciones disponibles:

- Frontend: [http://localhost:5173](http://localhost:5173)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health: [http://localhost:8000/health](http://localhost:8000/health)

## Endpoints base

- `GET /health`
- `GET /api/v1/filters`
- `GET /api/v1/search`
- `GET /api/v1/top10`
- `GET /api/v1/products/{id_tarifa}`

## Pruebas

- Backend local: `cd backend && ..\\.venv\\Scripts\\python.exe -m pytest -q`
- Frontend local: `cd frontend && npm test`
- Smoke test en Docker: `docker compose exec api python -m pytest -q`

## Mejoras fase 2

- Query engine DuckDB reutilizable para reducir overhead por request.
- Tabla con virtualizacion de filas para listados extensos.
- UI con drawer de filtros en movil, chips removibles y selector de filas por pagina.
- Suite de pruebas backend funcional + prueba UI con Vitest.

## Notas

- El CSV original se monta en modo solo lectura.
- El cache Parquet se guarda en un volumen Docker (`parquet_cache`).
- Las columnas no necesarias se ignoran en lectura sin modificar el archivo fuente.
