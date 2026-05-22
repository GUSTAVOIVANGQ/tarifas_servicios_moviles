"""
Script de normalización y mejora de datos para el Comparador de Tarifas Móviles
Genera un CSV optimizado con las filas más completas de la base de datos original.
"""

import csv
import os
import re
from datetime import datetime

INPUT_FILE = r"c:\Users\ivan-\Documents\GitHub\tarifas_servicios_moviles\05_tarifas_servicios_moviles_febrero26_gustavo.csv"
OUTPUT_FILE = r"c:\Users\ivan-\Documents\GitHub\tarifas_servicios_moviles\tarifas_moviles_normalizado.csv"

# Columnas originales (50 columnas)
ORIGINAL_COLS = [
    "ID_TARIFA", "ID_OPERADOR", "CONCESIONARIO", "FLAG_TARIFA", "FLAG_PROMOCION",
    "FLAG_PAQUETE", "NOMBRE_TARIFA", "FLAG_SUSTITUYE_TARIFA", "ID_TARIFA_SUSTITUYE",
    "DENOMINACION", "ID_TARIFA_PROMOCION", "FECHA_INICIO_VIGENCIA", "FECHA_FIN_VIGENCIA",
    "FECHA_CANCELACION", "ESTATUS", "FLAG_SERVICIO_PREPAGO", "FLAG_SERVICIO_POSPAGO",
    "FLAG_SERVICIO_PAQUETE", "FLAG_SERVICIOS_DIVERSOS", "FLAG_PARTICULAR", "FLAG_EMPRESARIAL",
    "DESCRIPCIÓN", "SERVICIOS", "MONTO_RECARGA", "VIGENCIA_SALDO_RECARGA",
    "SALDO_PROMOCIONAL", "VIGENCIA_SALDO_PROMOCIONAL", "SALDO_TOTAL",
    "RENTA_MENSUAL_SIN_IMPUESTOS", "RENTA_MENSUAL_CON_IMPUESTOS",
    "FLAG_PLAN_POSPAGO", "FLAG_PLAN_CONTROLADO", "LINEAS_INCLUIDAS",
    "COSTO_LINEA_ADICIONAL", "PLAZO_MINIMO_PERMANENCIA", "EQUIPOS_TERMINALES",
    "CAPACIDAD_INCLUIDA", "CAPACIDAD_UNIDAD_MOVIL", "CAPAC_ADIC_COSTO_SIN_IMPUESTO",
    "CAPA_ ADIC_COSTO_CON_IMPUESTO", "CAPACIDAD_ADICIONAL_UNIDAD",
    "FLAG_ROAMING_USA_MOVIL", "FLAG_ROAMING_CANADA_MOVIL", "FLAG_ROAMING_OTROS_MOVIL",
    "REDES_SOCIALES", "CAPACIDAD", "CAPACIDAD_UNIDAD_SOCIALM",
    "FLAG_ROAMING_USA_SOCIALM", "FLAG_ROAMING_CANADA_SOCIALM", "FLAG_ROAMING_OTROS_SOCIALM"
]

