import pandas as pd
from pathlib import Path
from unidecode import unidecode


# Directorio donde residen los archivos de entrada y salida
BASE_DIR = Path(r"C:\Users\Nitro\Downloads\AAAAAAAA")


def normaliza(texto):
    """Normaliza los nombres de programas quitando espacios, tildes y
    dejando todo en mayúsculas."""
    if pd.isnull(texto):
        return ""
    texto = unidecode(str(texto).upper())
    return texto.replace(" ", "")


def buscar_columna(df, objetivo):
    """Encuentra la columna que contiene el texto indicado
    ignorando mayúsculas, tildes y espacios."""
    objetivo_norm = normaliza(objetivo)
    for columna in df.columns:
        if objetivo_norm in normaliza(columna):
            return columna
    raise KeyError(f"No se encontró una columna que contenga '{objetivo}'.")


# Cargar los programas del CSV
programas_csv = pd.read_csv(BASE_DIR / "Sube_baja.csv")
programas_csv["PROGRAMA_NORM"] = programas_csv["PROGRAMA"].apply(normaliza)
nombres_csv = programas_csv["PROGRAMA_NORM"].unique()


# Cargar el Excel grande filtrado de la UPTC
df = pd.read_excel(BASE_DIR / "SNIES-POSGRADO-UPTC.xlsx", engine="openpyxl")
df["PROGRAMA_NORM"] = df["PROGRAMA ACADÉMICO"].apply(normaliza)


# Filtrar solo programas de posgrado
df = df[df["ID NIVEL ACADÉMICO"].astype(str).str.contains("2")]


# Filtrar por los años 2022 y 2023
df = df[df["AÑO"].between(2022, 2023)]


# Sumar estudiantes masculinos y femeninos, buscando las columnas de forma flexible
col_masc = buscar_columna(df, "MASCULINO")
col_fem = buscar_columna(df, "FEMENINO")
df["MATRICULADOS"] = df[[col_masc, col_fem]].fillna(0).sum(axis=1)


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


# Guardar a Excel en el mismo directorio
salida = BASE_DIR / "estudiantes.xlsx"
resumen.to_excel(salida, index=False)


print(f"Archivo '{salida.name}' generado con éxito.")
