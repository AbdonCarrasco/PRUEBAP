import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
from geopy.distance import geodesic
import folium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="WiFi Map con Grafos", layout="centered")
st.title("📡 Zonas WiFi gratuitas en Lima – con grafo de conexión")

# 🔍 Extraer puntos WiFi desde la web de WiFiMap
@st.cache_data
def obtener_puntos_wifi():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.wifimap.io/es/map/2190-lima")
    time.sleep(10)  # Esperar carga del mapa

    # Ejecutar JS para obtener puntos desde el mapa
    data_js = driver.execute_script("""
        return window.__WIFI_MAP_APP_STORE__?.hotspots || [];
    """)
    driver.quit()

    datos = []
    for punto in data_js:
        if all(k in punto for k in ("name", "lat", "lng")):
            datos.append({
                "nombre_lugar": punto["name"],
                "latitud": punto["lat"],
                "longitud": punto["lng"]
            })

    return pd.DataFrame(datos)

# 📥 Obtener datos
with st.spinner("Cargando puntos WiFi desde WiFiMap..."):
    df = obtener_puntos_wifi()

if df.empty:
    st.error("No se encontraron puntos WiFi.")
    st.stop()

# 🧹 Limpiar duplicados
df = df.drop_duplicates(subset=["latitud", "longitud"])

# 🗺️ Crear mapa
m = folium.Map(location=[df.latitud.mean(), df.longitud.mean()], zoom_start=12)

# 🔗 Conectar puntos con algoritmo de Prim
def conectar_puntos_prim(df):
    lugares = df[["nombre_lugar", "latitud", "longitud"]].values
    num_lugares = len(lugares)
    visitados = [False] * num_lugares
    conexiones = []
    visitados[0] = True

    while len(conexiones) < num_lugares - 1:
        min_dist = float('inf')
        u = v = -1
        for i in range(num_lugares):
            if visitados[i]:
                for j in range(num_lugares):
                    if not visitados[j]:
                        dist = geodesic(
                            (lugares[i][1], lugares[i][2]),
                            (lugares[j][1], lugares[j][2])
                        ).meters
                        if dist < min_dist:
                            min_dist = dist
                            u, v = i, j
        visitados[v] = True
        conexiones.append((lugares[u], lugares[v]))

    for (lugar1, lugar2) in conexiones:
        folium.PolyLine(
            [(lugar1[1], lugar1[2]), (lugar2[1], lugar2[2])],
            color="blue"
        ).add_to(m)

# 📌 Agregar marcadores y grafo
df.apply(lambda row: folium.Marker(
    [row.latitud, row.longitud], popup=row.nombre_lugar
).add_to(m), axis=1)

conectar_puntos_prim(df)

# 🗺️ Mostrar mapa
st.markdown("### 🔗 Grafo de conexiones optimizadas (algoritmo de Prim)")
st_folium(m, width=800, height=600)
