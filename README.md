# Valorador de empresas

Herramienta de analisis fundamental y valoracion de empresas en Streamlit,
desarrollada para la candidatura al club de inversion de la UPV.

## Que hace

- **Datos** — entrada y validacion del historico financiero (income
  statement, balance, cash flow) y de los datos de mercado de la empresa.
- **Calidad** — margenes, CAGRs, conversion de caja, ratios de deuda,
  fondo de maniobra y una serie de senales cualitativas derivadas de la
  formacion del club.
- **Valoracion** — multiplos actuales (PER, Earnings Yield, FCF Yield,
  Dividend Yield) comparados con la tasa libre de riesgo; retorno esperado
  descompuesto en crecimiento del BPA, dividendos y variacion del
  multiplo; valor intrinseco por descuento de flujos de caja (DCF) y por
  el metodo de multiplos; margen de seguridad.
- **Simulacion** — tabla de sensibilidad cruzando dos supuestos
  cualesquiera, y simulacion de Monte Carlo sobre el valor intrinseco o
  el retorno esperado.

## Como lanzarla

```bash
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run valorador_app.py
```

La pestana "Datos" incluye un boton "Cargar ejemplo" con cifras de
Microsoft para probar la aplicacion sin tener que rellenar nada a mano.

## Estructura

| Archivo             | Contenido                                                        |
|----------------------|-------------------------------------------------------------------|
| `datos.py`           | Dataclass `DatosEmpresa`, entrada/validacion, tabla y JSON.       |
| `metricas.py`        | Margenes, CAGRs, conversion de caja, ratios de deuda.             |
| `valoracion.py`      | Multiplos, retorno esperado, DCF, valor por multiplo, MoS.        |
| `simulacion.py`      | Tabla de sensibilidad y Monte Carlo.                               |
| `valorador_app.py`   | Interfaz Streamlit con las cuatro pestanas.                        |

`datos.py`, `metricas.py`, `valoracion.py` y `simulacion.py` no dependen
de Streamlit: son funciones puras, faciles de probar por separado.

## Convencion de unidades

- Magnitudes de los estados financieros: **millones** de la moneda de la
  empresa.
- Precio y dividendo por accion: moneda **por accion**.
- Acciones en circulacion: **millones** de acciones.

## Nota sobre los datos de ejemplo

Los anios 2019-2022 del ejemplo de Microsoft son aproximaciones pensadas
solo para probar la interfaz; unicamente 2018 y 2023 proceden de los
estados financieros reales. No usar para sacar conclusiones de inversion.

---

Basado en la formacion del club de inversion de la UPV (largo plazo y
psicologia, analisis de estados financieros, y basicos de valoracion).
