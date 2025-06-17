import osmnx as ox
import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium
from geopy.distance import geodesic

st.set_page_config(page_title="WiFi manual con grafo", layout="centered")
st.title("📡 Medición de distancia desde tu punto en el mapa hasta WiFi seleccionado")

# Lista de distritos posibles
distritos = sorted([
    "Ate", "Barranco", "Breña", "Carabayllo", "Cercado de Lima", "Chorrillos",
    "Comas", "El Agustino", "Independencia", "Jesús María", "La Molina",
    "La Victoria", "Lince", "Los Olivos", "Magdalena del Mar", "Miraflores",
    "Pueblo Libre", "Puente Piedra", "Rímac", "San Borja", "San Isidro",
    "San Juan de Lurigancho", "San Juan de Miraflores", "San Luis",
    "San Martín de Porres", "San Miguel", "Santa Anita", "Santiago de Surco",
    "Surquillo", "Villa El Salvador", "Villa María del Triunfo", "Callao"
])

# Elegir distrito
distrito = st.selectbox("Selecciona un distrito de Lima:", distritos)

# Función para obtener puntos WiFi públicos desde OSM
@st.cache_data
def obtener_wifi(distrito):
    try:
        lugar = ox.geocode_to_gdf(f"{distrito}, Lima, Peru")
        tags = {"internet_access": "wlan"}
        gdf = ox.features.features_from_polygon(lugar.geometry.iloc[0], tags)
        gdf = gdf[gdf.geometry.geom_type == "Point"]
        df = pd.DataFrame({
            "nombre_lugar": gdf.get("name", "WiFi público"),
            "latitud": gdf.geometry.y,
            "longitud": gdf.geometry.x
        })
        return df.reset_index(drop=True)
    except Exception as e:
        st.warning(f"No se encontraron puntos WiFi para {distrito}: {e}")
        return pd.DataFrame()

# Cargar WiFi
df = obtener_wifi(distrito)
st.markdown(f"### 🔍 Se encontraron **{len(df)} puntos WiFi** en {distrito}")
if df.empty:
    st.stop()

df.drop_duplicates(subset=["latitud", "longitud"], inplace=True)

# Crear mapa
m = folium.Map(location=[df.latitud.mean(), df.longitud.mean()], zoom_start=14)

# Agregar nodos WiFi
for idx, row in df.iterrows():
    folium.Marker(
        [row.latitud, row.longitud],
        popup=row.nombre_lugar or "WiFi público",
        icon=folium.Icon(color="green")
    ).add_to(m)

# 🔗 Algoritmo de Prim para conexiones
def conectar_con_prim(df):
    lugares = df[["nombre_lugar", "latitud", "longitud"]].values
    if len(lugares) < 2:
        return
    visitados = [False] * len(lugares)
    conexiones = []
    visitados[0] = True
    while len(conexiones) < len(lugares) - 1:
        min_dist = float("inf")
        u = v = -1
        for i in range(len(lugares)):
            if visitados[i]:
                for j in range(len(lugares)):
                    if not visitados[j]:
                        dist = geodesic((lugares[i][1], lugares[i][2]), (lugares[j][1], lugares[j][2])).meters
                        if dist < min_dist:
                            min_dist = dist
                            u, v = i, j
        visitados[v] = True
        conexiones.append((lugares[u], lugares[v]))
    for a, b in conexiones:
        folium.PolyLine([(a[1], a[2]), (b[1], b[2])], color="blue", weight=2).add_to(m)

conectar_con_prim(df)

# 🧭 Paso 1: usuario hace clic para marcar ubicación
st.markdown("### 🧭 Marca tu ubicación haciendo clic en el mapa")

respuesta = st_folium(m, width=800, height=600)

if respuesta and respuesta.get("last_clicked"):
    lat_usuario = respuesta["last_clicked"]["lat"]
    lon_usuario = respuesta["last_clicked"]["lng"]
    st.success(f"📍 Ubicación registrada: ({lat_usuario:.6f}, {lon_usuario:.6f})")

    # Paso 2: elegir punto WiFi
    st.markdown("### 📶 Ahora selecciona un punto WiFi para medir la distancia")
    lista_wifi = df["nombre_lugar"].fillna("WiFi público").tolist()
    punto_wifi = st.selectbox("Punto WiFi disponible:", lista_wifi)

    if punto_wifi:
        destino = df[df["nombre_lugar"] == punto_wifi].iloc[0]
        lat_wifi = destino["latitud"]
        lon_wifi = destino["longitud"]

        distancia = geodesic((lat_usuario, lon_usuario), (lat_wifi, lon_wifi)).meters
        st.markdown(f"📏 Distancia desde tu punto hasta '{punto_wifi}': **{distancia:.2f} metros**")

        # Mostrar ubicación del usuario
        folium.Marker(
            [lat_usuario, lon_usuario],
            tooltip="Tu ubicación",
            icon=folium.Icon(color="red", icon="user")
        ).add_to(m)

        # Dibujar arista entre ubicación y punto WiFi
        folium.PolyLine(
            [(lat_usuario, lon_usuario), (lat_wifi, lon_wifi)],
            color="orange", weight=3, tooltip="Distancia"
        ).add_to(m)

        st.markdown("### 🗺️ Mapa actualizado con conexión entre nodos")
        st_folium(m, width=800, height=600)
else:
    st.info("Haz clic en el mapa para registrar tu ubicación primero.")
