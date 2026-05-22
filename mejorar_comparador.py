"""
Mejoras al CSV del Comparador de Tarifas Moviles.
Aplica TODAS las mejoras posibles sobre tarifas_comparador_vigentes.csv
y genera una version mejorada in-place (reemplaza el archivo).
"""

import csv
import re
import os
import shutil
from datetime import datetime

INPUT  = r"c:\Users\ivan-\Documents\GitHub\tarifas_servicios_moviles\tarifas_comparador_vigentes.csv"
BACKUP = r"c:\Users\ivan-\Documents\GitHub\tarifas_servicios_moviles\tarifas_comparador_vigentes_BACKUP.csv"
OUTPUT = r"c:\Users\ivan-\Documents\GitHub\tarifas_servicios_moviles\tarifas_comparador_vigentes.csv"

# ─────────────────────────────────────────────────────────
# NUEVOS CAMPOS A AGREGAR
# ─────────────────────────────────────────────────────────
NUEVAS_COLS = [
    "PRECIO_REFERENCIA_MXN",   # Precio unificado: recarga o renta (el que exista)
    "PRECIO_POR_GB",           # Precio / DATOS_GB  (comparacion directa de valor)
    "VIGENCIA_TIPO",           # DIARIO/SEMANAL/MENSUAL/TRIMESTRAL/SEMESTRAL/ANUAL
    "DATOS_GB_NORM",           # GB normalizados correctamente (arregla KB/MB/TB/ILIMITADO)
    "VELOCIDAD_MAX_MBPS",      # Velocidad maxima extraida de descripcion
    "VELOCIDAD_THROTTLE_KBPS", # Velocidad tras agotar datos (throttling)
    "HOTSPOT_INCLUIDO",        # SI/NO — compartir datos / tethering
    "LLAMADAS_USA_CANADA",     # SI/NO — llamadas a USA y Canada incluidas
    "MINUTOS_ILIMITADOS",      # SI/NO
    "SMS_ILIMITADOS",          # SI/NO
    "APPS_STREAMING",          # Netflix, Disney, Spotify, etc. incluidos
    "APPS_RSSS_LISTA",         # WhatsApp, Facebook, Instagram, etc. (lista limpia)
    "RED_TECNOLOGIA",          # 2G/3G/4G LTE/5G detectada en descripcion
    "FECHA_INICIO_ISO",        # Fecha inicio en formato YYYY-MM-DD
    "FECHA_FIN_ISO",           # Fecha fin en formato YYYY-MM-DD
    "NOMBRE_TARIFA_LIMPIO",    # Nombre sin tabs, dobles espacios, caracteres raros
    "OPERADOR_GRUPO",          # Grupo corporativo: ATT / TELCEL / MOVISTAR / OTRO
]

# ─────────────────────────────────────────────────────────
# PATRONES DE EXTRACCION
# ─────────────────────────────────────────────────────────
RE_VELOCIDAD_MAX    = re.compile(r'hasta\s+([\d,\.]+)\s*(Mbps|Gbps)', re.IGNORECASE)
RE_VELOCIDAD_MAX2   = re.compile(r'([\d,\.]+)\s*(Mbps|Gbps)\s+(?:de\s+)?velocidad', re.IGNORECASE)
RE_THROTTLE         = re.compile(r'([\d,\.]+)\s*(Kbps|Mbps)(?:\s+de\s+velocidad)?\s*(?:reducida|throttling|limitada|minima)', re.IGNORECASE)
RE_THROTTLE2        = re.compile(r'velocidad\s+(?:se\s+)?(?:reduce|reducira|limitara|limita|baja)\s+(?:a\s+)?([\d,\.]+)\s*(Kbps|Mbps)', re.IGNORECASE)
RE_THROTTLE3        = re.compile(r'([\d,\.]+)\s*(Kbps|Mbps)\s+(?:hasta|por\s+el\s+resto)', re.IGNORECASE)
RE_MIN_NUM          = re.compile(r'([\d,\.]+)\s*min(?:utos?)?(?:\s+(?:nacionales?|en\s+mexico|incluidos?))?', re.IGNORECASE)
RE_SMS_NUM          = re.compile(r'([\d,\.]+)\s*(?:sms|mensajes\s+de\s+texto)(?:\s+(?:nacionales?|incluidos?))?', re.IGNORECASE)