# Nuevas columnas normalizadas para el comparador de tarifas
OUTPUT_COLS = [
    # --- IDENTIFICACIÓN ---
    "ID_TARIFA",
    "OPERADOR_NOMBRE",           # Nombre limpio del operador (sin S.A. DE C.V. etc.)
    "NOMBRE_TARIFA",
    "DENOMINACION",
    
    # --- CLASIFICACIÓN DEL PLAN ---
    "TIPO_PLAN",                 # PREPAGO / POSPAGO / CONTROL / PAQUETE
    "SEGMENTO",                  # PARTICULAR / EMPRESARIAL / AMBOS
    "ES_PROMOCION",              # SI/NO
    "ES_PAQUETE",                # SI/NO
    
    # --- VIGENCIA ---
    "FECHA_INICIO_VIGENCIA",
    "FECHA_FIN_VIGENCIA",
    "ESTATUS",                   # VIGENTE / NO-VIGENTE
    
    # --- SERVICIOS INCLUIDOS ---
    "SERVICIO_INTERNET",         # SI/NO
    "SERVICIO_VOZ",              # SI/NO
    "SERVICIO_SMS",              # SI/NO
    "SERVICIO_LD",               # SI/NO - Larga distancia
    "SERVICIO_DATOS_TX",         # SI/NO - Transmisión de datos
    "SERVICIO_RSSS",             # SI/NO - Redes sociales sin costo extra
    
    # --- PRECIOS ---
    "PRECIO_RECARGA_MXN",        # Para prepago: monto de recarga
    "VIGENCIA_DIAS",             # Vigencia en días
    "RENTA_MENSUAL_CON_IVA",     # Para pospago: renta mensual con IVA
    "RENTA_MENSUAL_SIN_IVA",     # Para pospago: renta mensual sin IVA
    
    # --- DATOS MÓVILES ---
    "DATOS_MB",                  # Datos en MB (normalizado a MB)
    "DATOS_GB",                  # Datos en GB (calculado)
    "DATOS_UNIDAD_ORIGINAL",     # Unidad original (MB/GB/KB)
    "DATOS_ILIMITADOS",          # SI/NO
    
    # --- CAPACIDAD ADICIONAL DE DATOS ---
    "DATOS_ADIC_COSTO_SIN_IVA",  # Costo por capacidad adicional sin IVA
    "DATOS_ADIC_COSTO_CON_IVA",  # Costo por capacidad adicional con IVA
    "DATOS_ADIC_UNIDAD",         # Unidad de capacidad adicional
    
    # --- VOZ ---
    "MINUTOS_INCLUIDOS",         # Estimado de minutos (cuando está en descripción)
    
    # --- SMS ---
    "SMS_INCLUIDOS",             # Estimado de SMS (cuando está en descripción)
    
    # --- ROAMING ---
    "ROAMING_USA",               # SI/NO
    "ROAMING_CANADA",            # SI/NO
    "ROAMING_OTROS",             # SI/NO
    
    # --- REDES SOCIALES ---
    "RSSS_DESCRIPCION",          # Descripción de redes sociales incluidas
    "RSSS_CAPACIDAD_MB",         # Capacidad de datos para RSSS en MB
    "RSSS_ILIMITADAS",           # SI/NO
    
    # --- POSPAGO ---
    "LINEAS_INCLUIDAS",
    "COSTO_LINEA_ADICIONAL",
    "PLAZO_MINIMO_MESES",        # Permanencia mínima en meses
    
    # --- METADATOS / DESCRIPCIÓN ---
    "DESCRIPCION_CORTA",         # Primeros 300 chars de descripción
    "SERVICIOS_LISTA",           # Lista de servicios separados por |
    
    # --- SCORE DE COMPLETITUD ---
    "SCORE_COMPLETITUD",         # 0-100 qué tan completa está la fila
]


def limpiar_operador(nombre):
    """Limpia el nombre del operador eliminando formas jurídicas."""
    if not nombre:
        return ""
    # Mapeo de nombres cortos conocidos
    mapa = {
        "RADIOMÓVIL DIPSA": "TELCEL",
        "RADIOMOVIL DIPSA": "TELCEL",
        "PEGASO PCS": "MOVISTAR",
        "AT&T OPCO UNE MEX": "AT&T",
        "AT&T DESARROLLO EN COMUNICACIONES DE MEXICO": "AT&T (IUSACELL)",
        "AT&T NORTE": "AT&T Norte",
        "AT&T DEL OCCIDENTE": "AT&T Occidente",
        "AT&T COMCENTRO": "AT&T Comcentro",
        "AT&T DEL GOLFO": "AT&T Golfo",
        "AT&T SURESTE": "AT&T Sureste",
        "AT&T CENTRAL": "AT&T Central",
        "AT&T DIGITAL": "NEXTEL/AT&T",
        "AT&T NTELCOMMEX": "NEXTEL",
        "AT&T COMUNICACIONES DIGITALES": "AT&T",
        "VIRGIN MOBILE MEXICO": "VIRGIN MOBILE",
        "MARLASANTAELLAROD": "ABIB",
        "MARLASANTAELLARODRÍGUEZ": "ABIB",
        "ALLESKLAR": "NABY",
        "SOLUCIONIKA": "NOX",
        "QUICKLY PHONE": "QUICKLY PHONE",
        "KUBO CEL": "KUBO CEL",
        "RADIOCOMUNICACIONES Y SERVICIOS": "RADIOCOMUNICACIONES",
        "GRUPO AT&T CELULLAR": "AT&T",
        "AT&T COMERCIALIZACIÓN MÓVIL": "AT&T",
    }
    n = nombre.strip()
    for key, val in mapa.items():
        if key.upper() in n.upper():
            return val
    # Si no hay mapeo, quitar formas jurídicas comunes
    for suffix in [
        ", S.A. DE C.V.", " S.A. DE C.V.", ", S. DE R.L. DE C.V.", " S.DE R.L. DE C.V.",
        " S. DE R.L.", ", S.DE R.L.", " S.A.P.I. DE C.V.", " DE C.V.", ", S.A.",
    ]:
        n = n.replace(suffix, "").replace(suffix.upper(), "")
    return n.strip()


