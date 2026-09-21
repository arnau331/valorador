"""
metricas.py
-----------
Diagnostico de calidad del negocio: margenes, crecimiento, generacion de
caja y solidez financiera.

Funciones puras: reciben un DatosEmpresa y devuelven listas o escalares,
sin depender de Streamlit.
"""

import pandas as pd

from datos import DatosEmpresa


def cagr(inicial: float, final: float, anios: int) -> float | None:
    """Tasa de crecimiento anual compuesta: (final/inicial)**(1/anios) - 1."""
    if anios <= 0 or inicial <= 0 or final <= 0:
        return None
    return (final / inicial) ** (1 / anios) - 1


def cagr_serie(serie: list[float]) -> float | None:
    """CAGR del primer al ultimo valor de una serie."""
    if len(serie) < 2:
        return None
    return cagr(serie[0], serie[-1], len(serie) - 1)


def ebitda(empresa: DatosEmpresa) -> list[float]:
    """EBITDA = EBIT + depreciacion y amortizacion."""
    return [e + d for e, d in zip(empresa.ebit, empresa.dya)]


def free_cash_flow(empresa: DatosEmpresa, restar_sbc: bool = True) -> list[float]:
    """
    FCF = flujo de caja operativo - CapEx (- SBC, opcionalmente).

    El estado de flujos de caja no resta la retribucion en acciones (SBC)
    porque no es una salida de caja, pero es un gasto real de personal que
    diluye al accionista. Se deja como opcion para comparar ambos criterios.
    """
    fcf = [o - c for o, c in zip(empresa.ocf, empresa.capex)]
    if restar_sbc:
        fcf = [f - s for f, s in zip(fcf, empresa.sbc)]
    return fcf


def bpa(empresa: DatosEmpresa) -> list[float]:
    """Beneficio por accion = beneficio neto / acciones diluidas."""
    return [b / a for b, a in zip(empresa.beneficio_neto, empresa.acciones)]


def fcf_por_accion(empresa: DatosEmpresa, restar_sbc: bool = True) -> list[float]:
    return [f / a for f, a in zip(free_cash_flow(empresa, restar_sbc), empresa.acciones)]


def margenes(empresa: DatosEmpresa, restar_sbc: bool = True) -> dict[str, list[float]]:
    """Margen bruto, EBIT, neto, EBITDA y FCF, ejercicio a ejercicio."""
    ing = empresa.ingresos
    return {
        "Margen bruto": [b / i for b, i in zip(empresa.beneficio_bruto, ing)],
        "Margen EBIT": [e / i for e, i in zip(empresa.ebit, ing)],
        "Margen neto": [b / i for b, i in zip(empresa.beneficio_neto, ing)],
        "Margen EBITDA": [e / i for e, i in zip(ebitda(empresa), ing)],
        "Margen FCF": [f / i for f, i in zip(free_cash_flow(empresa, restar_sbc), ing)],
    }


def conversion_caja(empresa: DatosEmpresa, restar_sbc: bool = True) -> list[float | None]:
    """FCF Conversion = FCF / beneficio neto: que parte del beneficio contable se hace caja."""
    return [
        (f / b) if b > 0 else None
        for f, b in zip(free_cash_flow(empresa, restar_sbc), empresa.beneficio_neto)
    ]


def deuda_neta(empresa: DatosEmpresa) -> float:
    """Deuda neta = deuda total - caja e inversiones. Negativa = caja neta."""
    deuda_total = empresa.deuda_largo_plazo + empresa.deuda_corriente
    return deuda_total - empresa.caja_e_inversiones


def net_debt_ebitda(empresa: DatosEmpresa) -> float | None:
    ebitda_actual = ebitda(empresa)[-1]
    if ebitda_actual <= 0:
        return None
    return deuda_neta(empresa) / ebitda_actual


def tipo_interes_deuda(empresa: DatosEmpresa) -> float | None:
    deuda_total = empresa.deuda_largo_plazo + empresa.deuda_corriente
    if deuda_total <= 0:
        return None
    return empresa.gasto_intereses / deuda_total


def working_capital(empresa: DatosEmpresa) -> float:
    """Fondo de maniobra = activos corrientes - pasivos corrientes."""
    return empresa.activos_corrientes - empresa.pasivos_corrientes