APPS_STREAMING_MAP = {
    "netflix": "Netflix",
    "disney": "Disney+",
    "hbo": "HBO Max",
    " max ": "HBO Max",
    "max incluido": "HBO Max",
    "spotify": "Spotify",
    "amazon prime": "Amazon Prime",
    "apple tv": "Apple TV+",
    "youtube": "YouTube Premium",
    "deezer": "Deezer",
    "tidal": "Tidal",
    "paramount": "Paramount+",
    "star+": "Star+",
    "vix": "Vix",
    "claro video": "Claro Video",
    "izzi go": "Izzi Go",
    "sky showtime": "SkyShowtime",
}

APPS_RSSS_MAP = {
    "whatsapp": "WhatsApp",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "twitter": "Twitter/X",
    "tiktok": "TikTok",
    "snapchat": "Snapchat",
    "telegram": "Telegram",
    "messenger": "Messenger",
    "pinterest": "Pinterest",
    "linkedin": "LinkedIn",
    "waze": "Waze",
    "google maps": "Google Maps",
    "youtube": "YouTube",
    "zoom": "Zoom",
    "teams": "Microsoft Teams",
}

GRUPOS_OPERADOR = {
    "TELCEL": "TELCEL",
    "AT&T": "AT&T",
    "MOVISTAR": "MOVISTAR",
    "NEXTEL": "AT&T",
    "VIRGIN MOBILE": "VIRGIN MOBILE",
    "MEGA CABLE": "MEGA CABLE",
    "FREEDOMPOP": "FREEDOMPOP",
    "ABIB": "ABIB",
    "NABY": "NABY",
    "NOX": "NOX",
    "IZZI": "IZZI",
}


# ─────────────────────────────────────────────────────────
# FUNCIONES DE EXTRACCION
# ─────────────────────────────────────────────────────────

def to_float(val):
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def normalizar_fecha(fecha_str):
    """Convierte DD/MM/YYYY a YYYY-MM-DD."""
    if not fecha_str or not fecha_str.strip():
        return ""
    s = fecha_str.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s  # retorna tal cual si no se puede parsear


def extraer_velocidad_max(desc):
    """Extrae velocidad maxima en Mbps desde descripcion."""
    m = RE_VELOCIDAD_MAX.search(desc)
    if not m:
        m = RE_VELOCIDAD_MAX2.search(desc)
    if m:
        val = to_float(m.group(1))
        unit = m.group(2).lower()
        if val is not None:
            if "gbps" in unit:
                return str(round(val * 1000, 2))
            return str(int(val))
    return ""


def extraer_throttle(desc):
    """Extrae velocidad de throttling en Kbps."""
    for pat in [RE_THROTTLE, RE_THROTTLE2, RE_THROTTLE3]:
        m = pat.search(desc)
        if m:
            val = to_float(m.group(1))
            unit = m.group(2).lower()
            if val is not None:
                if "mbps" in unit:
                    return str(int(val * 1024))
                return str(int(val))
    # Patron especifico comun: "512 Kbps" solo
    m = re.search(r'\b(128|256|512|1024|2048)\s*Kbps\b', desc, re.IGNORECASE)
    if m:
        return m.group(1)
    return ""


def extraer_apps_streaming(desc):
    """Extrae apps de streaming mencionadas."""
    d = desc.lower()
    encontradas = []
    for key, nombre in APPS_STREAMING_MAP.items():
        if key in d and nombre not in encontradas:
            encontradas.append(nombre)
    return " | ".join(encontradas)


def extraer_apps_rsss(desc, rsss_desc_original):
    """Extrae apps de redes sociales."""
    d = (desc + " " + rsss_desc_original).lower()
    encontradas = []
    for key, nombre in APPS_RSSS_MAP.items():
        if key in d and nombre not in encontradas:
            encontradas.append(nombre)
    return " | ".join(encontradas)