def determinar_tipo_plan(row):
    """Determina el tipo de plan: PREPAGO/POSPAGO/CONTROL/PAQUETE."""
    prepago = str(row.get("FLAG_SERVICIO_PREPAGO", "0")).strip() == "1"
    pospago = str(row.get("FLAG_SERVICIO_POSPAGO", "0")).strip() == "1"
    paquete_flag = str(row.get("FLAG_SERVICIO_PAQUETE", "0")).strip() == "1"
    controlado = str(row.get("FLAG_PLAN_CONTROLADO", "0")).strip() == "1"
    es_paquete = str(row.get("FLAG_PAQUETE", "0")).strip() == "1"
    
    if es_paquete or paquete_flag:
        if prepago:
            return "PREPAGO-PAQUETE"
        return "PAQUETE"
    if prepago:
        return "PREPAGO"
    if pospago:
        if controlado:
            return "CONTROL"
        return "POSPAGO"
    return "DESCONOCIDO"


def determinar_segmento(row):
    particular = str(row.get("FLAG_PARTICULAR", "0")).strip() == "1"
    empresarial = str(row.get("FLAG_EMPRESARIAL", "0")).strip() == "1"
    if particular and empresarial:
        return "AMBOS"
    if particular:
        return "PARTICULAR"
    if empresarial:
        return "EMPRESARIAL"
    return "N/D"


def extraer_servicios(servicios_str):
    """Extrae flags de servicios de la cadena de texto."""
    s = servicios_str.upper() if servicios_str else ""
    return {
        "internet": "INTERNET" in s,
        "voz": "TELEFONIA CELULAR" in s or "TELEFONIA MOVIL" in s,
        "ld": "LARGA DISTANCIA" in s,
        "datos": "TRANSMISION" in s and "DATOS" in s,
    }


def normalizar_capacidad_a_mb(valor, unidad):
    """Convierte cualquier valor de capacidad a MB."""
    try:
        v = float(str(valor).replace(",", "").strip())
    except (ValueError, TypeError):
        return None
    
    unidad = str(unidad).upper().strip() if unidad else ""
    if "GB" in unidad:
        return v * 1024
    elif "MB" in unidad:
        return v
    elif "KB" in unidad:
        return v / 1024
    return v  # Asumir MB si no hay unidad


def extraer_minutos_descripcion(desc):
    """Intenta extraer minutos de la descripción."""
    if not desc:
        return ""
    # Patrones comunes: "1500 min", "1,500 minutos", "ilimitados"
    if "ilimitad" in desc.lower() and ("minuto" in desc.lower() or "min" in desc.lower()):
        return "ILIMITADOS"
    m = re.search(r'([\d,\.]+)\s*(min(?:utos?)?)', desc, re.IGNORECASE)
    if m:
        return m.group(1).replace(",", "")
    return ""


def extraer_sms_descripcion(desc):
    """Intenta extraer SMS de la descripción."""
    if not desc:
        return ""
    if "ilimitad" in desc.lower() and "sms" in desc.lower():
        return "ILIMITADOS"
    m = re.search(r'([\d,\.]+)\s*(sms|mensajes)', desc, re.IGNORECASE)
    if m:
        return m.group(1).replace(",", "")
    return ""


def calcular_score(out_row):
    """Calcula un score 0-100 de completitud de la fila."""
    campos_clave = [
        "OPERADOR_NOMBRE", "NOMBRE_TARIFA", "TIPO_PLAN", "ESTATUS",
        "PRECIO_RECARGA_MXN", "RENTA_MENSUAL_CON_IVA",
        "DATOS_MB", "VIGENCIA_DIAS",
        "SERVICIO_VOZ", "SERVICIO_INTERNET",
    ]
    score = 0
    for c in campos_clave:
        val = out_row.get(c, "")
        if val and str(val).strip() not in ("", "0", "NO", "N/D"):
            score += 10
    # Bonus por campos adicionales
    bonus_campos = [
        "ROAMING_USA", "ROAMING_CANADA", "MINUTOS_INCLUIDOS", "SMS_INCLUIDOS",
        "DESCRIPCION_CORTA", "DATOS_ADIC_COSTO_CON_IVA"
    ]
    for c in bonus_campos:
        val = out_row.get(c, "")
        if val and str(val).strip() not in ("", "0", "NO", "N/D"):
            score = min(score + 5, 100)
    return score


