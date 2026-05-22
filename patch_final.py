"""
Patch final: 
  1. Corrige encoding mojibake en DESCRIPCION_CORTA
  2. Mejora deteccion de velocidad (throttle/max) con patrones ampliados
  3. Rellena MINUTOS_INCLUIDOS y SMS_INCLUIDOS donde faltaron
  4. Mejora deteccion de LLAMADAS_USA_CANADA tolerando encoding roto
  5. Agrega campo DESCRIPCION_UTF8 con texto corregido
  6. Genera reporte de calidad final
"""

import csv, re, os

CSV_FILE = r"c:\Users\ivan-\Documents\GitHub\tarifas_servicios_moviles\tarifas_comparador_vigentes.csv"
ORIG_CSV = r"c:\Users\ivan-\Documents\GitHub\tarifas_servicios_moviles\05_tarifas_servicios_moviles_febrero26_gustavo.csv"
TEMP_OUT = r"c:\Users\ivan-\Documents\GitHub\tarifas_servicios_moviles\tarifas_comparador_vigentes_tmp.csv"

# ─── Tabla de corrección encoding (utf-8 con bytes latin-1 mezclados) ───────
# Caracteres típicamente corruptos en CSV español del IFT
ENCODING_FIX = {
    "\ufffd": "?",   # replacement char genérico
    # Los más comunes en español:
    "\u00e1": "á",  # ya correcto
    "\u00e9": "é",
    "\u00ed": "í",
    "\u00f3": "ó",
    "\u00fa": "ú",
    "\u00f1": "ñ",
    "\u00fc": "ü",
    "\u00c1": "Á",
    "\u00c9": "É",
    "\u00cd": "Í",
    "\u00d3": "Ó",
    "\u00da": "Ú",
    "\u00d1": "Ñ",
}

# Mapa de bytes latin-1 corruptos → caracter correcto español
# Cuando un byte latin-1 fue leído como si fuera UTF-8
BYTE_FIX = {
    "\xe1": "á", "\xe9": "é", "\xed": "í", "\xf3": "ó", "\xfa": "ú",
    "\xf1": "ñ", "\xfc": "ü", "\xe0": "à", "\xe8": "è", "\xec": "ì",
    "\xe2": "â", "\xc1": "Á", "\xc9": "É", "\xcd": "Í", "\xd3": "Ó",
    "\xda": "Ú", "\xd1": "Ñ", "\xbf": "¿", "\xa1": "¡",
}


def fix_encoding_desc(texto):
    """
    Intenta corregir mojibake en texto usando surrogateescape.
    Cuando falla usa sustitución de caracteres conocidos.
    """
    if not texto:
        return ""
    # Intentar reparar: re-encode como surrogates y decodificar como cp1252
    try:
        fixed = texto.encode("utf-8", "surrogateescape").decode("cp1252")
        return fixed
    except Exception:
        pass
    # Fallback: reemplazar bytes sueltos
    for bad, good in BYTE_FIX.items():
        texto = texto.replace(bad, good)
    return texto


# ─── Patrones de velocidad MEJORADOS ────────────────────────────────────────
RE_VEL_MAX_LIST = [
    re.compile(r'hasta\s+([\d,\.]+)\s*(Gbps|Mbps)', re.IGNORECASE),
    re.compile(r'([\d,\.]+)\s*(Gbps|Mbps)\s+(?:de\s+)?velocidad\s+(?:m.xima|alta|normal|incluida)', re.IGNORECASE),
    re.compile(r'velocidad\s+(?:de\s+(?:hasta\s+)?)?([\d,\.]+)\s*(Gbps|Mbps)', re.IGNORECASE),
    re.compile(r'([\d]+)\s*Mbps\s+(?:fija|garantizada|\()', re.IGNORECASE),
    # Para plan names tipo "HBB 5Mbps" o "50Mbps"
    re.compile(r'\b(\d+)\s*Mbps\b', re.IGNORECASE),
]