def extraer_red_tecnologia(desc):
    """Detecta tecnologia de red 5G/4G/3G/2G."""
    d = desc.upper()
    redes = []
    if "5G" in d:
        redes.append("5G")
    if "4G" in d or "LTE" in d:
        redes.append("4G LTE")
    if "3G" in d:
        redes.append("3G")
    if "2G" in d or "GSM" in d or "EDGE" in d:
        redes.append("2G")
    return " | ".join(redes) if redes else ""


def determinar_vigencia_tipo(dias_str):
    """Clasifica la vigencia en tipo semantico."""
    v = to_float(dias_str)
    if v is None:
        return ""
    v = int(v)
    if v <= 0:   return "INMEDIATA"
    if v == 1:   return "DIARIA"
    if v <= 3:   return "2-3 DIAS"
    if v <= 7:   return "SEMANAL"
    if v <= 15:  return "QUINCENAL"
    if v <= 31:  return "MENSUAL"
    if v <= 62:  return "BIMESTRAL"
    if v <= 93:  return "TRIMESTRAL"
    if v <= 186: return "SEMESTRAL"
    if v <= 366: return "ANUAL"
    return "MAS DE UN ANO"


def normalizar_datos_gb(cap_val, cap_unit, datos_mb_actual, datos_gb_actual):
    """
    Recalcula DATOS_GB correctamente desde la fuente,
    manejando TB, GB, MB, KB, ILIMITADO.
    """
    unit = str(cap_unit).upper().strip()
    
    # Caso ILIMITADO ya marcado
    if unit == "ILIMITADO" or (cap_val and "ILIMITADO" in str(cap_val).upper()):
        return "ILIMITADO"
    
    # Si ya tenemos DATOS_MB calculado, usarlo
    if datos_mb_actual:
        mb = to_float(datos_mb_actual)
        if mb and mb > 0:
            if mb >= 1024 * 1024:  # >= 1 TB
                return str(round(mb / 1024 / 1024, 2)) + " TB"
            if mb >= 1024:
                return str(round(mb / 1024, 2))
            return str(round(mb / 1024, 4))  # menos de 1 GB
    
    # Calcular desde valor y unidad originales
    val = to_float(cap_val)
    if val is None:
        return datos_gb_actual or ""
    
    if "TB" in unit:
        return str(round(val * 1024, 2))
    if "GB" in unit:
        return str(round(val, 2))
    if "MB" in unit:
        return str(round(val / 1024, 4))
    if "KB" in unit:
        return str(round(val / 1024 / 1024, 6))
    
    return datos_gb_actual or ""


def precio_referencia(precio_recarga, renta_con_iva):
    """Precio unificado: toma el que exista (prioriza renta sobre recarga)."""
    r = str(renta_con_iva).strip()
    p = str(precio_recarga).strip()
    if r and to_float(r) and to_float(r) > 0:
        return r
    if p and to_float(p) and to_float(p) > 0:
        return p
    return ""


def precio_por_gb(precio_ref, datos_gb_norm):
    """Calcula precio / GB. Retorna vacio si ILIMITADO o sin datos."""
    if datos_gb_norm == "ILIMITADO" or not datos_gb_norm:
        return ""
    # Quitar TB al final si lo hay
    gb_str = str(datos_gb_norm).replace(" TB", "").strip()
    gb = to_float(gb_str)
    precio = to_float(precio_ref)
    if gb and precio and gb > 0 and precio > 0:
        return str(round(precio / gb, 2))
    return ""


def determinar_grupo_operador(nombre_operador):
    """Agrupa operadores por marca corporativa."""
    n = str(nombre_operador).upper()
    for key, grupo in GRUPOS_OPERADOR.items():
        if key in n:
            return grupo
    return "OTRO"


def limpiar_nombre_tarifa(nombre):
    """Limpia tabs, saltos de linea y espacios multiples del nombre."""
    if not nombre:
        return ""
    s = nombre.replace("\t", " ").replace("\r", " ").replace("\n", " ")
    s = re.sub(r'\s{2,}', ' ', s)
    return s.strip()


def es_hotspot(desc):
    return "SI" if re.search(r'hotspot|compartir\s+datos|tethering|punto\s+de\s+acceso', desc, re.IGNORECASE) else "NO"


