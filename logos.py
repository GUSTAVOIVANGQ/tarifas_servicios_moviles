import pandas as pd
import requests
from io import BytesIO
import matplotlib.pyplot as plt
from PIL import Image

# 1. Leer el archivo CSV
df = pd.read_csv("tarifas_moviles_normalizado.csv")

# 2. Extraer los nombres únicos de la columna de operadores
operadores_unicos = df['OPERADOR_NOMBRE'].dropna().unique()

# 3. Diccionario con dominios para los operadores conocidos en tu CSV
dominios_conocidos = {
    "TELCEL": "telcel.com",
    "MOVISTAR": "movistar.com.mx",
    "AT&T": "att.com.mx",
    "VIRGIN MOBILE": "virginmobile.mx"
}

# Filtrar para mostrar solo los operadores que coincidan
operadores_a_mostrar = [op for op in operadores_unicos if op in dominios_conocidos]

# 4. Crear la gráfica para mostrar los logos
fig, axes = plt.subplots(1, len(operadores_a_mostrar), figsize=(12, 3))

if len(operadores_a_mostrar) == 1:
    axes = [axes] # Evitar errores si solo hay 1 operador

for ax, nombre in zip(axes, operadores_a_mostrar):
    dominio = dominios_conocidos[nombre]
    url = f"https://logo.clearbit.com/{dominio}"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        ax.imshow(img)
    except Exception:
        ax.text(0.5, 0.5, "No encontrado", ha='center', va='center')
    
    ax.set_title(nombre, fontsize=10, fontweight='bold')
    ax.axis('off')

plt.suptitle("Logos de Operadores (Datos de CSV)", fontsize=14)
plt.tight_layout()
plt.show()