RE_THROTTLE_LIST = [
    re.compile(r'velocidad\s+reducida\s+(?:de\s+)?([\d,\.]+)\s*(Kbps|Mbps)', re.IGNORECASE),
    re.compile(r'([\d,\.]+)\s*(Kbps|Mbps)\s+(?:de\s+)?velocidad\s+reducida', re.IGNORECASE),
    re.compile(r'reduce\s+(?:a\s+)?([\d,\.]+)\s*(Kbps|Mbps)', re.IGNORECASE),
    re.compile(r'reducir.{0,20}([\d,\.]+)\s*(Kbps|Mbps)', re.IGNORECASE),
    re.compile(r'([\d,\.]+)\s*(Kbps|Mbps)\s+(?:por\s+el\s+resto|hasta\s+el\s+fin)', re.IGNORECASE),
    re.compile(r'a\s+([\d,\.]+)\s*(Kbps|Mbps)\s+(?:de\s+velocidad)?(?:\s+(?:hasta|por))', re.IGNORECASE),
    # Velocidad throttle común: "512 Kbps", "1 Mbps" solos en contexto de datos adicionales
    re.compile(r'\b(128|256|512|1024|2048)\s*Kbps\b', re.IGNORECASE),
    re.compile(r'\b1\s*Mbps\b\s+(?:con|para|hasta|por)', re.IGNORECASE),
]

RE_MIN_MEJORADO = [
    re.compile(r'([\d,\.]+)\s*min(?:utos?)?(?:\s+(?:nacionales?|incluidos?|en\s+M.xico|total(?:es)?))?', re.IGNORECASE),
    re.compile(r'(\d+(?:,\d+)?)\s*(?:minutos?|min\.?)\s+(?:de\s+)?(?:voz|llamadas?)', re.IGNORECASE),
    re.compile(r'(\d+(?:\.\d+)?)\s*(?:k)\s*min(?:utos?)?', re.IGNORECASE),  # "10k minutos"
]

RE_SMS_MEJORADO = [
    re.compile(r'([\d,\.]+)\s*(?:SMS|mensajes?\s+de\s+texto)(?:\s+(?:nacionales?|incluidos?))?', re.IGNORECASE),
    re.compile(r'(\d+(?:,\d+)?)\s*(?:SMS|mensajes?\s+de\s+texto)\s+(?:a\s+)?(?:M.xico|nacional)', re.IGNORECASE),
]

# Patrón llamadas USA/Canadá tolerante al encoding roto
RE_LLAMADAS_USA = re.compile(
    r'(?:usa|ee\.?uu\.?|estados\s*unidos|EUA)'
    r'|(?:canad[a\xe1\ufffd])'       # Canadá con 'á' roto o correcto
    r'|(?:canad.{0,2}(?:\s+|,|\.))', re.IGNORECASE
)

RE_HOTSPOT_MEJORADO = re.compile(
    r'hotspot|compartir\s+(?:datos|internet)|tethering|punto\s+de\s+acceso'
    r'|wi-?fi\s+(?:portatil|movil|compartido)|internet\s+compartido'
    r'|modem\s+portatil|conectar\s+otros\s+dispositivos',
    re.IGNORECASE
)