def es_llamadas_usa_canada(desc):
    d = desc.lower()
    patrones = [
        "usa y canad", "ee.uu. y canad", "estados unidos y canad",
        "mexico, usa", "mexico, ee.uu", "mexico, estados unidos",
        "llam.*canad", "canad.*llam", "roaming.*usa", "usa.*roaming",
    ]
    for p in patrones:
        if re.search(p, d):
            return "SI"
    return "NO"


def es_minutos_ilimitados(minutos_str, desc):
    if str(minutos_str).strip().upper() == "ILIMITADOS":
        return "SI"
    d = desc.lower()
    if re.search(r'minutos?\s+ilimitados?|llamadas?\s+ilimitadas?', d):
        return "SI"
    return "NO"


def es_sms_ilimitados(sms_str, desc):
    if str(sms_str).strip().upper() == "ILIMITADOS":
        return "SI"
    d = desc.lower()
    if re.search(r'sms\s+ilimitados?|mensajes?\s+ilimitados?', d):
        return "SI"
    return "NO"


# ─────────────────────────────────────────────────────────
# PROCESO PRINCIPAL
# ─────────────────────────────────────────────────────────

def mejorar_fila(row):
    """Aplica todas las mejoras a una fila existente y retorna dict actualizado."""
    desc = row.get("DESCRIPCION_CORTA", "") or ""
    rsss = row.get("RSSS_DESCRIPCION", "") or ""
    
    # Descripcion completa para extraccion (concatenar ambas)
    desc_full = desc + " " + rsss

    # Calcular precio referencia
    pref = precio_referencia(row.get("PRECIO_RECARGA_MXN",""), row.get("RENTA_MENSUAL_CON_IVA",""))

    # Datos GB normalizados (recalcular)
    datos_gb_norm = normalizar_datos_gb(
        row.get("DATOS_MB", ""),        # ya normalizado a MB en paso anterior
        row.get("DATOS_UNIDAD_ORIGINAL", ""),
        row.get("DATOS_MB", ""),
        row.get("DATOS_GB", ""),
    )
    # Si la unidad original era ILIMITADO
    if row.get("DATOS_ILIMITADOS","") == "SI":
        datos_gb_norm = "ILIMITADO"

    # Precio por GB
    ppgb = precio_por_gb(pref, datos_gb_norm)

    # Velocidad
    vel_max = extraer_velocidad_max(desc_full)
    vel_thr = extraer_throttle(desc_full)

    # Apps
    apps_stream = extraer_apps_streaming(desc_full)
    apps_rsss   = extraer_apps_rsss(desc_full, rsss)

    # Red
    red = extraer_red_tecnologia(desc_full)

    # Fechas ISO
    f_inicio_iso = normalizar_fecha(row.get("FECHA_INICIO_VIGENCIA",""))
    f_fin_iso    = normalizar_fecha(row.get("FECHA_FIN_VIGENCIA",""))

    # Minutos/SMS
    min_str = row.get("MINUTOS_INCLUIDOS","") or ""
    sms_str = row.get("SMS_INCLUIDOS","") or ""

    # Mejoras adicionales a campos existentes
    row["NOMBRE_TARIFA"] = limpiar_nombre_tarifa(row.get("NOMBRE_TARIFA",""))
    row["DESCRIPCION_CORTA"] = (row.get("DESCRIPCION_CORTA","") or "").strip()

    # Nuevos campos
    row["PRECIO_REFERENCIA_MXN"]   = pref
    row["PRECIO_POR_GB"]           = ppgb
    row["VIGENCIA_TIPO"]           = determinar_vigencia_tipo(row.get("VIGENCIA_DIAS",""))
    row["DATOS_GB_NORM"]           = datos_gb_norm
    row["VELOCIDAD_MAX_MBPS"]      = vel_max
    row["VELOCIDAD_THROTTLE_KBPS"] = vel_thr
    row["HOTSPOT_INCLUIDO"]        = es_hotspot(desc_full)
    row["LLAMADAS_USA_CANADA"]     = es_llamadas_usa_canada(desc_full)
    row["MINUTOS_ILIMITADOS"]      = es_minutos_ilimitados(min_str, desc_full)
    row["SMS_ILIMITADOS"]          = es_sms_ilimitados(sms_str, desc_full)
    row["APPS_STREAMING"]          = apps_stream
    row["APPS_RSSS_LISTA"]         = apps_rsss
    row["RED_TECNOLOGIA"]          = red
    row["FECHA_INICIO_ISO"]        = f_inicio_iso
    row["FECHA_FIN_ISO"]           = f_fin_iso
    row["NOMBRE_TARIFA_LIMPIO"]    = limpiar_nombre_tarifa(row.get("NOMBRE_TARIFA",""))
    row["OPERADOR_GRUPO"]          = determinar_grupo_operador(row.get("OPERADOR_NOMBRE",""))

    return row


