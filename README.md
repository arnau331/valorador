# Valorador de empresas

Herramienta de analisis fundamental y valoracion de empresas en Streamlit,
desarrollada para la candidatura al club de inversion de la UPV.

## Que hace

A partir del historico financiero de una empresa (income statement,
balance y cash flow) calcula:

- **Calidad**: margenes, CAGRs, conversion de caja, ratios de deuda y
  fondo de maniobra.
- **Valoracion**: PER, FCF Yield y Dividend Yield; retorno esperado
  (crecimiento del BPA + dividendos +/- variacion del multiplo); valor
  intrinseco por descuento de flujos de caja (DCF) y por el metodo de
  multiplos; margen de seguridad.
- **Simulacion**: tabla de sensibilidad y Monte Carlo sobre esos mismos
  resultados.

Los estados financieros van en millones de la moneda de la empresa; el
precio y el dividendo, en moneda por accion.

## Instalacion y ejecucion

```bash
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run valorador_app.py
```

La pestana "Datos" tiene un boton "Cargar ejemplo" con cifras de
Microsoft para probar la app sin rellenar nada a mano.

## Base teorica

Los conceptos y formulas (margenes, EBITDA, FCF, SBC, multiplos, retorno
esperado, DCF, margen de seguridad) vienen de la formacion en tres
documentos del club de inversion de la UPV: largo plazo y psicologia,
analisis de estados financieros, y basicos de valoracion.

## Como lo valide

Introduje a mano los datos reales de los ultimos ejercicios de Microsoft
y de Apple (10-K de cada una) y comprobe que los margenes, CAGRs, ratios
de deuda y multiplos que calcula la app coinciden con las cifras
publicadas por ambas empresas.

## Desarrollo

Usé Claude Code como asistente de desarrollo durante la construccion de
la herramienta.