def tabla_evolucion(empresa: DatosEmpresa, restar_sbc: bool = True) -> pd.DataFrame:
    """Magnitudes absolutas por ejercicio, en millones."""
    filas = {
        "Ingresos": empresa.ingresos,
        "Beneficio bruto": empresa.beneficio_bruto,
        "EBIT": empresa.ebit,
        "EBITDA": ebitda(empresa),
        "Beneficio neto": empresa.beneficio_neto,
        "FCF": free_cash_flow(empresa, restar_sbc),
        "Acciones (millones)": empresa.acciones,
    }
    tabla = pd.DataFrame(filas, index=empresa.anios).T
    tabla.columns = [str(a) for a in empresa.anios]
    return tabla


def tabla_margenes(empresa: DatosEmpresa, restar_sbc: bool = True) -> pd.DataFrame:
    tabla = pd.DataFrame(margenes(empresa, restar_sbc), index=empresa.anios).T
    tabla.columns = [str(a) for a in empresa.anios]
    return tabla


def tabla_crecimiento(empresa: DatosEmpresa, restar_sbc: bool = True) -> pd.DataFrame:
    """CAGR de cada magnitud durante todo el periodo."""
    series = {
        "Ingresos": empresa.ingresos,
        "Beneficio bruto": empresa.beneficio_bruto,
        "EBIT": empresa.ebit,
        "Beneficio neto": empresa.beneficio_neto,
        "FCF": free_cash_flow(empresa, restar_sbc),
        "BPA": bpa(empresa),
        "FCF por accion": fcf_por_accion(empresa, restar_sbc),
        "Acciones en circulacion": empresa.acciones,
    }
    return pd.DataFrame({"CAGR": {nombre: cagr_serie(s) for nombre, s in series.items()}})


def senales(empresa: DatosEmpresa, restar_sbc: bool = True) -> list[tuple[str, bool, str]]:
    """
    Comprobaciones cualitativas de la formacion del club: (titulo, cumple,
    explicacion). No son reglas absolutas, son indicios a interpretar.
    """
    resultado = []
    crec = {
        nombre: cagr_serie(serie)
        for nombre, serie in {
            "ingresos": empresa.ingresos,
            "bruto": empresa.beneficio_bruto,
            "ebit": empresa.ebit,
            "acciones": empresa.acciones,
        }.items()
    }

    if crec["bruto"] is not None and crec["ingresos"] is not None:
        cumple = crec["bruto"] > crec["ingresos"]
        resultado.append((
            "El beneficio bruto crece mas rapido que los ingresos",
            cumple,
            "Indica expansion del margen bruto: la empresa gana eficiencia "
            "o poder de fijacion de precios.",
        ))

    if crec["ebit"] is not None and crec["ingresos"] is not None:
        cumple = crec["ebit"] > crec["ingresos"]
        resultado.append((
            "El EBIT crece mas rapido que los ingresos",
            cumple,
            "Apalancamiento operativo: los costes crecen menos que las ventas.",
        ))

    if crec["acciones"] is not None:
        cumple = crec["acciones"] < 0
        resultado.append((
            "El numero de acciones se reduce",
            cumple,
            "Recompras: el accionista posee cada anio una parte mayor del "
            "negocio. Si crece, hay dilucion.",
        ))

    conv = conversion_caja(empresa, restar_sbc)[-1]
    if conv is not None:
        cumple = conv > 0.8
        resultado.append((
            "Conversion de caja por encima del 80%",
            cumple,
            f"Actualmente {conv:.0%}. Mide cuanto del beneficio contable "
            "se convierte en caja real.",
        ))

    nde = net_debt_ebitda(empresa)
    if nde is not None:
        cumple = nde < 2.0
        resultado.append((
            "Net Debt / EBITDA por debajo de 2x",
            cumple,
            f"Actualmente {nde:.2f}x. Por encima de 3x se considera mala "
            "salud financiera; negativo significa caja neta.",
        ))

    margen_fcf = margenes(empresa, restar_sbc)["Margen FCF"]
    if len(margen_fcf) >= 2:
        cumple = margen_fcf[-1] > margen_fcf[0]
        resultado.append((
            "El margen FCF se expande en el periodo",
            cumple,
            f"De {margen_fcf[0]:.1%} a {margen_fcf[-1]:.1%}.",
        ))

    if working_capital(empresa) != 0:
        wc = working_capital(empresa)
        resultado.append((
            "Fondo de maniobra positivo",
            wc > 0,
            f"Actualmente {wc:,.0f} millones. Negativo no siempre es malo: "
            "algunas empresas de software lo tienen por modelo de negocio.",
        ))

    return resultado
