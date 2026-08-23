# Buscador de Tarifas del Registro Público de Telecomunicaciones

Herramienta oficial para la consulta, búsqueda y comparación de tarifas y promociones registradas en el **Registro Público de Telecomunicaciones**, desarrollada para la **Comisión Reguladora de Telecomunicaciones (CRT)**, órgano adscrito a la Agencia de Transformación Digital y Telecomunicaciones (ATDT).

Este proyecto es la renovación del antiguo visor de tarifas del IFT (`tarifas.ift.org.mx`). Permite a usuarios finales, analistas y concesionarios navegar el catálogo completo de tarifas registradas — **Servicios Móviles, Servicios Fijos, Televisión Restringida y Otros Servicios de Telecomunicaciones** — con filtros avanzados, comparador de planes, buscador de logos de operadores y exportación de datos.

> Este README documenta el arranque técnico del proyecto. El detalle de alcance, cronograma y gestión vive en el reporte de proyecto entregado junto con este documento.

- **Frontend:** React ⚛️ + Vite ⚡ + Tailwind CSS 🎨
- **Backend:** FastAPI 🚀 (Python)
- **Procesamiento de Datos:** Polars 🐻 & DuckDB 🦆 (Análisis de alto rendimiento en memoria)
- **Infraestructura:** Docker 🐳 & Docker Compose
    

## Requisitos

- Podman o Docker Desktop con Docker Compose
- Git
- Node.js 20+ (solo si se desarrolla frontend fuera de contenedor)
- Python 3.11+ (solo para el script de datos)
- .NET 8+ o JDK 21+ (solo si se desarrolla backend fuera de contenedor)

---

## Levantar el proyecto

```bash
git clone <url-del-repositorio>
cd buscador-tarifas
cp .env.example .env
docker compose up --build
# o con Podman:
podman-compose up --build
```

Aplicaciones disponibles:
- **Frontend:** http://localhost:5173
- **API docs (Swagger):** http://localhost:8080/swagger
- **Health:** http://localhost:8080/health

---

## Variables de entorno

Copiar `.env.example` a `.env` y ajustar según el entorno local. Nunca subir `.env` real al repositorio.

```env
CSV_SOURCE_PATH=./data/05_tarifas_servicios_moviles_febrero26_gustavo.csv
PARQUET_CACHE_DIR=./data/parquet_cache
DB_CONNECTION_STRING=Host=localhost;Port=5432;Database=tarifas_dev;Username=dev;Password=dev
API_PORT=8080
FRONTEND_PORT=5173
CORS_ORIGINS=http://localhost:5173
CLEARBIT_LOGO_BASE_URL=https://logo.clearbit.com
```

---

## Estructura del repositorio

```
├── backend/              # C# (.NET) o Java (Spring Boot)
│   ├── src/
│   ├── tests/
│   └── Dockerfile
├── frontend/             # React + Vite + Tailwind, pruebas Vitest
│   ├── src/
│   └── Dockerfile
├── data-scripts/         # Python: lectura CSV por lotes e inserción a BD
│   ├── ingest_csv.py
│   └── logos.py
├── e2e/                  # Pruebas Playwright de extremo a extremo
├── data/                 # CSV fuente (solo lectura) y cache Parquet
├── Prototipos/           # Prototipos de diseño IA
├── .github/workflows/    # Pipelines de CI
├── docker-compose.yml
├── podman-compose.yml
├── .env.example
└── README.md
```

---

## Endpoints del API

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/health` | Estado del servicio |
| `GET` | `/api/v1/filters` | Opciones de filtros disponibles (operadores, rangos) |
| `GET` | `/api/v1/search` | Búsqueda paginada con filtros |
| `GET` | `/api/v1/top10` | Top 10 planes por criterio |
| `GET` | `/api/v1/products/{id_tarifa}` | Detalle de una tarifa específica |
| `GET` | `/api/v1/logos/{operador}` | URL del logo del operador (Clearbit + fallback) |
| `GET` | `/api/v1/export` | Exportar resultados filtrados a CSV/Excel |

---

## Flujo de trabajo en equipo

### Ramas
- `main`: producción, protegida, solo se fusiona vía Pull Request aprobado.
- `develop`: integración de features antes de release.
- `feature/<nombre-corto>`, `fix/<nombre-corto>`, `release/<version>`.

### Commits
Usar [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`) para que el historial y el changelog se generen automáticamente.

### Pull Requests
- Mínimo 1 revisión aprobada antes de fusionar.
- CI en verde (lint + pruebas) obligatorio.
- Describir qué cambia y cómo se probó.

### Reparto de áreas

| Rol | Responsabilidad |
|---|---|
| **Ingeniero A — Datos** | Script Python para leer CSV por lotes e insertar en BD de desarrollo |
| **Ingeniero B — Backend** | API C# o Java, conexión a BD, endpoints (inicialmente con mocks) |
| **Ingeniero C — Frontend** | Maquetación del buscador y filtros, consumiendo JSON mock del Ing. B |
| **DevOps — Infraestructura** | Contenedores Podman/Docker, configuración para servidor RedHat |

---

## Calidad de código

- Pre-commit hooks: `husky` + `lint-staged` (frontend), `pre-commit` framework con `ruff`/`black` (Python).
- Ejecutar antes de cada commit: linters corren automáticamente; si fallan, el commit se bloquea.

---

## Pruebas

```bash
# Python (data scripts)
cd data-scripts && python -m pytest -q

# Backend C#
cd backend && dotnet test

# Frontend
cd frontend && npm test

# Smoke test en Docker
docker compose exec api dotnet test  # o mvn test para Java

# E2E
cd e2e && npx playwright test
```

---

## CI/CD

GitHub Actions ejecuta en cada Pull Request:
1. Lint (Ruff/ESLint)
2. Pruebas unitarias (Python, backend, frontend)
3. Prueba de accesibilidad automatizada (axe-core)
4. Build de imágenes Docker/Podman (validación, sin publicar)

---

## Accesibilidad y cumplimiento

Por ser una herramienta de un organismo público, el sitio debe cumplir **WCAG 2.1 nivel AA**: contraste de color, navegación por teclado, compatibilidad con lectores de pantalla y estructura semántica correcta. Estas validaciones se integran en CI.

---

## Roadmap

- [ ] Script de ingesta CSV → BD (Ingeniero A, semana 1)
- [ ] Endpoints mock del API (Ingeniero B, semana 1)
- [ ] Maquetación del buscador y filtros (Ingeniero C, semana 1)
- [ ] Contenedores Podman + config RedHat (DevOps, semana 1)
- [ ] Buscador de logos completo con fallback (semana 2)
- [ ] Integración frontend ↔ backend real (semana 2)
- [ ] Exportación de resultados a CSV/Excel desde la interfaz
- [ ] Migración completa de datos históricos del RPC y el SNII
- [ ] Comparador de tarifas entre concesionarios (todos los servicios)
- [ ] API pública documentada para consumo externo (open data)
- [ ] Panel de administración para carga de nuevas tarifas

---

## Evidencia — Prototipo anterior

Capturas de pantalla del funcionamiento del prototipo previo (FastAPI + React):

![Vista de resultados](pictures/Captura%20de%20pantalla%202026-04-09%20125932.png)
![Filtros avanzados](pictures/Captura%20de%20pantalla%202026-04-09%20125713.png)
![Detalle de tarifa](pictures/Captura%20de%20pantalla%202026-04-09%20125949.png)
