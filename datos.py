"""
datos.py
--------
Define la estructura de datos de una empresa y las funciones para
convertirla a/desde una tabla editable y a/desde JSON.

Convenio de unidades (IMPORTANTE, mantenerlo en todo el proyecto):
  - Todas las magnitudes de los estados financieros: MILLONES de la moneda.
  - Precio y dividendo por accion: unidades de moneda POR ACCION.
  - Acciones en circulacion: MILLONES de acciones.
  Asi, beneficio_neto / acciones da directamente el BPA en moneda por accion.
"""

from dataclasses import dataclass, field, asdict
import json

import pandas as pd


# Filas de la tabla historica. El orden aqui es el orden en que
# apareceran en la interfaz.
FILAS_HISTORICO = [
    ("ingresos", "Ingresos (Total revenue)"),
    ("beneficio_bruto", "Beneficio bruto (Gross margin)"),
    ("ebit", "EBIT (Operating income)"),
    ("beneficio_neto", "Beneficio neto (Net income)"),
    ("acciones", "Acciones diluidas (millones)"),
    ("ocf", "Flujo de caja operativo (Net cash from operations)"),
    ("capex", "CapEx (en positivo)"),
    ("sbc", "Stock-based compensation"),
    ("dya", "Depreciacion y amortizacion"),
]

ETIQUETAS = dict(FILAS_HISTORICO)
CLAVES_HISTORICO = [clave for clave, _ in FILAS_HISTORICO]


@dataclass
class DatosEmpresa:
    """Todos los datos de entrada necesarios para analizar una empresa."""

    nombre: str = ""
    ticker: str = ""
    moneda: str = "USD"

    # Historico: una lista por magnitud, de mas antiguo a mas reciente.
    anios: list[int] = field(default_factory=list)
    ingresos: list[float] = field(default_factory=list)
    beneficio_bruto: list[float] = field(default_factory=list)
    ebit: list[float] = field(default_factory=list)
    beneficio_neto: list[float] = field(default_factory=list)
    acciones: list[float] = field(default_factory=list)
    ocf: list[float] = field(default_factory=list)
    capex: list[float] = field(default_factory=list)
    sbc: list[float] = field(default_factory=list)
    dya: list[float] = field(default_factory=list)

    # Balance: solo el ultimo ejercicio.
    deuda_largo_plazo: float = 0.0
    deuda_corriente: float = 0.0
    caja_e_inversiones: float = 0.0
    activos_corrientes: float = 0.0
    pasivos_corrientes: float = 0.0
    gasto_intereses: float = 0.0

    # Mercado.
    precio: float = 0.0
    dividendo_por_accion: float = 0.0

    # --- Utilidades -----------------------------------------------------

    @property
    def n_anios(self) -> int:
        return len(self.anios)

    def serie(self, clave: str) -> list[float]:
        """Devuelve una de las series historicas por su nombre de clave."""
        return getattr(self, clave)

    def ultimo(self, clave: str) -> float:
        """Ultimo valor (mas reciente) de una serie historica."""
        serie = self.serie(clave)
        if not serie:
            raise ValueError(f"La serie '{clave}' esta vacia.")
        return serie[-1]

    def validar(self) -> list[str]:
        """Devuelve una lista de problemas encontrados. Vacia = todo bien."""
        problemas = []

        if self.n_anios < 2:
            problemas.append("Hacen falta al menos 2 anios de historico.")

        for clave in CLAVES_HISTORICO:
            serie = self.serie(clave)
            if len(serie) != self.n_anios:
                problemas.append(
                    f"'{ETIQUETAS[clave]}' tiene {len(serie)} valores "
                    f"y deberia tener {self.n_anios}."
                )

        if self.precio <= 0:
            problemas.append("El precio de la accion debe ser mayor que cero.")

        if self.ingresos and any(v <= 0 for v in self.ingresos):
            problemas.append("Hay ingresos nulos o negativos.")

        if self.acciones and any(v <= 0 for v in self.acciones):
            problemas.append("Hay un numero de acciones nulo o negativo.")

        if self.capex and any(v < 0 for v in self.capex):
            problemas.append(
                "Hay CapEx negativo. En el informe aparece entre parentesis, "
                "pero aqui debe introducirse en positivo."
            )

        return problemas

    # --- Conversion a/desde tabla (para st.data_editor) -----------------

    def a_tabla(self) -> pd.DataFrame:
        """Convierte el historico en un DataFrame: filas = conceptos, columnas = anios."""
        datos = {
            ETIQUETAS[clave]: self.serie(clave) for clave in CLAVES_HISTORICO
        }
        tabla = pd.DataFrame(datos, index=self.anios).T
        tabla.columns = [str(a) for a in self.anios]
        return tabla

    def aplicar_tabla(self, tabla: pd.DataFrame) -> None:
        """Vuelca el contenido de la tabla editada de vuelta al objeto."""
        self.anios = [int(c) for c in tabla.columns]
        etiqueta_a_clave = {v: k for k, v in ETIQUETAS.items()}
        for etiqueta, fila in tabla.iterrows():
            clave = etiqueta_a_clave.get(etiqueta)
            if clave is not None:
                setattr(self, clave, [float(v) for v in fila.tolist()])

    # --- Persistencia ---------------------------------------------------

    def a_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)

    @classmethod
    def desde_json(cls, texto: str) -> "DatosEmpresa":
        return cls(**json.loads(texto))


def tabla_vacia(anios: list[int]) -> pd.DataFrame:
    """Tabla de historico con todo a cero, lista para que el usuario la rellene."""
    return pd.DataFrame(
        0.0,
        index=[ETIQUETAS[c] for c in CLAVES_HISTORICO],
        columns=[str(a) for a in anios],
    )


def ejemplo_microsoft() -> DatosEmpresa:
    """
    Datos de ejemplo para probar la aplicacion.

    ATENCION: los anios 2019-2022 son APROXIMACIONES para poder probar la
    interfaz. Solo 2018 y 2023 proceden de los estados financieros reales.
    Sustituir por los datos del 10-K antes de sacar ninguna conclusion.
    """
    return DatosEmpresa(
        nombre="Microsoft Corporation (DATOS DE PRUEBA)",
        ticker="MSFT",
        moneda="USD",
        anios=[2018, 2019, 2020, 2021, 2022, 2023],
        ingresos=[110360, 125843, 143015, 168088, 198270, 211915],
        beneficio_bruto=[72007, 82933, 96937, 115856, 135620, 146052],
        ebit=[35058, 42959, 52959, 69916, 83383, 88523],
        beneficio_neto=[16571, 39240, 44281, 61271, 72738, 72361],
        acciones=[7794, 7753, 7683, 7608, 7540, 7472],
        ocf=[43884, 52185, 60675, 76740, 89035, 87582],
        capex=[11632, 13925, 15441, 20622, 23886, 28107],
        sbc=[3940, 4652, 5289, 6118, 7502, 9611],
        dya=[10261, 11682, 12796, 11686, 14460, 13861],
        deuda_largo_plazo=41990,
        deuda_corriente=5247,
        caja_e_inversiones=111262,
        activos_corrientes=184257,
        pasivos_corrientes=104149,
        gasto_intereses=1968,
        precio=330.0,
        dividendo_por_accion=2.72,
    )