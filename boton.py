import streamlit as st

st.set_page_config(page_title="Test", layout="centered")
st.title("🔘 Botón de prueba")

if st.button("Presióname"):
    st.success("¡Funcionando!")
