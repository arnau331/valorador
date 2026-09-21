"""
valoracion.py
-------------
Multiplos, retorno esperado, descuento de flujos de caja (DCF) y margen
de seguridad.

'supuestos' es el diccionario de la barra lateral: tasa_libre_riesgo,
coste_oportunidad, crecimiento_esperado, multiplo_salida y horizonte.
"""

import pandas as pd

import metricas
from datos import DatosEmpresa


def per_actual(empresa: DatosEmpresa) -> float | None:
    """PER = Precio / BPA, con el BPA del ultimo ejercicio."""
    bpa_actual = metricas.bpa(empresa)[-1]
    if bpa_actual <= 0:
        return None
    return empresa.precio / bpa_actual


def earnings_yield(empresa: DatosEmpresa) -> float | None:
    """Inversa del PER."""
    per = per_actual(empresa)
    return (1 / per) if per else None


def fcf_yield(empresa: DatosEmpresa, restar_sbc: bool = True) -> float | None:
    """FCF Yield = (FCF/Accion) / Precio."""
    if empresa.precio <= 0:
        return None
    fcf_share = metricas.fcf_por_accion(empresa, restar_sbc)[-1]
    return fcf_share / empresa.precio


def dividend_yield(empresa: DatosEmpresa) -> float:
    if empresa.precio <= 0:
        return 0.0
    return empresa.dividendo_por_accion / empresa.precio


def multiplos_actuales(empresa: DatosEmpresa, supuestos: dict, restar_sbc: bool = True) -> dict:
    """PER, Earnings Yield, FCF Yield y Dividend Yield de hoy, junto a la tasa libre de riesgo."""
    return {
        "per": per_actual(empresa),
        "earnings_yield": earnings_yield(empresa),
        "fcf_yield": fcf_yield(empresa, restar_sbc),
        "dividend_yield": dividend_yield(empresa),
        "tasa_libre_riesgo": supuestos["tasa_libre_riesgo"],
    }


def retorno_esperado(empresa: DatosEmpresa, supuestos: dict) -> dict:
    """
    Retorno esperado = crecimiento del BPA + dividendos +/- variacion del
    multiplo. Proyecta el BPA al crecimiento asumido, aplica el multiplo
    de salida para obtener el precio final, y separa el CAGR de precio
    resultante en la parte que viene del crecimiento y la que viene del
    cambio de multiplo.
    """
    g = supuestos["crecimiento_esperado"]
    n = int(supuestos["horizonte"])
    multiplo_final = supuestos["multiplo_salida"]

    bpa_actual = metricas.bpa(empresa)[-1]
    if bpa_actual <= 0:
        return {"error": "El BPA del ultimo ejercicio es negativo o nulo."}

    multiplo_actual = per_actual(empresa)
    bpa_final = bpa_actual * (1 + g) ** n
    precio_final = bpa_final * multiplo_final

    cagr_precio = (precio_final / empresa.precio) ** (1 / n) - 1
    cagr_multiplo = (multiplo_final / multiplo_actual) ** (1 / n) - 1
    div_yield = dividend_yield(empresa)

    return {
        "bpa_actual": bpa_actual,
        "bpa_final": bpa_final,
        "multiplo_actual": multiplo_actual,
        "multiplo_final": multiplo_final,
        "precio_actual": empresa.precio,
        "precio_final": precio_final,
        "crecimiento_bpa": g,
        "variacion_multiplo": cagr_multiplo,
        "dividend_yield": div_yield,
        "cagr_precio": cagr_precio,
        "retorno_esperado": cagr_precio + div_yield,
    }


