"""Aplica DESCRIPCION_CORREGIDA con encoding cp1252 al CSV comparador."""
import csv, os

ORIG     = r"c:\Users\ivan-\Documents\GitHub\tarifas_servicios_moviles\05_tarifas_servicios_moviles_febrero26_gustavo.csv"
CSV_FILE = r"c:\Users\ivan-\Documents\GitHub\tarifas_servicios_moviles\tarifas_comparador_vigentes.csv"
TEMP     = r"c:\Users\ivan-\Documents\GitHub\tarifas_servicios_moviles\_tmp_desc.csv"

DESC_COL = "DESCRIPCI\ufffdN"   # nombre real con replace-char

# 1) Cargar descripciones corregidas del original
print("Cargando descripciones del original...")
desc_map = {}
with open(ORIG, "r", encoding="utf-8", errors="replace") as fp:
    reader = csv.DictReader(fp)
    for i, row in enumerate(reader):
        if i % 40000 == 0 and i > 0:
            print(f"  {i:,}...")
        # El BOM hace que la primera columna tenga el BOM en el key
        id_t = str(row.get("\ufeffID_TARIFA") or row.get("ID_TARIFA") or "").strip()
        desc = row.get(DESC_COL) or ""
        if id_t and desc:
            try:
                fixed = desc.encode("utf-8", "surrogateescape").decode("cp1252")
            except Exception:
                fixed = desc
            desc_map[id_t] = fixed[:400].replace("\n"," ").replace("\r"," ").replace("\t"," ").strip()

print(f"Descripciones cargadas: {len(desc_map):,}")
# muestra
for k, v in list(desc_map.items())[5:7]:
    print(f"  ID={k}: {repr(v[:100])}")

# 2) Aplicar al CSV comparador
print("\nAplicando al comparador CSV...")
with open(CSV_FILE, "r", encoding="utf-8-sig") as fin:
    reader = csv.DictReader(fin)
    cols = list(reader.fieldnames)
    rows = list(reader)

corregidas = 0
for row in rows:
    id_t = str(row.get("ID_TARIFA","")).strip()
    desc_c = desc_map.get(id_t, "")
    row["DESCRIPCION_CORREGIDA"] = desc_c
    if desc_c:
        corregidas += 1

with open(TEMP, "w", encoding="utf-8-sig", newline="") as fout:
    writer = csv.DictWriter(fout, fieldnames=cols, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)

os.replace(TEMP, CSV_FILE)

sz = os.path.getsize(CSV_FILE) / 1024 / 1024
print(f"\nFilas con desc corregida: {corregidas:,} de {len(rows):,}")
print(f"Tamano final: {sz:.1f} MB")

# Verificar muestra
print("\nMuestra DESCRIPCION_CORREGIDA:")
with open(CSV_FILE, "r", encoding="utf-8-sig") as fp:
    sample_rows = []
    for r in csv.DictReader(fp):
        if r.get("DESCRIPCION_CORREGIDA"):
            sample_rows.append(r)
            if len(sample_rows) >= 2:
                break
    for r in sample_rows:
        op   = r.get("OPERADOR_NOMBRE","")
        plan = r.get("NOMBRE_TARIFA","")[:40]
        desc = r.get("DESCRIPCION_CORREGIDA","")[:120]
        print(f"  OP={op}  PLAN={plan}")
        print(f"  DESC={desc}\n")

# 3) Estadisticas finales de calidad
print("=== ESTADISTICAS FINALES ===")
campos_check = [
    "DATOS_GB_NORM","PRECIO_REFERENCIA_MXN","VIGENCIA_TIPO",
    "VELOCIDAD_MAX_MBPS","VELOCIDAD_THROTTLE_KBPS",
    "HOTSPOT_INCLUIDO","LLAMADAS_USA_CANADA",
    "MINUTOS_INCLUIDOS","SMS_INCLUIDOS",
    "APPS_STREAMING","APPS_RSSS_LISTA","RED_TECNOLOGIA",
    "DESCRIPCION_CORREGIDA",
]
totales = len(rows)
with open(CSV_FILE, "r", encoding="utf-8-sig") as fp:
    reader = csv.DictReader(fp)
    conteos = {c: 0 for c in campos_check}
    ilim = 0
    for row in reader:
        for c in campos_check:
            v = row.get(c,"")
            if v and v not in ("NO","0",""):
                conteos[c] += 1
        if row.get("DATOS_GB_NORM","") == "ILIMITADO":
            ilim += 1

print(f"\nTotal filas: {totales:,}")
for c, cnt in conteos.items():
    pct = cnt / totales * 100
    bar = "#" * int(pct / 5)
    print(f"  {c:<30}: {cnt:6,} ({pct:5.1f}%) {bar}")
print(f"\n  Planes ILIMITADOS de datos: {ilim:,}")
