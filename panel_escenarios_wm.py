import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="Modelo financiero — Escenarios", layout="wide")
st.title("Modelo financiero — Escenarios")

# =========================
#  CARGA DE DATOS
# =========================
st.sidebar.header("Carga de datos")
src = st.sidebar.radio("Fuente", ["Ruta local", "Subir CSV"])

def load_csv_semicolon(path_or_buf):
    """Primero intenta ; fijo. Si falla, intenta autodetección."""
    try:
        return pd.read_csv(path_or_buf, sep=";", engine="python")
    except Exception:
        pass
    return pd.read_csv(path_or_buf, sep=None, engine="python")

if src == "Ruta local":
    path = st.sidebar.text_input("Ruta CSV (;)", "")
    path = path.strip().strip('"')
    if not path:
        st.info("Ingresa la ruta del CSV para continuar…")
        st.stop()
    if not os.path.exists(path):
        st.error("No encuentro el archivo en esa ruta. Verifica la ruta exacta.")
        st.stop()
    try:
        df = load_csv_semicolon(path)
    except Exception as e:
        st.error(f"No pude leer el CSV: {e}")
        st.stop()
else:
    file = st.sidebar.file_uploader("Sube CSV (;)", type=["csv"])
    if file is None:
        st.info("Sube un CSV para continuar…")
        st.stop()
    try:
        df = load_csv_semicolon(file)
    except Exception as e:
        st.error(f"No pude leer el CSV subido: {e}")
        st.stop()

with st.expander("Columnas detectadas"):
    st.write(list(df.columns))

# =========================
#  MAPEO EXPLÍCITO
# =========================
st.sidebar.header("Mapeo de columnas (elige exactamente tus columnas)")

def select_col(lbl, hints, exclude=None):
    # Sugerir primero por 'hints', si no hay coincidencias, mostrar todas
    candidates = [c for c in df.columns if any(h.lower() in c.lower() for h in hints)]
    if not candidates:
        candidates = list(df.columns)
    # Excluir columnas no válidas para evitar mapeos accidentales
    if exclude:
        candidates = [c for c in candidates if c not in set(exclude)]
    return st.sidebar.selectbox(lbl, candidates)

# Primero elegimos la columna de estudiantes para poder excluirla del resto
col_num_est = select_col("N° EST (conteo de estudiantes)",
                         ["n° est","n est","n-est","n_est","estudiante","estudiantes","numero","número"])

col_programa    = select_col("Programa", ["programa"], exclude=[col_num_est])
col_nivel       = select_col("Nivel", ["nivel","formación","formacion"], exclude=[col_num_est])
col_modalidad   = select_col("Modalidad", ["modalidad"], exclude=[col_num_est])

# Ponderadores 0–1 del programa (NUNCA deben ser N-EST)
excluir_ponderadores = [col_num_est]
col_est         = select_col("Est (ponderador 0–1)", ["est"], exclude=excluir_ponderadores)
col_planta      = select_col("Planta (ponderador 0–1)", ["planta"], exclude=excluir_ponderadores)
col_comp        = select_col("Comp (ponderador 0–1)", ["comp"], exclude=excluir_ponderadores)
col_tipo        = select_col("Tipo (ponderador 0–1)", ["tipo"], exclude=excluir_ponderadores)
col_promcred    = select_col("PromdeCreditos", ["prom"], exclude=[col_num_est])
col_matricula   = select_col("MATRÍCULA", ["matr","matríc","matricu"], exclude=[col_num_est])
col_matr_actual = select_col(
    "MATR.ACTUAL (MATRÍCULA * salario mínimo)",
    ["matr","actual","matrícula","matricula"],
    exclude=[col_num_est, col_matricula],
)
col_valor_cred  = select_col(
    "Valor crédito",
    ["valor", "crédito", "credito"],
    exclude=[col_num_est, col_promcred, col_matr_actual, col_matricula],
)

# Validación final
required = [
    col_programa, col_nivel, col_modalidad, col_est, col_planta, col_comp,
    col_tipo, col_promcred, col_matricula, col_matr_actual, col_valor_cred,
    col_num_est,
]
if any(c is None for c in required):
    st.error("Faltan columnas requeridas (elige todas en el mapeo del panel lateral).")
    st.stop()

finance_cols = [col_promcred, col_matricula, col_matr_actual, col_valor_cred]
if col_num_est in finance_cols or col_est == col_num_est or col_planta == col_num_est or col_comp == col_num_est or col_tipo == col_num_est:
    st.error(f"Revisa el mapeo: ninguna columna financiera ni ponderador puede ser '{col_num_est}'.")
    st.stop()

with st.expander("Mapeo actual"):
    st.write({
        "Programa": col_programa,
        "Nivel": col_nivel,
        "Modalidad": col_modalidad,
        "Est": col_est,
        "Planta": col_planta,
        "Comp": col_comp,
        "Tipo": col_tipo,
        "PromdeCreditos": col_promcred,
        "MATRÍCULA": col_matricula,
        "MATR.ACTUAL": col_matr_actual,
        "Valor crédito": col_valor_cred,
        "N-EST": col_num_est,
    })
 
# =========================
#  PARÁMETROS DEL MODELO
# =========================