def dcf_valor_intrinseco(
    empresa: DatosEmpresa, supuestos: dict, restar_sbc: bool = True
) -> dict:
    """
    Valor intrinseco por descuento de flujos de caja (FCF por accion).

    El valor terminal no usa una perpetuidad de Gordon (que exige que el
    coste de oportunidad supere al crecimiento): aplica el multiplo de
    salida al BPA final, igual que en retorno_esperado, para que ambos
    metodos compartan los mismos supuestos.
    """
    r = supuestos["coste_oportunidad"]
    g = supuestos["crecimiento_esperado"]
    n = int(supuestos["horizonte"])
    multiplo_final = supuestos["multiplo_salida"]

    bpa_actual = metricas.bpa(empresa)[-1]
    if bpa_actual <= 0:
        return {"error": "El BPA del ultimo ejercicio es negativo o nulo; el DCF no es fiable."}

    fcf_share_actual = metricas.fcf_por_accion(empresa, restar_sbc)[-1]

    flujos = []
    valor_presente_flujos = 0.0
    for anio in range(1, n + 1):
        fcf_anio = fcf_share_actual * (1 + g) ** anio
        valor_presente = fcf_anio / (1 + r) ** anio
        flujos.append({
            "anio": anio,
            "fcf_por_accion": fcf_anio,
            "valor_presente": valor_presente,
        })
        valor_presente_flujos += valor_presente

    bpa_final = bpa_actual * (1 + g) ** n
    valor_terminal = bpa_final * multiplo_final
    valor_presente_terminal = valor_terminal / (1 + r) ** n

    return {
        "flujos": flujos,
        "valor_presente_flujos": valor_presente_flujos,
        "bpa_final": bpa_final,
        "valor_terminal": valor_terminal,
        "valor_presente_terminal": valor_presente_terminal,
        "valor_intrinseco": valor_presente_flujos + valor_presente_terminal,
    }


def tabla_flujos_dcf(resultado_dcf: dict) -> pd.DataFrame:
    """Convierte el detalle de dcf_valor_intrinseco en una tabla para mostrar."""
    tabla = pd.DataFrame(resultado_dcf["flujos"]).set_index("anio")
    tabla.columns = ["FCF por accion", "Valor presente"]
    return tabla


def valor_intrinseco_por_multiplo(empresa: DatosEmpresa, supuestos: dict) -> dict:
    """
    Metodo alternativo al DCF, sin flujos intermedios: el precio que
    habria que pagar hoy para que, vendiendo al multiplo de salida al
    final del horizonte, el retorno obtenido sea el coste de oportunidad.
    """
    r = supuestos["coste_oportunidad"]
    g = supuestos["crecimiento_esperado"]
    n = int(supuestos["horizonte"])
    multiplo_final = supuestos["multiplo_salida"]

    bpa_actual = metricas.bpa(empresa)[-1]
    if bpa_actual <= 0:
        return {"error": "El BPA del ultimo ejercicio es negativo o nulo."}

    bpa_final = bpa_actual * (1 + g) ** n
    precio_objetivo = bpa_final * multiplo_final
    valor_intrinseco = precio_objetivo / (1 + r) ** n

    return {
        "bpa_final": bpa_final,
        "precio_objetivo": precio_objetivo,
        "valor_intrinseco": valor_intrinseco,
    }


def margen_seguridad(precio: float, valor_intrinseco: float | None) -> float | None:
    """MoS = 1 - Precio/Valor. Positivo: precio por debajo del valor intrinseco."""
    if valor_intrinseco is None or valor_intrinseco <= 0:
        return None
    return 1 - precio / valor_intrinseco


def resumen_valoracion(
    empresa: DatosEmpresa, supuestos: dict, restar_sbc: bool = True
) -> dict:
    """Agrupa DCF y metodo de multiplos junto a su margen de seguridad."""
    dcf = dcf_valor_intrinseco(empresa, supuestos, restar_sbc)
    multiplo = valor_intrinseco_por_multiplo(empresa, supuestos)

    resultado = {"dcf": dcf, "multiplo": multiplo}
    if "valor_intrinseco" in dcf:
        resultado["mos_dcf"] = margen_seguridad(empresa.precio, dcf["valor_intrinseco"])
    if "valor_intrinseco" in multiplo:
        resultado["mos_multiplo"] = margen_seguridad(empresa.precio, multiplo["valor_intrinseco"])
    return resultado
