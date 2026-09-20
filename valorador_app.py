import streamlit as st
import pandas as pd

st.title("Valorador de empresas")
st.write("Entorno funcionando correctamente.")

df = pd.DataFrame({"año": [2021, 2022, 2023], "ingresos": [168, 198, 212]})
st.dataframe(df)
st.line_chart(df.set_index("año"))