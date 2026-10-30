# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 23:40:16 2026

@author: germa
"""

import geopandas as gpd

# ===========================
# RUTAS ORIGINALES
# ===========================

ruta_colonias = r"capas\ColoniasGDL.shp"

ruta_comunidades = r"capas\comunidades_gdl_v5.gpkg"

ruta_distritos = r"capas\DistritoLocalSept2022.shp"

# ===========================
# LEER ARCHIVOS
# ===========================

colonias = gpd.read_file(ruta_colonias)

comunidades = gpd.read_file(ruta_comunidades)

distritos = gpd.read_file(ruta_distritos)

# Solo Guadalajara

distritos = distritos[
    distritos["DISTRITO_L"].isin([8,9,11,13])
]

# ===========================
# CONVERTIR A WGS84
# ===========================

colonias = colonias.to_crs(4326)

comunidades = comunidades.to_crs(4326)

distritos = distritos.to_crs(4326)

# ===========================
# EXPORTAR
# ===========================

colonias.to_file(
    "capas/colonias.geojson",
    driver="GeoJSON"
)

comunidades.to_file(
    "capas/comunidades.geojson",
    driver="GeoJSON"
)

distritos.to_file(
    "capas/distritos.geojson",
    driver="GeoJSON"
)

print("GeoJSON generados correctamente")