# =========================
#  PARSEO NUMÉRICO ROBUSTO
# =========================
def to_number_series(series):
    s = series.astype(str).str.replace(r"[^\d,.\-]", "", regex=True).str.strip()

    # Caso 1: tiene punto y coma -> "." miles, "," decimales (1.234.567,89)
    both = s.str.contains(",") & s.str.contains(r"\.")
    s[both] = s[both].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)

    # Caso 2: solo puntos -> probablemente miles (1.234.567)
    only_dot = s.str.contains(r"\.") & ~s.str.contains(",")
    pat_thousand_dot = s.str.match(r"^\d{1,3}(\.\d{3})+$")
    s[only_dot & pat_thousand_dot] = s[only_dot & pat_thousand_dot].str.replace(".", "", regex=False)

    # Caso 3: solo comas -> o miles (1,234,567) o decimales (123,45)
    only_com = s.str.contains(",") & ~s.str.contains(r"\.")
    pat_thousand_com = s.str.match(r"^\d{1,3}(,\d{3})+$")
    s[only_com & pat_thousand_com] = s[only_com & pat_thousand_com].str.replace(",", "", regex=False)   # miles
    s[only_com & ~pat_thousand_com] = s[only_com & ~pat_thousand_com].str.replace(",", ".", regex=False) # decimal

    return pd.to_numeric(s, errors="coerce")

# =========================
#  CÁLCULO (SIN TOCAR TU CSV)
# =========================
df_calc = df.copy()

Est     = to_number_series(df_calc[col_est]).fillna(0)
Planta  = to_number_series(df_calc[col_planta]).fillna(0)
Comp    = to_number_series(df_calc[col_comp]).fillna(0)
Tipo    = to_number_series(df_calc[col_tipo]).fillna(0)
PromCr  = to_number_series(df_calc[col_promcred]).fillna(0)
MatrBase = to_number_series(df_calc[col_matricula]).fillna(0)
MatrAct  = to_number_series(df_calc[col_matr_actual]).fillna(0)
ValorCredBase = to_number_series(df_calc[col_valor_cred]).fillna(0)
NEst     = to_number_series(df_calc[col_num_est]).fillna(0)

df_calc["valor_nuevo_credito"] = ValorCredBase * (0.35*Est + 0.35*Planta + 0.2*Comp + 0.1*Tipo)
df_calc["MATR.NUEVA_CALC"] = df_calc["valor_nuevo_credito"] * PromCr
df_calc["Recaudo_actual"] = NEst * MatrAct
df_calc["Recaudo_nuevo"] = df_calc["MATR.NUEVA_CALC"] * NEst
df_calc["Delta_recaudo"] = df_calc["Recaudo_nuevo"] - df_calc["Recaudo_actual"]
df_calc["Delta_recaudo_%"] = np.where(df_calc["Recaudo_actual"] == 0, 0, df_calc["Delta_recaudo"] / df_calc["Recaudo_actual"])

# =========================
#  MÉTRICAS Y VISTAS
# =========================
c1, c2, c3, c4 = st.columns(4)
c1.metric("Recaudo actual", f"{df_calc['Recaudo_actual'].sum():,.0f}")
c2.metric("Recaudo nuevo",  f"{df_calc['Recaudo_nuevo'].sum():,.0f}")
delta_abs = df_calc["Delta_recaudo"].sum()
base_sum  = df_calc["Recaudo_actual"].sum()
delta_pct = 0 if base_sum == 0 else delta_abs / base_sum
c3.metric("Δ Recaudo (COP)", f"{delta_abs:,.0f}")
c4.metric("Δ Recaudo (%)",   f"{delta_pct*100:,.2f}%")

# Auditoría rápida para verificar fórmulas fila a fila
with st.expander("Control rápido (5 filas): N-EST * MATR.ACTUAL y MATR.NUEVA_CALC"):
    tmp = df_calc[[col_programa, col_num_est, col_matr_actual, "MATR.NUEVA_CALC"]].head(5).copy()
    tmp["calc_actual"] = to_number_series(tmp[col_num_est]) * to_number_series(tmp[col_matr_actual])
    tmp["calc_nuevo"]  = to_number_series(tmp[col_num_est]) * tmp["MATR.NUEVA_CALC"]
    st.dataframe(tmp)

with st.expander("Detalle de cálculo del nuevo valor"):
    st.dataframe(df_calc[[
        col_programa, col_nivel, "valor_nuevo_credito", "MATR.NUEVA_CALC", "Recaudo_nuevo"
    ]])

st.subheader("Resumen por nivel")
by_level = df_calc.groupby(df_calc[col_nivel]).agg(
    rec_actual=("Recaudo_actual", "sum"),
    rec_nuevo =("Recaudo_nuevo",  "sum"),
).reset_index()
by_level["delta"]   = by_level["rec_nuevo"] - by_level["rec_actual"]
by_level["delta_%"] = np.where(by_level["rec_actual"] == 0, 0, by_level["delta"] / by_level["rec_actual"])
st.dataframe(by_level, use_container_width=True)
st.bar_chart(by_level.set_index(col_nivel)[["rec_actual", "rec_nuevo"]])

st.subheader("Programas: Top ± impacto (Δ Recaudo)")
df_sorted = df_calc[[col_programa, col_nivel, "Recaudo_actual", "Recaudo_nuevo", "Delta_recaudo", "Delta_recaudo_%"]]\
    .sort_values("Delta_recaudo", ascending=False)
st.dataframe(df_sorted.head(20), use_container_width=True)
st.dataframe(df_sorted.tail(20).sort_values("Delta_recaudo", ascending=True), use_container_width=True)
top_prog = df_sorted.head(10)[[col_programa, "Recaudo_actual", "Recaudo_nuevo"]].set_index(col_programa)
st.bar_chart(top_prog)

# =========================
#  DESCARGA CSV CON ';'
# =========================
st.subheader("Descargar resultados")
st.download_button(
    "CSV (;) – escenario_resultados_puntoycoma.csv",
    df_calc.to_csv(sep=";", index=False).encode("utf-8-sig"),
    file_name="escenario_resultados_puntoycoma.csv",
    mime="text/csv"
)
