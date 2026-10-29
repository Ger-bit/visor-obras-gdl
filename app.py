# -*- coding: utf-8 -*-
"""
Created on Wed Oct 28 11:27:57 2026

@author: german
"""
#OBRASv2.1

# ============================================================
# 1. LIBRERÍAS
# ============================================================
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
import unicodedata
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# ============================================================
# 2. CONFIG STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Visor de Obras Públicas",
    layout="wide"
)

st.title("VISOR DE OBRAS PÚBLICAS GUADALAJARA 🏗️")

# ============================================================
# 3. RUTAS
# ============================================================

ruta_colonias_shp = "capas/ColoniasGDL.shp"

ruta_comunidades_shp = "capas/comunidades_gdl_v5.gpkg"

ruta_distritos_shp = "capas/DistritoLocalSept2022.shp"

ruta_excel_obras = "input/obras_publicas_231026.xlsx"

ruta_poblacion = "input/colonias_2021_pob.csv"

# ============================================================
# 4. FUNCIONES
# ============================================================

def normalizar_texto(texto):

    if pd.isna(texto):
        return ""

    texto = str(texto)

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        c
        for c in texto
        if not unicodedata.combining(c)
    )

    texto = texto.upper()

    texto = " ".join(
        texto.strip().split()
    )

    return texto

# ============================================================
# 5. CARGA DE DATOS
# ============================================================

@st.cache_data
def cargar_datos():

    obras = pd.read_excel(ruta_excel_obras)

    poblacion = pd.read_csv(ruta_poblacion)

    colonias = gpd.read_file(ruta_colonias_shp)

    comunidades = gpd.read_file(ruta_comunidades_shp)

    distritos = gpd.read_file(ruta_distritos_shp)

    return obras, poblacion, colonias, comunidades, distritos

obras, poblacion, colonias, comunidades, distritos = cargar_datos()

# ============================================================
# 6. NORMALIZACIÓN
# ============================================================

# Obras
obras["colonia_norm"] = obras["Colonia"].apply(normalizar_texto)

# Población
poblacion["colonia_norm"] = poblacion["nombre2"].apply(normalizar_texto)

# Colonias SHP
colonias["colonia_norm"] = colonias["NOMBRE2"].apply(normalizar_texto)

# ============================================================
# 7. INCORPORAR POBLACIÓN POR COLONIA
# ============================================================

# Crear tabla de población limpia

poblacion_cruce = poblacion[
    [
        "colonia_norm",
        "POBTOT"
    ]
].copy()

# Eliminar duplicados

poblacion_cruce = poblacion_cruce.drop_duplicates(
    subset=["colonia_norm"]
)

# Cruce directo Obras -> Población

obras = obras.merge(

    poblacion_cruce,

    on="colonia_norm",

    how="left"

)

# Renombrar

obras.rename(

    columns={
        "POBTOT": "Poblacion_Colonia"
    },

    inplace=True

)

# Diagnóstico

coincidencias = obras[
    "Poblacion_Colonia"
].notna().sum()

print(
    f"Coincidencias población: "
    f"{coincidencias} de {len(obras)}"
)

#Prueba de cruces de población
#st.write(
#    obras[
#        [
#            "Colonia",
#            "colonia_norm",
#            "Poblacion_Colonia"
#        ]
#    ].head(30)
#)

# ============================================================
# 8. FILTRAR DISTRITOS DE GDL
# ============================================================

distritos = distritos[
    distritos["DISTRITO_L"].isin([8,9,11,13])
]

# ============================================================
# 9. SIDEBAR
# ============================================================

st.sidebar.header("Filtros")

estatus = st.sidebar.multiselect(
    "Estatus",
    obras["Estatus"].dropna().unique(),
    default=obras["Estatus"].dropna().unique()
)


tipo_obra = st.sidebar.multiselect(
    "Tipo de Obra",
    obras["Tipo de Obra"].dropna().unique(),
    default=obras["Tipo de Obra"].dropna().unique()
)

responsable = st.sidebar.multiselect(
    "Responsable",
    obras["Responsable obra"].dropna().unique(),
    default=obras["Responsable obra"].dropna().unique()
)

