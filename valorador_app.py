"""
valorador_app.py
----------------
Interfaz de la herramienta de valoracion.

Lanzar con:  streamlit run valorador_app.py
"""

import streamlit as st

import metricas
import valoracion
import simulacion

from datos import (
    DatosEmpresa,
    ETIQUETAS,
    CLAVES_HISTORICO,
    ejemplo_microsoft,
    tabla_vacia,
)

st.set_page_config(page_title="Valorador de empresas", layout="wide")


# Streamlit reejecuta el script entero en cada interaccion, asi que el
# estado que debe sobrevivir a un clic vive en st.session_state.
if "empresa" not in st.session_state:
    st.session_state.empresa = DatosEmpresa(
        anios=[2019, 2020, 2021, 2022, 2023],
    )
    for clave in CLAVES_HISTORICO:
        setattr(st.session_state.empresa, clave, [0.0] * 5)

empresa: DatosEmpresa = st.session_state.empresa


with st.sidebar:
    st.header("Empresa")

    empresa.nombre = st.text_input("Nombre", value=empresa.nombre)
    empresa.ticker = st.text_input("Ticker", value=empresa.ticker)
    empresa.moneda = st.selectbox(
        "Moneda", ["USD", "EUR", "GBP"],
        index=["USD", "EUR", "GBP"].index(empresa.moneda),
    )

    st.divider()
    st.header("Mercado")

    empresa.precio = st.number_input(
        "Precio por accion", min_value=0.0, value=float(empresa.precio), step=1.0,
    )
    empresa.dividendo_por_accion = st.number_input(
        "Dividendo por accion (ultimo anio)",
        min_value=0.0, value=float(empresa.dividendo_por_accion), step=0.1,
    )

    st.divider()
    st.header("Supuestos")

    tasa_libre_riesgo = st.number_input(
        "Tasa libre de riesgo (%)", min_value=0.0, max_value=20.0,
        value=4.5, step=0.1,
        help="Bono estadounidense a 10 anios.",
    )
    coste_oportunidad = st.number_input(
        "Coste de oportunidad exigido (%)", min_value=0.0, max_value=40.0,
        value=10.0, step=0.5,
        help="Tasa de descuento. El club sugiere el doble de la tasa libre de riesgo.",
    )
    crecimiento_esperado = st.number_input(
        "Crecimiento anual esperado del BPA (%)", min_value=-20.0, max_value=60.0,
        value=10.0, step=0.5,
    )
    multiplo_salida = st.number_input(
        "Multiplo de salida (PER)", min_value=1.0, max_value=80.0,
        value=20.0, step=1.0,
        help="PER al que esperas que cotice la empresa al final del horizonte.",
    )
    horizonte = st.slider("Horizonte (anios)", min_value=1, max_value=15, value=5)

    supuestos = {
        "tasa_libre_riesgo": tasa_libre_riesgo / 100,
        "coste_oportunidad": coste_oportunidad / 100,
        "crecimiento_esperado": crecimiento_esperado / 100,
        "multiplo_salida": multiplo_salida,
        "horizonte": horizonte,
    }


st.title("Valorador de empresas")
st.caption("Todas las cifras de los estados financieros van en millones.")

pestana_datos, pestana_calidad, pestana_valoracion, pestana_simulacion = st.tabs(
    ["Datos", "Calidad", "Valoracion", "Simulacion"]
)