def flag_si_no(val):
    return "SI" if str(val).strip() == "1" else "NO"


def procesar_fila(row):
    """Transforma una fila original en la fila normalizada."""
    # Servicios
    svcs = extraer_servicios(row.get("SERVICIOS", ""))
    
    # Precios
    precio_recarga = row.get("MONTO_RECARGA", "").strip()
    saldo_total = row.get("SALDO_TOTAL", "").strip()
    renta_con_iva = row.get("RENTA_MENSUAL_CON_IMPUESTOS", "").strip()
    renta_sin_iva = row.get("RENTA_MENSUAL_SIN_IMPUESTOS", "").strip()
    
    # Capacidad de datos móviles
    cap_val = row.get("CAPACIDAD_INCLUIDA", "").strip()
    cap_unit = row.get("CAPACIDAD_UNIDAD_MOVIL", "").strip()
    datos_mb = normalizar_capacidad_a_mb(cap_val, cap_unit) if cap_val else None
    datos_gb = round(datos_mb / 1024, 2) if datos_mb else None
    datos_ilimitados = "NO"
    if cap_unit.upper() in ("KB",) and (not cap_val or cap_val == "0"):
        datos_ilimitados = "NO"
    desc = row.get("DESCRIPCIÓN", "")
    if "ilimitad" in desc.lower() and "datos" in desc.lower():
        datos_ilimitados = "SI"
    
    # Vigencia
    vigencia = row.get("VIGENCIA_SALDO_RECARGA", "").strip()
    
    # Capacidad adicional
    adic_sin_iva = row.get("CAPAC_ADIC_COSTO_SIN_IMPUESTO", "").strip()
    adic_con_iva = row.get("CAPA_ ADIC_COSTO_CON_IMPUESTO", "").strip()
    adic_unit = row.get("CAPACIDAD_ADICIONAL_UNIDAD", "").strip()
    
    # Redes sociales
    rsss_desc = row.get("REDES_SOCIALES", "").strip()
    rsss_cap = row.get("CAPACIDAD", "").strip()
    rsss_unit = row.get("CAPACIDAD_UNIDAD_SOCIALM", "").strip()
    rsss_mb = normalizar_capacidad_a_mb(rsss_cap, rsss_unit) if rsss_cap else None
    rsss_ilimitadas = "SI" if rsss_cap and "ILIMITADO" in rsss_cap.upper() else "NO"
    
    # Descripción corta (primeros 300 chars)
    desc_corta = desc[:300].replace("\n", " ").replace("\r", " ").strip() if desc else ""
    
    # Servicios como lista
    svcs_original = row.get("SERVICIOS", "").strip()
    svcs_lista = svcs_original.replace(",", "|") if svcs_original else ""
    
    # Minutos y SMS desde descripción
    minutos = extraer_minutos_descripcion(desc)
    sms = extraer_sms_descripcion(desc)
    
    # Plazo mínimo
    plazo = row.get("PLAZO_MINIMO_PERMANENCIA", "").strip()
    
    out = {
        "ID_TARIFA": row.get("ID_TARIFA", "").strip(),
        "OPERADOR_NOMBRE": limpiar_operador(row.get("CONCESIONARIO", "")),
        "NOMBRE_TARIFA": row.get("NOMBRE_TARIFA", "").strip(),
        "DENOMINACION": row.get("DENOMINACION", "").strip(),
        
        "TIPO_PLAN": determinar_tipo_plan(row),
        "SEGMENTO": determinar_segmento(row),
        "ES_PROMOCION": flag_si_no(row.get("FLAG_PROMOCION", "0")),
        "ES_PAQUETE": flag_si_no(row.get("FLAG_PAQUETE", "0")),
        
        "FECHA_INICIO_VIGENCIA": row.get("FECHA_INICIO_VIGENCIA", "").strip(),
        "FECHA_FIN_VIGENCIA": row.get("FECHA_FIN_VIGENCIA", "").strip(),
        "ESTATUS": row.get("ESTATUS", "").strip(),
        
        "SERVICIO_INTERNET": "SI" if svcs["internet"] else "NO",
        "SERVICIO_VOZ": "SI" if svcs["voz"] else "NO",
        "SERVICIO_SMS": "SI" if "sms" in desc.lower() or "mensajes de texto" in desc.lower() else "NO",
        "SERVICIO_LD": "SI" if svcs["ld"] else "NO",
        "SERVICIO_DATOS_TX": "SI" if svcs["datos"] else "NO",
        "SERVICIO_RSSS": "SI" if rsss_desc else "NO",
        
        "PRECIO_RECARGA_MXN": precio_recarga or saldo_total,
        "VIGENCIA_DIAS": vigencia,
        "RENTA_MENSUAL_CON_IVA": renta_con_iva,
        "RENTA_MENSUAL_SIN_IVA": renta_sin_iva,
        
        "DATOS_MB": str(round(datos_mb, 2)) if datos_mb else "",
        "DATOS_GB": str(datos_gb) if datos_gb else "",
        "DATOS_UNIDAD_ORIGINAL": cap_unit,
        "DATOS_ILIMITADOS": datos_ilimitados,
        
        "DATOS_ADIC_COSTO_SIN_IVA": adic_sin_iva,
        "DATOS_ADIC_COSTO_CON_IVA": adic_con_iva,
        "DATOS_ADIC_UNIDAD": adic_unit,
        
        "MINUTOS_INCLUIDOS": minutos,
        "SMS_INCLUIDOS": sms,
        
        "ROAMING_USA": flag_si_no(row.get("FLAG_ROAMING_USA_MOVIL", "0")),
        "ROAMING_CANADA": flag_si_no(row.get("FLAG_ROAMING_CANADA_MOVIL", "0")),
        "ROAMING_OTROS": flag_si_no(row.get("FLAG_ROAMING_OTROS_MOVIL", "0")),
        
        "RSSS_DESCRIPCION": rsss_desc,
        "RSSS_CAPACIDAD_MB": str(round(rsss_mb, 2)) if rsss_mb else "",
        "RSSS_ILIMITADAS": rsss_ilimitadas,
        
        "LINEAS_INCLUIDAS": row.get("LINEAS_INCLUIDAS", "").strip(),
        "COSTO_LINEA_ADICIONAL": row.get("COSTO_LINEA_ADICIONAL", "").strip(),
        "PLAZO_MINIMO_MESES": plazo,
        
        "DESCRIPCION_CORTA": desc_corta,
        "SERVICIOS_LISTA": svcs_lista,
        
        "SCORE_COMPLETITUD": 0,
    }
    
    out["SCORE_COMPLETITUD"] = calcular_score(out)
    return out