def to_float(v):
    try:
        return float(str(v).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def extraer_velocidad_max_v2(nombre, desc):
    """Extrae velocidad máxima buscando primero en nombre del plan, luego descripción."""
    for texto in [nombre, desc]:
        if not texto:
            continue
        for pat in RE_VEL_MAX_LIST:
            m = pat.search(texto)
            if m:
                val = to_float(m.group(1))
                unit = m.group(2).lower() if len(m.groups()) > 1 else "mbps"
                if val is not None and val < 10000:  # sanity check
                    if "gbps" in unit:
                        return str(int(val * 1000))
                    return str(int(val))
    return ""


def extraer_throttle_v2(desc):
    """Extrae velocidad throttle con patrones mejorados."""
    if not desc:
        return ""
    for pat in RE_THROTTLE_LIST:
        m = pat.search(desc)
        if m:
            groups = m.groups()
            if len(groups) >= 2:
                val = to_float(groups[0])
                unit = groups[1].lower()
                if val is not None and val < 100000:
                    if "mbps" in unit:
                        return str(int(val * 1024))
                    return str(int(val))
            elif len(groups) == 1:
                val = to_float(groups[0])
                if val:
                    return str(int(val))
    return ""


def extraer_minutos_v2(desc):
    """Extrae minutos con patrones mejorados."""
    if not desc:
        return ""
    d = desc.lower()
    if re.search(r'minutos?\s+ilimitados?|llamadas?\s+ilimitadas?', d):
        return "ILIMITADOS"
    for pat in RE_MIN_MEJORADO:
        m = pat.search(desc)
        if m:
            val = m.group(1).replace(",","")
            try:
                v = float(val)
                if 0 < v < 100000:  # sanity
                    return str(int(v))
            except ValueError:
                pass
    return ""


def extraer_sms_v2(desc):
    """Extrae SMS con patrones mejorados."""
    if not desc:
        return ""
    d = desc.lower()
    if re.search(r'sms\s+ilimitados?|mensajes?\s+ilimitados?', d):
        return "ILIMITADOS"
    for pat in RE_SMS_MEJORADO:
        m = pat.search(desc)
        if m:
            val = m.group(1).replace(",","")
            try:
                v = float(val)
                if 0 < v < 100000:
                    return str(int(v))
            except ValueError:
                pass
    return ""


def llamadas_usa_v2(desc):
    return "SI" if RE_LLAMADAS_USA.search(desc or "") else "NO"


def hotspot_v2(desc):
    return "SI" if RE_HOTSPOT_MEJORADO.search(desc or "") else "NO"


# ─── LECTURA DEL CSV ORIGINAL PARA DESCRIPCIONES CORREGIDAS ─────────────────
print("Leyendo descripciones originales con encoding corregido...")
desc_map = {}  # ID_TARIFA -> descripcion corregida

# Leer el original con surrogateescape para arreglar encoding
with open(ORIG_CSV, "r", encoding="utf-8", errors="surrogateescape") as fp:
    reader = csv.DictReader(fp)
    for i, row in enumerate(reader):
        if i % 30000 == 0 and i > 0:
            print(f"  Leidas {i:,} filas del original...")
        id_t = str(row.get("ID_TARIFA", "")).strip()
        if id_t:
            desc_raw = row.get("DESCRIPCI\xf3N") or row.get("DESCRIPCI\u00d3N") or row.get("DESCRIPCIÓN") or ""
            for key in row:
                if "DESCRI" in key.upper() and ("N" in key.upper() or "\xd3" in key or "\u00d3" in key):
                    desc_raw = row[key] or ""
                    break
            if desc_raw:
                try:
                    fixed = desc_raw.encode("utf-8", "surrogateescape").decode("cp1252")
                except Exception:
                    fixed = desc_raw
                desc_map[id_t] = fixed[:500].replace("\n", " ").replace("\r", " ").replace("\t", " ").strip()

print(f"Descripciones originales cargadas: {len(desc_map):,}")


# ─── PATCH PRINCIPAL ─────────────────────────────────────────────────────────
print("\nAplicando patch al CSV del comparador...")

with open(CSV_FILE, "r", encoding="utf-8-sig") as fin:
    reader = csv.DictReader(fin)
    original_cols = list(reader.fieldnames)
    
    # Agregar nuevos campos si no existen
    extra = ["DESCRIPCION_CORREGIDA"]
    new_cols = original_cols + [c for c in extra if c not in original_cols]
    
    # Ya existen en el CSV del paso anterior, inicializar en "":
    for c in extra:
        if c not in original_cols:
            pass
    
    rows_in = list(reader)

print(f"Filas a parchear: {len(rows_in):,}")
print(f"Columnas: {len(original_cols)} -> {len(new_cols)}")

stats = {
    "vel_max_mejorada": 0,
    "throttle_mejorado": 0,
    "hotspot_mejorado": 0,
    "llamadas_usa_mejorado": 0,
    "minutos_rellenados": 0,
    "sms_rellenados": 0,
    "desc_corregida": 0,
}

rows_out = []
for i, row in enumerate(rows_in):
    if i % 20000 == 0 and i > 0:
        print(f"  {i:,} / {len(rows_in):,}...")

    id_t = str(row.get("ID_TARIFA","")).strip()
    nombre = row.get("NOMBRE_TARIFA_LIMPIO","") or row.get("NOMBRE_TARIFA","") or ""
    
    # Descripción: usar la corregida del original si existe
    desc_corr = desc_map.get(id_t, "")
    if desc_corr:
        stats["desc_corregida"] += 1
        desc_uso = desc_corr[:400]
    else:
        desc_uso = row.get("DESCRIPCION_CORTA","") or ""
    
    row["DESCRIPCION_CORREGIDA"] = desc_corr[:400] if desc_corr else ""
    
    # Velocidad máxima (mejorada)
    vel_old = row.get("VELOCIDAD_MAX_MBPS","")
    vel_new = extraer_velocidad_max_v2(nombre, desc_uso) if not vel_old else vel_old
    if vel_new and not vel_old:
        stats["vel_max_mejorada"] += 1
    row["VELOCIDAD_MAX_MBPS"] = vel_new

    # Throttle (mejorado)
    thr_old = row.get("VELOCIDAD_THROTTLE_KBPS","")
    thr_new = extraer_throttle_v2(desc_uso) if not thr_old else thr_old
    if thr_new and not thr_old:
        stats["throttle_mejorado"] += 1
    row["VELOCIDAD_THROTTLE_KBPS"] = thr_new

    # Hotspot (mejorado)
    hot_old = row.get("HOTSPOT_INCLUIDO","NO")
    hot_new = hotspot_v2(desc_uso)
    if hot_new == "SI" and hot_old == "NO":
        stats["hotspot_mejorado"] += 1
    row["HOTSPOT_INCLUIDO"] = hot_new

    # Llamadas USA/Canadá (mejorado)
    usa_old = row.get("LLAMADAS_USA_CANADA","NO")
    usa_new = llamadas_usa_v2(desc_uso)
    if usa_new == "SI" and usa_old == "NO":
        stats["llamadas_usa_mejorado"] += 1
    row["LLAMADAS_USA_CANADA"] = usa_new

    # Minutos (rellenar vacíos)
    min_old = row.get("MINUTOS_INCLUIDOS","")
    if not min_old:
        min_new = extraer_minutos_v2(desc_uso)
        if min_new:
            stats["minutos_rellenados"] += 1
        row["MINUTOS_INCLUIDOS"] = min_new
    
    # SMS (rellenar vacíos)
    sms_old = row.get("SMS_INCLUIDOS","")
    if not sms_old:
        sms_new = extraer_sms_v2(desc_uso)
        if sms_new:
            stats["sms_rellenados"] += 1
        row["SMS_INCLUIDOS"] = sms_new

    # Inicializar nuevo campo si no existe
    if "DESCRIPCION_CORREGIDA" not in row:
        row["DESCRIPCION_CORREGIDA"] = ""

    rows_out.append(row)

# Escribir CSV final (sobreescribir)
print(f"\nEscribiendo CSV final...")
with open(TEMP_OUT, "w", encoding="utf-8-sig", newline="") as fout:
    writer = csv.DictWriter(fout, fieldnames=new_cols, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows_out)

# Reemplazar el original
os.replace(TEMP_OUT, CSV_FILE)

sz = os.path.getsize(CSV_FILE) / 1024 / 1024
print(f"\n=== PATCH COMPLETADO ===")
print(f"Archivo final:    {CSV_FILE}")
print(f"Filas:            {len(rows_out):,}")
print(f"Columnas totales: {len(new_cols)}")
print(f"Tamano:           {sz:.1f} MB")
print(f"\n--- MEJORAS APLICADAS ---")
for k, v in stats.items():
    pct = v / len(rows_out) * 100 if rows_out else 0
    print(f"  {k:<28}: {v:6,}  ({pct:.1f}%)")