comunidad = st.sidebar.multiselect(
    "Comunidad",
    obras["Comunidad"].dropna().unique(),
    default=obras["Comunidad"].dropna().unique()
)

distrito = st.sidebar.multiselect(
    "Distrito",
    obras["Distrito"].dropna().unique(),
    default=obras["Distrito"].dropna().unique()
)

# ============================================================
# 10. FILTROS NUMÉRICOS
# ============================================================

#
# Monto MDP

obras["Monto MDP"] = (
    obras["Monto MDP"]
    .astype(str)
    .str.replace("$","", regex=False)
    .str.replace(",","", regex=False)
    .str.strip()
)

obras["Monto MDP"] = pd.to_numeric(
    obras["Monto MDP"],
    errors="coerce"
)

# Avance físico

obras["Avance físico"] = (
    obras["Avance físico"]
    .astype(str)
    .str.replace("%","", regex=False)
    .str.strip()
)

obras["Avance físico"] = pd.to_numeric(
    obras["Avance físico"],
    errors="coerce"
)

# sustituir nulos

obras["Monto MDP"] = obras["Monto MDP"].fillna(0)

obras["Avance físico"] = obras["Avance físico"].fillna(0)
#
monto_min = float(obras["Monto MDP"].fillna(0).min())
monto_max = float(obras["Monto MDP"].fillna(0).max())

rango_monto = st.sidebar.slider(
    "Monto MDP",
    monto_min,
    monto_max,
    (monto_min,monto_max)
)

# ============================================================
# 11. FILTRADO
# ============================================================

df = obras[
    (obras["Estatus"].isin(estatus))
    &
    (obras["Tipo de Obra"].isin(tipo_obra))
    &
    (obras["Responsable obra"].isin(responsable))
    &
    (obras["Comunidad"].isin(comunidad))
    &
    (obras["Distrito"].isin(distrito))
    &
    (obras["Monto MDP"].between(
        rango_monto[0],
        rango_monto[1]
    ))
]


# ============================================================
# 12. KPI
# ============================================================

obras_concluidas = len(
    df[
        df["Estatus"].isin([
            "Obra Concluida",
            "Entregado"
        ])
    ]
)

obras_proceso = len(
    df[
        df["Estatus"].isin([
            "En proceso",
            "Por Arrancar",
            "Por Licitar"
        ])
    ]
)

colonias_intervenidas = (
    df["Colonia"]
    .dropna()
    .nunique()
)

monto_total = (
    df["Monto MDP"]
    .fillna(0)
    .sum()
)

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Obras",
    len(df)
)

c2.metric(
    "Concluidas",
    obras_concluidas
)

c3.metric(
    "En proceso",
    obras_proceso
)

c4.metric(
    "Colonias intervenidas",
    colonias_intervenidas
)

c5.metric(
    "Inversión (MDP)",
    f"{monto_total:,.1f}"
)

