import pandas as pd
from geopy.distance import geodesic
import folium
import streamlit as st
from streamlit_folium import st_folium

# Configuración de la página
st.set_page_config(page_title="Mapa + Chat LLM", layout="centered")
st.title("📡 Mapa de Acceso Gratuito a Internet + Chat LLM")

# ---------------- CHATBOT ----------------
st.markdown("### 🧠 Chat LLM local")
if st.button("Abrir Chat"):
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html = f.read()
        st.components.v1.html(html, height=700)
    except FileNotFoundError:
        st.error("⚠️ No se encontró el archivo index.html. Asegúrate de que esté en la misma carpeta.")

# ---------------- MAPA ----------------
opcion = st.selectbox("Selecciona qué distrito mostrar:", ["Ambos", "La Victoria", "San Juan de Lurigancho"])

# Cargar datos
df_victoria = pd.read_csv("la_victoria.csv")
df_lurigancho = pd.read_csv("san_juan_de_lurigancho.csv")

# Limpiar vacíos
df_victoria.dropna(subset=["latitud", "longitud"], inplace=True)
df_lurigancho.dropna(subset=["latitud", "longitud"], inplace=True)

# Definir qué puntos mostrar
if opcion == "La Victoria":
    df_puntos = df_victoria
elif opcion == "San Juan de Lurigancho":
    df_puntos = df_lurigancho
else:
    df_puntos = pd.concat([df_victoria, df_lurigancho])

# Crear mapa
m = folium.Map(location=[df_puntos.latitud.mean(), df_puntos.longitud.mean()], zoom_start=12)

# Algoritmo de Prim para conectar puntos
def conectar_puntos_prim(df):
    lugares = df[["nombre_lugar", "latitud", "longitud"]].values
    num_lugares = len(lugares)
    visitados = [False] * num_lugares
    conexiones = []
    visitados[0] = True

    while len(conexiones) < num_lugares - 1:
        min_dist = float('inf')
        u, v = -1, -1
        for i in range(num_lugares):
            if visitados[i]:
                for j in range(num_lugares):
                    if not visitados[j]:
                        dist = geodesic((lugares[i][1], lugares[i][2]), (lugares[j][1], lugares[j][2])).meters
                        if dist < min_dist:
                            min_dist = dist
                            u, v = i, j
        visitados[v] = True
        conexiones.append((min_dist, lugares[u][0], lugares[v][0]))

    for _, lugar1, lugar2 in conexiones:
        lat1, lon1 = df[df["nombre_lugar"] == lugar1][["latitud", "longitud"]].values[0]
        lat2, lon2 = df[df["nombre_lugar"] == lugar2][["latitud", "longitud"]].values[0]
        folium.PolyLine([(lat1, lon1), (lat2, lon2)], color="blue").add_to(m)

# Agregar marcadores y líneas
if opcion in ["Ambos", "La Victoria"]:
    df_victoria.apply(lambda row: folium.Marker([row.latitud, row.longitud], popup=row.nombre_lugar).add_to(m), axis=1)
    conectar_puntos_prim(df_victoria)

if opcion in ["Ambos", "San Juan de Lurigancho"]:
    df_lurigancho.apply(lambda row: folium.Marker([row.latitud, row.longitud], popup=row.nombre_lugar).add_to(m), axis=1)
    conectar_puntos_prim(df_lurigancho)

# Mostrar mapa
st.markdown("### 🗺️ Mapa interactivo con conexión entre puntos")
st_folium(m, width=800, height=600)
