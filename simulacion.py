"""
simulacion.py
-------------
Analisis de sensibilidad y simulacion de Monte Carlo sobre el valor
intrinseco (DCF) o el retorno esperado, para ver cuanto dependen de los
supuestos de crecimiento, coste de oportunidad y multiplo de salida.
"""

import numpy as np
import pandas as pd

import valoracion
from datos import DatosEmpresa


VARIABLES = {
    "crecimiento_esperado": {"etiqueta": "Crecimiento BPA", "paso": 0.03, "formato": "pct"},
    "coste_oportunidad": {"etiqueta": "Coste de oportunidad", "paso": 0.02, "formato": "pct"},
    "multiplo_salida": {"etiqueta": "Multiplo de salida", "paso": 3.0, "formato": "mult"},
    "horizonte": {"etiqueta": "Horizonte", "paso": 2, "formato": "anios"},
}

OBJETIVOS = {
    "valor_intrinseco": "Valor intrinseco (DCF)",
    "retorno_esperado": "Retorno esperado",
}


def _formatear(variable: str, valor: float) -> str:
    formato = VARIABLES[variable]["formato"]
    if formato == "pct":
        return f"{valor:.1%}"
    if formato == "mult":
        return f"{valor:.0f}x"
    return f"{int(valor)} anios"


def rango_alrededor(variable: str, valor_central: float, n: int = 5) -> list[float]:
    """n valores centrados en valor_central, espaciados por el paso de la variable."""
    paso = VARIABLES[variable]["paso"]
    mitad = n // 2
    valores = [valor_central + (i - mitad) * paso for i in range(n)]
    if variable == "multiplo_salida":
        valores = [max(v, 1.0) for v in valores]
    if variable == "horizonte":
        valores = [max(int(round(v)), 1) for v in valores]
    return valores


def _evaluar(
    empresa: DatosEmpresa, supuestos: dict, objetivo: str, restar_sbc: bool
) -> float | None:
    if objetivo == "valor_intrinseco":
        resultado = valoracion.dcf_valor_intrinseco(empresa, supuestos, restar_sbc)
    else:
        resultado = valoracion.retorno_esperado(empresa, supuestos)
    return resultado.get(objetivo)


def tabla_sensibilidad(
    empresa: DatosEmpresa,
    supuestos: dict,
    eje_filas: str = "crecimiento_esperado",
    eje_columnas: str = "multiplo_salida",
    valores_filas: list[float] | None = None,
    valores_columnas: list[float] | None = None,
    objetivo: str = "valor_intrinseco",
    restar_sbc: bool = True,
) -> pd.DataFrame:
    """Cruza dos supuestos y muestra el valor intrinseco o el retorno esperado resultante."""
    if eje_filas == eje_columnas:
        raise ValueError("Las dos variables de la tabla deben ser distintas.")

    if valores_filas is None:
        valores_filas = rango_alrededor(eje_filas, supuestos[eje_filas])
    if valores_columnas is None:
        valores_columnas = rango_alrededor(eje_columnas, supuestos[eje_columnas])

    filas = {}
    for vf in valores_filas:
        fila = {}
        for vc in valores_columnas:
            supuestos_mod = dict(supuestos)
            supuestos_mod[eje_filas] = vf
            supuestos_mod[eje_columnas] = vc
            fila[_formatear(eje_columnas, vc)] = _evaluar(
                empresa, supuestos_mod, objetivo, restar_sbc
            )
        filas[_formatear(eje_filas, vf)] = fila

    tabla = pd.DataFrame(filas).T
    tabla.index.name = VARIABLES[eje_filas]["etiqueta"]
    tabla.columns.name = VARIABLES[eje_columnas]["etiqueta"]
    return tabla


def monte_carlo(
    empresa: DatosEmpresa,
    supuestos: dict,
    n_simulaciones: int = 5000,
    desviacion_crecimiento: float = 0.05,
    desviacion_multiplo: float = 4.0,
    desviacion_coste_oportunidad: float = 0.01,
    objetivo: str = "valor_intrinseco",
    restar_sbc: bool = True,
    semilla: int | None = 42,
) -> pd.DataFrame:
    """
    Simula 'n_simulaciones' escenarios muestreando crecimiento, multiplo de
    salida y coste de oportunidad de normales centradas en los supuestos.
    El multiplo se trunca a un minimo de 1x y el coste de oportunidad a un
    minimo de 1 punto por encima del crecimiento simulado, para evitar
    combinaciones sin sentido economico.
    """
    rng = np.random.default_rng(semilla)

    crecimientos = rng.normal(
        supuestos["crecimiento_esperado"], desviacion_crecimiento, n_simulaciones
    )
    multiplos = np.clip(
        rng.normal(supuestos["multiplo_salida"], desviacion_multiplo, n_simulaciones),
        1.0, None,
    )
    costes = rng.normal(
        supuestos["coste_oportunidad"], desviacion_coste_oportunidad, n_simulaciones
    )
    costes = np.maximum(costes, crecimientos + 0.01)

    resultados = np.full(n_simulaciones, np.nan)
    for i in range(n_simulaciones):
        supuestos_mod = dict(supuestos)
        supuestos_mod["crecimiento_esperado"] = crecimientos[i]
        supuestos_mod["multiplo_salida"] = multiplos[i]
        supuestos_mod["coste_oportunidad"] = costes[i]
        valor = _evaluar(empresa, supuestos_mod, objetivo, restar_sbc)
        if valor is not None:
            resultados[i] = valor

    return pd.DataFrame({
        "crecimiento_esperado": crecimientos,
        "multiplo_salida": multiplos,
        "coste_oportunidad": costes,
        "resultado": resultados,
    })


def resumen_monte_carlo(
    resultados: pd.DataFrame, precio_actual: float | None = None
) -> dict:
    """Percentiles de la distribucion y, si se da el precio, probabilidad de infravaloracion."""
    serie = resultados["resultado"].dropna()
    if serie.empty:
        return {"error": "Ninguna simulacion produjo un resultado valido."}

    resumen = {
        "p10": serie.quantile(0.10),
        "p25": serie.quantile(0.25),
        "mediana": serie.quantile(0.50),
        "p75": serie.quantile(0.75),
        "p90": serie.quantile(0.90),
        "media": serie.mean(),
        "desviacion": serie.std(),
        "n_validas": len(serie),
        "n_total": len(resultados),
    }
    if precio_actual is not None and precio_actual > 0:
        resumen["prob_infravalorada"] = (serie > precio_actual).mean()

    return resumen


def histograma(resultados: pd.DataFrame, bins: int = 40) -> pd.Series:
    """Cuenta de simulaciones por intervalo de resultado, lista para un bar_chart."""
    serie = resultados["resultado"].dropna()
    conteo, bordes = np.histogram(serie, bins=bins)
    centros = (bordes[:-1] + bordes[1:]) / 2
    return pd.Series(conteo, index=pd.Index(centros, name="resultado"))
