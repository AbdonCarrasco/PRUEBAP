import pandas as pd
from geopy.distance import geodesic
import folium
import streamlit as st
from streamlit_folium import st_folium

st.title("Mi Proyecto con Chat LLM")

st.set_page_config(page_title="Chat LLM", layout="centered")
st.title("Mi Proyecto con Chat LLM")

if st.button("Abrir Chat"):
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()
    st.components.v1.html(html, height=700)





st.set_page_config(page_title="Mapa WiFi Gratuito", layout="centered")
st.title("📡 Mapa de Acceso Gratuito a Internet por Distrito")

# Menú desplegable
opcion = st.selectbox("Selecciona qué distrito mostrar:", ["Ambos", "La Victoria", "San Juan de Lurigancho"])

# Leer archivos
df_victoria = pd.read_csv("la_victoria.csv")
df_lurigancho = pd.read_csv("san_juan_de_lurigancho.csv")

# Limpiar vacíos
df_victoria.dropna(subset=["latitud", "longitud"], inplace=True)
df_lurigancho.dropna(subset=["latitud", "longitud"], inplace=True)

# Seleccionar DataFrame según opción
if opcion == "La Victoria":
    df_puntos = df_victoria
elif opcion == "San Juan de Lurigancho":
    df_puntos = df_lurigancho
else:
    df_puntos = pd.concat([df_victoria, df_lurigancho])

# Crear mapa
m = folium.Map(location=[df_puntos.latitud.mean(), df_puntos.longitud.mean()], zoom_start=12)

# Función de conexión utilizando el algoritmo de Prim
def conectar_puntos_prim(df):
    # Almacenar los lugares como una lista de tuplas (nombre_lugar, latitud, longitud)
    lugares = df[["nombre_lugar", "latitud", "longitud"]].values
    num_lugares = len(lugares)

    # Inicializar las estructuras para Prim
    visitados = [False] * num_lugares  # Lista de nodos visitados
    conexiones = []  # Lista de conexiones de la forma (distancia, nodo_1, nodo_2)
    
    # Comenzamos con el primer nodo
    visitados[0] = True  # Marcamos el primer nodo como visitado
    
    # Mientras haya nodos no visitados
    while len(conexiones) < num_lugares - 1:
        min_dist = float('inf')
        u, v = -1, -1
        for i in range(num_lugares):
            if visitados[i]:
                for j in range(num_lugares):
                    if not visitados[j]:  # Solo considerar nodos no visitados
                        dist = geodesic((lugares[i][1], lugares[i][2]), (lugares[j][1], lugares[j][2])).meters
                        if dist < min_dist:
                            min_dist = dist
                            u, v = i, j
        visitados[v] = True  # Marcar el nodo 'v' como visitado
        conexiones.append((min_dist, lugares[u][0], lugares[v][0]))  # Añadir la conexión
    
    # Dibujar las conexiones en el mapa
    for _, lugar1, lugar2 in conexiones:
        lat1, lon1 = df[df["nombre_lugar"] == lugar1][["latitud", "longitud"]].values[0]
        lat2, lon2 = df[df["nombre_lugar"] == lugar2][["latitud", "longitud"]].values[0]
        folium.PolyLine([(lat1, lon1), (lat2, lon2)], color="blue").add_to(m)

# Agregar puntos y líneas según lo elegido
if opcion in ["Ambos", "La Victoria"]:
    df_victoria.apply(lambda row: folium.Marker([row.latitud, row.longitud], popup=row.nombre_lugar).add_to(m), axis=1)
    conectar_puntos_prim(df_victoria)

if opcion in ["Ambos", "San Juan de Lurigancho"]:
    df_lurigancho.apply(lambda row: folium.Marker([row.latitud, row.longitud], popup=row.nombre_lugar).add_to(m), axis=1)
    conectar_puntos_prim(df_lurigancho)

# Mostrar mapa
st.markdown("### 🌐 Mapa interactivo")
st_folium(m, width=800, height=600)