with pestana_datos:
    col_a, col_b, col_c = st.columns([1, 1, 2])

    with col_a:
        if st.button("Cargar ejemplo", use_container_width=True):
            st.session_state.empresa = ejemplo_microsoft()
            st.rerun()

    with col_b:
        if st.button("Vaciar", use_container_width=True):
            vacia = DatosEmpresa(anios=empresa.anios)
            for clave in CLAVES_HISTORICO:
                setattr(vacia, clave, [0.0] * len(empresa.anios))
            st.session_state.empresa = vacia
            st.rerun()

    st.subheader("Periodo")

    col_1, col_2 = st.columns(2)
    with col_1:
        anio_final = st.number_input(
            "Ultimo ejercicio", min_value=1990, max_value=2100,
            value=empresa.anios[-1] if empresa.anios else 2023, step=1,
        )
    with col_2:
        n_anios = st.number_input(
            "Numero de ejercicios", min_value=2, max_value=10,
            value=max(len(empresa.anios), 2), step=1,
        )

    nuevos_anios = list(range(int(anio_final) - int(n_anios) + 1, int(anio_final) + 1))

    if nuevos_anios != empresa.anios:
        if st.button("Aplicar periodo (se reinician los datos)"):
            nueva = DatosEmpresa(
                nombre=empresa.nombre,
                ticker=empresa.ticker,
                moneda=empresa.moneda,
                anios=nuevos_anios,
                precio=empresa.precio,
                dividendo_por_accion=empresa.dividendo_por_accion,
            )
            for clave in CLAVES_HISTORICO:
                setattr(nueva, clave, [0.0] * len(nuevos_anios))
            st.session_state.empresa = nueva
            st.rerun()

    st.subheader("Historico")
    st.caption(
        "Una columna por ejercicio, de mas antiguo a mas reciente. "
        "El CapEx aparece entre parentesis en el informe: introducelo en positivo."
    )

    tabla_editada = st.data_editor(
        empresa.a_tabla() if empresa.anios else tabla_vacia(nuevos_anios),
        use_container_width=True,
        num_rows="fixed",
        key="editor_historico",
    )
    empresa.aplicar_tabla(tabla_editada)

    st.subheader("Balance (ultimo ejercicio)")

    col_1, col_2, col_3 = st.columns(3)
    with col_1:
        empresa.caja_e_inversiones = st.number_input(
            "Caja e inversiones a corto", value=float(empresa.caja_e_inversiones), step=100.0
        )
        empresa.activos_corrientes = st.number_input(
            "Activos corrientes", value=float(empresa.activos_corrientes), step=100.0
        )
    with col_2:
        empresa.deuda_largo_plazo = st.number_input(
            "Deuda a largo plazo", value=float(empresa.deuda_largo_plazo), step=100.0
        )
        empresa.pasivos_corrientes = st.number_input(
            "Pasivos corrientes", value=float(empresa.pasivos_corrientes), step=100.0
        )
    with col_3:
        empresa.deuda_corriente = st.number_input(
            "Parte corriente de la deuda", value=float(empresa.deuda_corriente), step=100.0
        )
        empresa.gasto_intereses = st.number_input(
            "Gasto en intereses", value=float(empresa.gasto_intereses), step=10.0
        )

    st.divider()

    problemas = empresa.validar()
    if problemas:
        for p in problemas:
            st.warning(p)
    else:
        st.success("Datos completos y coherentes.")

    with st.expander("Guardar / cargar empresa"):
        st.download_button(
            "Descargar datos en JSON",
            data=empresa.a_json(),
            file_name=f"{empresa.ticker.lower() or 'empresa'}.json",
            mime="application/json",
        )
        subido = st.file_uploader("Cargar un archivo JSON", type="json")
        if subido is not None:
            try:
                st.session_state.empresa = DatosEmpresa.desde_json(
                    subido.read().decode("utf-8")
                )
                st.success("Datos cargados.")
                st.rerun()
            except Exception as error:
                st.error(f"No se pudo leer el archivo: {error}")


with pestana_calidad:
    if empresa.validar():
        st.warning("Completa los datos en la pestana anterior.")
    else:
        restar_sbc = st.toggle(
            "Restar la retribucion en acciones (SBC) al FCF",
            value=True,
            help=(
                "No es una salida de caja, pero es un gasto real de "
                "personal que diluye al accionista."
            ),
        )

        st.subheader("Evolucion")
        st.dataframe(
            metricas.tabla_evolucion(empresa, restar_sbc).style.format("{:,.0f}"),
            use_container_width=True,
        )

        st.subheader("Margenes")
        tabla_mg = metricas.tabla_margenes(empresa, restar_sbc)
        st.dataframe(tabla_mg.style.format("{:.1%}"), use_container_width=True)
        st.line_chart(tabla_mg.T)

        st.subheader("Crecimiento anual compuesto")
        col_1, col_2 = st.columns([1, 1])
        with col_1:
            st.dataframe(
                metricas.tabla_crecimiento(empresa, restar_sbc).style.format(
                    "{:.1%}", na_rep="n/d"
                ),
                use_container_width=True,
            )
        with col_2:
            conv = metricas.conversion_caja(empresa, restar_sbc)[-1]
            nde = metricas.net_debt_ebitda(empresa)
            tipo = metricas.tipo_interes_deuda(empresa)

            st.metric("Deuda neta (millones)", f"{metricas.deuda_neta(empresa):,.0f}")
            st.metric("Net Debt / EBITDA", f"{nde:.2f}x" if nde is not None else "n/d")
            st.metric("Conversion de caja", f"{conv:.0%}" if conv is not None else "n/d")
            st.metric("Tipo de interes de la deuda", f"{tipo:.2%}" if tipo is not None else "n/d")
            st.metric("Fondo de maniobra (millones)", f"{metricas.working_capital(empresa):,.0f}")

        st.subheader("Senales")
        for titulo, cumple, explicacion in metricas.senales(empresa, restar_sbc):
            icono = ":green[OK]" if cumple else ":red[Atencion]"
            st.markdown(f"**{icono} — {titulo}**  \n{explicacion}")