def main():
    # Backup
    print(f"Haciendo backup -> {BACKUP}")
    shutil.copy2(INPUT, BACKUP)

    # Leer todo
    print("Leyendo CSV...")
    with open(INPUT, "r", encoding="utf-8-sig") as fp:
        reader = csv.DictReader(fp)
        original_cols = reader.fieldnames[:]
        filas = list(reader)

    print(f"Filas leidas: {len(filas):,}")

    # Columnas finales: originales + nuevas
    nuevas_cols_a_agregar = [c for c in NUEVAS_COLS if c not in original_cols]
    all_cols = original_cols + nuevas_cols_a_agregar
    print(f"Columnas originales: {len(original_cols)}")
    print(f"Columnas nuevas a agregar: {len(nuevas_cols_a_agregar)}")
    print(f"Total columnas finales: {len(all_cols)}")

    # Procesar
    print("Aplicando mejoras...")
    mejoradas = []
    stats = {
        "con_velocidad": 0, "con_throttle": 0, "con_hotspot": 0,
        "con_llamadas_usa": 0, "con_apps_stream": 0, "con_apps_rsss": 0,
        "con_red": 0, "con_precio_ref": 0, "con_ppgb": 0, "ilimitados": 0,
    }

    for i, row in enumerate(filas):
        if i % 15000 == 0 and i > 0:
            print(f"  {i:,} / {len(filas):,}...")
        
        # Inicializar nuevas cols en vacio
        for c in nuevas_cols_a_agregar:
            if c not in row:
                row[c] = ""
        
        row = mejorar_fila(row)
        
        # Stats
        if row["VELOCIDAD_MAX_MBPS"]:      stats["con_velocidad"]   += 1
        if row["VELOCIDAD_THROTTLE_KBPS"]: stats["con_throttle"]    += 1
        if row["HOTSPOT_INCLUIDO"] == "SI": stats["con_hotspot"]     += 1
        if row["LLAMADAS_USA_CANADA"] == "SI": stats["con_llamadas_usa"] += 1
        if row["APPS_STREAMING"]:          stats["con_apps_stream"] += 1
        if row["APPS_RSSS_LISTA"]:         stats["con_apps_rsss"]   += 1
        if row["RED_TECNOLOGIA"]:          stats["con_red"]         += 1
        if row["PRECIO_REFERENCIA_MXN"]:   stats["con_precio_ref"]  += 1
        if row["PRECIO_POR_GB"]:           stats["con_ppgb"]        += 1
        if row["DATOS_GB_NORM"] == "ILIMITADO": stats["ilimitados"] += 1
        
        mejoradas.append(row)

    # Escribir CSV mejorado (sobreescribe el original)
    print(f"\nEscribiendo CSV mejorado -> {OUTPUT}")
    with open(OUTPUT, "w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=all_cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(mejoradas)

    size_mb = os.path.getsize(OUTPUT) / 1024 / 1024
    print(f"\n=== RESULTADO ===")
    print(f"Filas mejoradas:            {len(mejoradas):,}")
    print(f"Columnas totales:           {len(all_cols)}")
    print(f"Tamano archivo:             {size_mb:.1f} MB")
    print(f"\n--- CAMPOS NUEVOS EXTRAIDOS ---")
    for k, v in stats.items():
        pct = v / len(mejoradas) * 100 if mejoradas else 0
        print(f"  {k:25s}: {v:6,}  ({pct:.1f}%)")
    print(f"\nBackup guardado en: {BACKUP}")
    print("LISTO.")


if __name__ == "__main__":
    main()
