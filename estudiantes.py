import pandas as pd
from unidecode import unidecode

def normaliza(texto):
    if pd.isnull(texto):
        return ""
    return unidecode(str(texto).strip().upper())

# Cargar los 128 programas del CSV
programas_csv = pd.read_csv(r"C:\Users\Nitro\Downloads\AAAAAAAA\Sube_baja.csv")
programas_csv["PROGRAMA_NORM"] = programas_csv["PROGRAMA"].apply(normaliza)
nombres_csv = programas_csv["PROGRAMA_NORM"].unique()

# Cargar el Excel grande
df = pd.read_excel(r"C:\Users\Nitro\Downloads\AAAAAAAA\SNIES-POSGRADO.xlsx", engine="openpyxl")
df["PROGRAMA_NORM"] = df["PROGRAMA ACADÉMICO"].apply(normaliza)

# Filtrar por institución UPTC
df = df[df["INSTITUCIÓN DE EDUCACIÓN SUPERIOR (IES)"].str.upper().str.contains("UPTC")]

# Filtrar solo programas de posgrado (ajusta si es necesario)
df = df[df["ID NIVEL ACADÉMICO"].astype(str).str.contains("2")]

# Filtrar por los últimos 3 años (ajusta si es necesario)
df = df[df["AÑO"].between(2022, 2023)]

# Filtrar solo los programas que están en ambos archivos (usando la columna normalizada)
df_filtrado = df[df["PROGRAMA_NORM"].isin(nombres_csv)]

# Agrupar y sumar estudiantes por programa, modalidad y nivel
resumen = (
    df_filtrado
    .groupby(["PROGRAMA ACADÉMICO", "MODALIDAD", "NIVEL DE FORMACIÓN"], as_index=False)["MATRICULADOS"]
    .sum()
    .rename(columns={
        "PROGRAMA ACADÉMICO": "Programa",
        "MODALIDAD": "modalidad",
        "NIVEL DE FORMACIÓN": "nivel de formacion",
        "MATRICULADOS": "Estudiantes"
    })
)

# Guardar a Excel
resumen.to_excel(r"C:\Users\Nitro\Downloads\AAAAAAAA\estudiantes.xlsx", index=False)

print("Archivo 'estudiantes.xlsx' generado con éxito.")