with pestana_valoracion:
    if empresa.validar():
        st.warning("Completa los datos en la pestana anterior.")
    else:
        restar_sbc_val = st.toggle(
            "Restar la retribucion en acciones (SBC) al FCF",
            value=True,
            key="restar_sbc_valoracion",
        )

        st.subheader("Multiplos actuales")
        mult = valoracion.multiplos_actuales(empresa, supuestos, restar_sbc_val)
        col_1, col_2, col_3, col_4 = st.columns(4)
        col_1.metric("PER", f"{mult['per']:.1f}x" if mult["per"] else "n/d")
        col_2.metric(
            "Earnings Yield",
            f"{mult['earnings_yield']:.1%}" if mult["earnings_yield"] else "n/d",
        )
        col_3.metric(
            "FCF Yield", f"{mult['fcf_yield']:.1%}" if mult["fcf_yield"] else "n/d"
        )
        col_4.metric("Dividend Yield", f"{mult['dividend_yield']:.1%}")
        st.caption(
            f"Tasa libre de riesgo: {mult['tasa_libre_riesgo']:.1%}. Una Yield por "
            "debajo de esta tasa solo se justifica si la empresa crece rapido."
        )

        st.divider()
        st.subheader("Retorno esperado")

        ret = valoracion.retorno_esperado(empresa, supuestos)
        if "error" in ret:
            st.warning(ret["error"])
        else:
            col_1, col_2, col_3, col_4 = st.columns(4)
            col_1.metric("Crecimiento BPA", f"{ret['crecimiento_bpa']:.1%}")
            col_2.metric("Dividendos", f"{ret['dividend_yield']:.1%}")
            col_3.metric("Var. multiplo", f"{ret['variacion_multiplo']:+.1%}")
            col_4.metric("Retorno esperado (CAGR)", f"{ret['retorno_esperado']:.1%}")
            st.caption(
                f"BPA: {ret['bpa_actual']:.2f} → {ret['bpa_final']:.2f} en "
                f"{supuestos['horizonte']} anios. Multiplo: "
                f"{ret['multiplo_actual']:.1f}x → {ret['multiplo_final']:.1f}x. "
                f"Precio: {ret['precio_actual']:.2f} → {ret['precio_final']:.2f}."
            )

        st.divider()
        st.subheader("Valor intrinseco y margen de seguridad")

        resumen = valoracion.resumen_valoracion(empresa, supuestos, restar_sbc_val)

        col_dcf, col_mult = st.columns(2)
        with col_dcf:
            st.markdown("**Descuento de flujos de caja (DCF)**")
            dcf = resumen["dcf"]
            if "error" in dcf:
                st.warning(dcf["error"])
            else:
                st.metric(
                    "Valor intrinseco", f"{dcf['valor_intrinseco']:,.2f} {empresa.moneda}"
                )
                mos_dcf = resumen.get("mos_dcf")
                if mos_dcf is not None:
                    color = "green" if mos_dcf > 0 else "red"
                    st.markdown(f"Margen de seguridad: :{color}[{mos_dcf:.1%}]")
                with st.expander("Detalle de los flujos"):
                    st.dataframe(
                        valoracion.tabla_flujos_dcf(dcf).style.format("{:.2f}"),
                        use_container_width=True,
                    )
                    st.caption(
                        f"Valor terminal: {dcf['valor_terminal']:,.2f} (valor "
                        f"presente: {dcf['valor_presente_terminal']:,.2f})."
                    )

        with col_mult:
            st.markdown("**Metodo de multiplos** (sin flujos intermedios)")
            mult_val = resumen["multiplo"]
            if "error" in mult_val:
                st.warning(mult_val["error"])
            else:
                st.metric(
                    "Valor intrinseco",
                    f"{mult_val['valor_intrinseco']:,.2f} {empresa.moneda}",
                )
                mos_multiplo = resumen.get("mos_multiplo")
                if mos_multiplo is not None:
                    color = "green" if mos_multiplo > 0 else "red"
                    st.markdown(f"Margen de seguridad: :{color}[{mos_multiplo:.1%}]")
                st.caption(
                    f"Precio objetivo en {supuestos['horizonte']} anios: "
                    f"{mult_val['precio_objetivo']:,.2f}."
                )

        st.caption(f"Precio actual: {empresa.precio:,.2f} {empresa.moneda}.")

