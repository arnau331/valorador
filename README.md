# Valorador de empresas

Herramienta de análisis fundamental y valoración de empresas en Streamlit,
desarrollada para la candidatura al club de inversión de la UPV.

## Qué hace

A partir del histórico financiero de una empresa (income statement,
balance y cash flow) calcula:

- **Calidad**: márgenes, CAGRs, conversión de caja, ratios de deuda y
  fondo de maniobra.
- **Valoración**: PER, FCF Yield y Dividend Yield; retorno esperado
  (crecimiento del BPA + dividendos +/- variación del múltiplo); valor
  intrínseco por descuento de flujos de caja (DCF) y por el método de
  múltiplos; margen de seguridad.
- **Simulación**: tabla de sensibilidad y Monte Carlo sobre esos mismos
  resultados.

Los estados financieros van en millones de la moneda de la empresa; el
precio y el dividendo, en moneda por acción.

## Instalación y ejecución

```bash
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run valorador_app.py
```

La pestaña "Datos" tiene un botón "Cargar ejemplo" con cifras de
Microsoft para probar la app sin rellenar nada a mano.

## Base teórica

Los conceptos y fórmulas (márgenes, EBITDA, FCF, SBC, múltiplos, retorno
esperado, DCF, margen de seguridad) vienen de la formación en tres
documentos del club de inversión de la UPV: largo plazo y psicología,
análisis de estados financieros, y básicos de valoración.

## Cómo lo validé

Introduje a mano los datos reales de los últimos ejercicios de Microsoft
y de Apple (10-K de cada una) y comprobé que los márgenes, CAGRs, ratios
de deuda y múltiplos que calcula la app coinciden con las cifras
publicadas por ambas empresas.

## Desarrollo

Usé Claude Code como asistente de desarrollo durante la construcción de
la herramienta.