def es_fila_util(out_row, umbral_score=30):
    """Filtra filas que son útiles para el comparador."""
    # Solo VIGENTE o NO-VIGENTE recientes (no canceladas)
    estatus = out_row.get("ESTATUS", "")
    if estatus not in ("VIGENTE", "NO-VIGENTE"):
        return False
    
    # Debe tener operador y nombre
    if not out_row.get("OPERADOR_NOMBRE") or not out_row.get("NOMBRE_TARIFA"):
        return False
    
    # Score mínimo
    if out_row.get("SCORE_COMPLETITUD", 0) < umbral_score:
        return False
    
    return True


def main():
    print(f"Procesando: {INPUT_FILE}")
    print(f"Salida:     {OUTPUT_FILE}")
    
    total = 0
    aceptadas = 0
    vigentes = 0
    
    with open(INPUT_FILE, "r", encoding="utf-8-sig", errors="replace") as f_in, \
         open(OUTPUT_FILE, "w", encoding="utf-8-sig", newline="") as f_out:
        
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=OUTPUT_COLS, extrasaction="ignore")
        writer.writeheader()
        
        for row in reader:
            total += 1
            if total % 10000 == 0:
                print(f"  Procesadas {total:,} filas, aceptadas {aceptadas:,}...")
            
            out = procesar_fila(row)
            
            if es_fila_util(out, umbral_score=30):
                writer.writerow(out)
                aceptadas += 1
                if out["ESTATUS"] == "VIGENTE":
                    vigentes += 1
    
    print(f"\n✅ Completado:")
    print(f"   Total filas procesadas:  {total:,}")
    print(f"   Filas aceptadas:         {aceptadas:,}")
    print(f"   Filas VIGENTES:          {vigentes:,}")
    print(f"   Archivo generado:        {OUTPUT_FILE}")
    print(f"   Tamaño aproximado:       {os.path.getsize(OUTPUT_FILE) / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