with pestana_simulacion:
    if empresa.validar():
        st.warning("Completa los datos en la pestana anterior.")
    else:
        restar_sbc_sim = st.toggle(
            "Restar la retribucion en acciones (SBC) al FCF",
            value=True,
            key="restar_sbc_simulacion",
        )
        objetivo = st.radio(
            "Que quieres analizar",
            options=list(simulacion.OBJETIVOS.keys()),
            format_func=lambda k: simulacion.OBJETIVOS[k],
            horizontal=True,
        )

        st.subheader("Tabla de sensibilidad")

        variables_disponibles = list(simulacion.VARIABLES.keys())
        col_1, col_2 = st.columns(2)
        with col_1:
            eje_filas = st.selectbox(
                "Eje de filas",
                variables_disponibles,
                index=variables_disponibles.index("crecimiento_esperado"),
                format_func=lambda v: simulacion.VARIABLES[v]["etiqueta"],
            )
        with col_2:
            opciones_columnas = [v for v in variables_disponibles if v != eje_filas]
            indice_defecto = (
                opciones_columnas.index("multiplo_salida")
                if "multiplo_salida" in opciones_columnas
                else 0
            )
            eje_columnas = st.selectbox(
                "Eje de columnas",
                opciones_columnas,
                index=indice_defecto,
                format_func=lambda v: simulacion.VARIABLES[v]["etiqueta"],
            )

        tabla_sens = simulacion.tabla_sensibilidad(
            empresa,
            supuestos,
            eje_filas=eje_filas,
            eje_columnas=eje_columnas,
            objetivo=objetivo,
            restar_sbc=restar_sbc_sim,
        )
        formato_tabla = "{:.1%}" if objetivo == "retorno_esperado" else "{:,.2f}"
        st.dataframe(
            tabla_sens.style.format(formato_tabla, na_rep="n/d").background_gradient(
                cmap="RdYlGn", axis=None
            ),
            use_container_width=True,
        )

        st.divider()
        st.subheader("Simulacion de Monte Carlo")
        st.caption(
            "Muestrea el crecimiento, el multiplo y el coste de oportunidad "
            "para ver el rango de resultados posibles."
        )

        col_1, col_2, col_3, col_4 = st.columns(4)
        with col_1:
            n_sim = st.number_input(
                "Numero de simulaciones", min_value=100, max_value=20000,
                value=3000, step=100,
            )
        with col_2:
            desv_g = st.number_input(
                "Desv. crecimiento (pp)", min_value=0.0, max_value=30.0,
                value=5.0, step=0.5,
            ) / 100
        with col_3:
            desv_m = st.number_input(
                "Desv. multiplo (x)", min_value=0.0, max_value=20.0,
                value=4.0, step=0.5,
            )
        with col_4:
            desv_r = st.number_input(
                "Desv. coste oportunidad (pp)", min_value=0.0, max_value=10.0,
                value=1.0, step=0.5,
            ) / 100

        if st.button("Simular"):
            st.session_state.resultados_mc = simulacion.monte_carlo(
                empresa,
                supuestos,
                n_simulaciones=int(n_sim),
                desviacion_crecimiento=desv_g,
                desviacion_multiplo=desv_m,
                desviacion_coste_oportunidad=desv_r,
                objetivo=objetivo,
                restar_sbc=restar_sbc_sim,
            )

        if "resultados_mc" in st.session_state:
            resultados_mc = st.session_state.resultados_mc
            resumen_mc = simulacion.resumen_monte_carlo(
                resultados_mc,
                precio_actual=empresa.precio if objetivo == "valor_intrinseco" else None,
            )
            if "error" in resumen_mc:
                st.warning(resumen_mc["error"])
            else:
                formato_mc = "{:.1%}" if objetivo == "retorno_esperado" else "{:,.2f}"
                col_1, col_2, col_3 = st.columns(3)
                col_1.metric("Mediana (P50)", formato_mc.format(resumen_mc["mediana"]))
                col_2.metric("P10", formato_mc.format(resumen_mc["p10"]))
                col_3.metric("P90", formato_mc.format(resumen_mc["p90"]))

                if "prob_infravalorada" in resumen_mc:
                    st.metric(
                        "Probabilidad de estar infravalorada",
                        f"{resumen_mc['prob_infravalorada']:.0%}",
                    )

                st.bar_chart(simulacion.histograma(resultados_mc))
                st.caption(
                    f"{resumen_mc['n_validas']} de {resumen_mc['n_total']} "
                    "simulaciones produjeron un resultado valido."
                )
