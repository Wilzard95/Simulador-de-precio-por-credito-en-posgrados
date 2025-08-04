import pandas as pd
from unidecode import unidecode


def normaliza(texto):
    """Normaliza los nombres de programas quitando espacios, tildes y
    dejando todo en mayúsculas."""
    if pd.isnull(texto):
        return ""
    texto = unidecode(str(texto).upper())
    return texto.replace(" ", "")


# Cargar los programas del CSV
programas_csv = pd.read_csv(r"C:\Users\Nitro\Downloads\AAAAAAAA\Sube_baja.csv")
programas_csv["PROGRAMA_NORM"] = programas_csv["PROGRAMA"].apply(normaliza)
nombres_csv = programas_csv["PROGRAMA_NORM"].unique()


# Cargar el Excel grande
df = pd.read_excel(r"C:\Users\Nitro\Downloads\AAAAAAAA\SNIES-POSGRADO-UPTC.xlsx", engine="openpyxl")
df["PROGRAMA_NORM"] = df["PROGRAMA ACADÉMICO"].apply(normaliza)


# Filtrar por institución UPTC
df = df[df["INSTITUCIÓN DE EDUCACIÓN SUPERIOR (IES)"].str.upper().str.contains("UPTC")]


# Filtrar solo programas de posgrado
df = df[df["ID NIVEL ACADÉMICO"].astype(str).str.contains("2")]


# Filtrar por los años 2022 y 2023
df = df[df["AÑO"].between(2022, 2023)]


# Sumar estudiantes masculinos y femeninos
df["MATRICULADOS"] = df[["MASCULINO", "FEMENINO"]].fillna(0).sum(axis=1)


# Filtrar solo los programas que están en ambos archivos
df_filtrado = df[df["PROGRAMA_NORM"].isin(nombres_csv)]


# Agrupar y sumar estudiantes por programa, modalidad, nivel y año
resumen = (
    df_filtrado
    .groupby(["PROGRAMA ACADÉMICO", "MODALIDAD", "NIVEL DE FORMACIÓN", "AÑO"], as_index=False)["MATRICULADOS"]
    .sum()
    .rename(
        columns={
            "PROGRAMA ACADÉMICO": "Programa",
            "MODALIDAD": "modalidad",
            "NIVEL DE FORMACIÓN": "nivel de formacion",
            "AÑO": "anio",
            "MATRICULADOS": "Estudiantes",
        }
    )
)


# Guardar a Excel
resumen.to_excel(r"C:\Users\Nitro\Downloads\AAAAAAAA\estudiantes.xlsx", index=False)


print("Archivo 'estudiantes.xlsx' generado con éxito.")