st.markdown("""
<style>

[data-testid="stMetric"] {
    text-align: center;
}

[data-testid="stMetricValue"] {
    font-size: 1.5rem;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# 13.0 BUSCADOR DE COLONIAS
# ============================================================

lista_colonias = sorted(
    df["Colonia"]
    .dropna()
    .unique()
)

colonia_busqueda = st.selectbox(
    "🔎 Buscar colonia",
    [""] + lista_colonias
)

if colonia_busqueda:

    df = df[
        df["Colonia"] == colonia_busqueda
    ]

# ============================================================
# 13. MAPA
# ============================================================

mapa = folium.Map(
    location=[20.6736,-103.344],
    zoom_start=12,
    tiles=None
)

# ============================================================
# 14. BASEMAPS
# ============================================================

folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    attr="Google",
    name="Google Maps"
).add_to(mapa)

folium.TileLayer(
    tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    attr="Google",
    name="Google Satelital"
).add_to(mapa)

# ============================================================
# 15. CAPAS GEO
# ============================================================

colonias = colonias.to_crs(4326)

comunidades = comunidades.to_crs(4326)

distritos = distritos.to_crs(4326)


folium.GeoJson(
    comunidades,
    name="Comunidades",
    style_function=lambda x:{
        "fillOpacity":0,
        "color":"purple",
        "weight":2
    }
).add_to(mapa)

folium.GeoJson(
    distritos,
    name="Distritos",
    style_function=lambda x:{
        "fillOpacity":0,
        "color":"black",
        "weight":3
    }
).add_to(mapa)

folium.GeoJson(

    colonias,

    name="Colonias",

    style_function=lambda x: {

        "fillColor":"#90CAF9",

        "fillOpacity":0.05,

        "color":"#607D8B",

        "weight":0.4

    },

    highlight_function=lambda x: {

        "fillColor":"#42A5F5",

        "fillOpacity":0.30,

        "color":"#1565C0",

        "weight":2

    },

    tooltip=folium.GeoJsonTooltip(

        fields=["NOMBRE2"],

        aliases=["Colonia:"],

        sticky=True

    )

).add_to(mapa)


# ============================================================
# 16. COLORES
# ============================================================

COLORES = {

    "Obra Concluida":"green",

    "En proceso":"orange",

    "Entregado":"purple",

    "Por Arrancar":"blue",

    "Por Licitar":"red",

    "Por contratar":"gray"

}

###AJUSTE

obras["Latitud"] = pd.to_numeric(
    obras["Latitud"],
    errors="coerce"
)

obras["Longitud"] = pd.to_numeric(
    obras["Longitud"],
    errors="coerce"
)

# ============================================================
# 17. CLUSTER OBRAS
# ============================================================

cluster = MarkerCluster(
    name="Obras"
).add_to(mapa)

for _, row in df.iterrows():

    lat = row["Latitud"]
    lon = row["Longitud"]

    if pd.isna(lat) or pd.isna(lon):
        continue

    color = COLORES.get(
        row["Estatus"],
        "blue"
    )

    avance = row.get(
        "Avance físico",
        0
    )

    popup = f"""
    <b>{row['Descripcion']}</b><br><br>

    <b>Estatus:</b> {row['Estatus']}<br>
    <b>Tipo:</b> {row['Tipo de Obra']}<br>
    <b>Monto:</b> ${row['Monto MDP']} MDP<br>
    <b>Responsable:</b> {row['Responsable obra']}<br>
    <b>Contrato:</b> {row['Contrato']}<br>

    <hr>

    <b>Colonia:</b> {row['Colonia']}<br>
    <b>Comunidad:</b> {row['Comunidad']}<br>
    <b>Distrito:</b> {row['Distrito']}<br>

    <hr>

    <b>Dirección:</b><br>
    {row['Dirección']}<br>

    <hr>

    <b>Avance:</b> {avance}%<br>

    <div style="
    width:100%;
    background:#DDD;
    height:15px;">

    <div style="
    width:{avance}%;
    background:#4CAF50;
    height:15px;">
    </div>

    </div>

    <br>

    {
     f"{int(row['Poblacion_Colonia']):,} habitantes"
     if pd.notna(row['Poblacion_Colonia'])
     else "Sin dato disponible"
     }

    """

    folium.CircleMarker(
        location=[lat, lon],
        radius=8,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        popup=folium.Popup(
            popup,
            max_width=450
        )
    ).add_to(cluster)

# ============================================================
# 18. CONTROL DE CAPAS
# ============================================================

folium.LayerControl().add_to(mapa)

# ============================================================
# 19. RENDER
# ============================================================

st_folium(
    mapa,
    width=None,
    height=850
)

# ============================================================
# 20. TABLA DE RESULTADOS
# ============================================================

st.markdown("---")

st.subheader("📋 Obras filtradas")

columnas_tabla = [

    "Descripcion",

    "Estatus",

    "Monto MDP",

    "Distrito",

    "Comunidad",

    "Colonia",

    "Avance físico"

]

tabla = df[columnas_tabla].copy()

st.dataframe(
    tabla,
    use_container_width=True,
    height=400
)


# ============================================================
# 21. DESCARGA EXCEL
# ============================================================

from io import BytesIO

buffer = BytesIO()

with pd.ExcelWriter(
    buffer,
    engine="openpyxl"
) as writer:

    tabla.to_excel(
        writer,
        sheet_name="Obras",
        index=False
    )

st.download_button(

    label="📥 Descargar Excel",

    data=buffer.getvalue(),

    file_name="obras_filtradas.xlsx",

    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

)