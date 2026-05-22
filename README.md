# Comparador de Tarifas de Servicios Móviles

Este proyecto es un prototipo funcional desarrollado para la **Comisión Reguladora de Telecomunicaciones**, diseñado para brindar transparencia y facilidad de comparación en el mercado de telefonía móvil.

La plataforma permite a los usuarios finales y analistas navegar por un catálogo de más de 6,500 registros de tarifas, aplicando filtros avanzados para encontrar el plan que mejor se adapte a sus necesidades presupuestarias y técnicas.

## 🚀 Stack Tecnológico

- **Frontend:** React ⚛️ + Vite ⚡ + Tailwind CSS 🎨
- **Backend:** FastAPI 🚀 (Python)
- **Procesamiento de Datos:** Polars 🐻 & DuckDB 🦆 (Análisis de alto rendimiento en memoria)
- **Infraestructura:** Docker 🐳 & Docker Compose

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

## Características Principales

- **Búsqueda Inteligente:** Filtrado instantáneo por nombre de compañía o términos clave.
- **Normalización de Datos:** Limpieza automática de unidades (GB/MB) para comparativas coherentes.
- **Motor de Consultas Optimizado:** Uso de archivos Parquet y DuckDB para respuestas en milisegundos.
- **Diseño Responsivo:** Interfaz adaptada para uso en escritorio y dispositivos móviles.

## Endpoints del API

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

- Rediseño completo de la interfaz de usuario (UX/UI).
- Query engine DuckDB reutilizable para reducir overhead por request.
- Tabla con virtualizacion de filas para listados extensos.
- UI con drawer de filtros en movil, chips removibles y selector de filas por pagina.
- Suite de pruebas backend funcional + prueba UI con Vitest.

## Notas

- El CSV original se monta en modo solo lectura.
- El cache Parquet se guarda en un volumen Docker (`parquet_cache`).
- Las columnas no necesarias se ignoran en lectura sin modificar el archivo fuente.

## Evidencia

Capturas de pantalla del funcionamiento de la plataforma:

![Buscador Inteligente](pictures/Captura%20de%20pantalla%202026-04-09%20135049.png)
![Panel de Filtros](pictures/Captura%20de%20pantalla%202026-04-09%20133701.png)
![Resultados y Vistas](pictures/Captura%20de%20pantalla%202026-04-09%20125932.png)
