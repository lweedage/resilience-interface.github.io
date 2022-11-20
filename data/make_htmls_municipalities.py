import os

import branca
import folium
import geopandas as gpd
import numpy as np
from pyproj import Transformer

style_function = lambda x: {'fillColor': '#ffffff',
                            'color': '#000000',
                            'fillOpacity': 0.1,
                            'weight': 0.1}


def find_municipalities(province):
    with open("data/raw_data/cities_per_province") as f:
        data = f.read()
        data = data.split('\n')
    if province == 'Netherlands':
        print(province)
        cities = []
        for line in data:
            line = line.split(':')
            for city in line[1].split(','):
                cities.append(city)
        return cities
    else:
        for line in data:
            line = line.split(':')
            if line[0] == province:
                return line[1].split(',')


transformer = Transformer.from_crs("epsg:28992", "epsg:4326")

provinces = ['Drenthe', 'Flevoland', 'Friesland', 'Groningen', 'Limburg', 'Overijssel', 'Utrecht', 'Zeeland',
             'Zuid-Holland', 'Gelderland', 'Noord-Brabant', 'Noord-Holland']

os.chdir(r'/home/lotte/PycharmProjects/Disaster Resilience - interface')

for fsp_or_fdp in ['FDP', 'FSP']:
    # initialize the map
    netherlands = [52.23212312992836, 5.409836285734089]

    df = gpd.read_file('data/raw_data/zip_codes.shp')

    m = folium.Map(location=netherlands, zoom_start=8, tiles=None)
    base_m = folium.FeatureGroup(name='BaseMap', overlay=True, control=False)
    folium.TileLayer(tiles='OpenStreetMap').add_to(base_m)
    base_m.add_to(m)

    # Make group and subgroups
    fg_kpn = folium.FeatureGroup(name='MNO 1', overlay=False)
    m.add_child(fg_kpn)

    fg_tmobile = folium.FeatureGroup(name='MNO 2', overlay=False)
    m.add_child(fg_tmobile)

    fg_vodafone = folium.FeatureGroup(name='MNO 3', overlay=False)
    m.add_child(fg_vodafone)

    fg_allMNO = folium.FeatureGroup(name='National roaming', overlay=False)
    m.add_child(fg_allMNO)

    # load measures
    tmobile_measures = gpd.read_file(f"data/converted_data/Measures/T-Mobile_municipalities.shp")
    kpn_measures = gpd.read_file("data/converted_data/Measures/KPN_municipalities.shp")
    vodafone_measures = gpd.read_file("data/converted_data/Measures/Vodafone_municipalities.shp")
    allMNO_measures = gpd.read_file("data/converted_data/Measures/all_MNOs_municipalities.shp")

    all_measures = [tmobile_measures, kpn_measures, vodafone_measures, allMNO_measures]
    feature_groups = [fg_tmobile, fg_kpn, fg_vodafone, fg_allMNO]

    providers = ['T-Mobile', 'KPN', 'Vodafone', 'National roaming']

    if fsp_or_fdp == 'FDP':
        minimum = 0
        maximum = 0
        for measure in all_measures:
            if max(measure[fsp_or_fdp].astype('float')) > maximum:
                maximum = max(measure[fsp_or_fdp].astype('float'))
        colormap = 'GnBu'
        threshold_scale = np.arange(0, maximum + 1e-6 + (maximum + 1e-6) / 8, (maximum + 1e-6) / 8)

    else:
        maximum = 1
        minimum = 1
        for measure in all_measures:
            if min(measure[fsp_or_fdp].astype('float')) < minimum:
                minimum = min(measure[fsp_or_fdp].astype('float')) - 0.1
        colormap = 'BuGn'
        threshold_scale = np.arange(min(0, minimum - 1e-6), 1 + (1 - minimum + 1e-6) / 8, (1 - minimum + 1e-6) / 8)

    for measures, fg, provider in zip(all_measures, feature_groups, providers):
        measures.insert(0, 'ID', range(0, len(measures)))
        measures['ID'] = measures['ID'].astype('str')
        measures['FSP'] = measures['FSP'].astype('float')
        measures['FDP'] = measures['FDP'].astype('float')

        measures.crs = "EPSG:4326"
        chloropleth = folium.Choropleth(
            geo_data=measures,
            name='Choropleth',
            data=measures,
            columns=['ID', fsp_or_fdp],
            key_on='feature.properties.ID',
            fill_color=colormap,
            fill_opacity=0.5,
            line_opacity=1,
            legend_name=fsp_or_fdp,
            highlight=True,
            threshold_scale=threshold_scale
        ).geojson.add_to(fg)

        folium.features.GeoJson(
            data=measures,
            name=provider,
            smooth_factor=2,
            style_function=style_function,
            tooltip=folium.features.GeoJsonTooltip(
                fields=['area', fsp_or_fdp],
                aliases=['Zip code: ', fsp_or_fdp + ': '],
                localize=True,
                sticky=False,
                labels=True,
                style="""
                            background-color: #F0EFEF;
                            border: 2px solid black;
                            border-radius: 3px;
                            box-shadow: 3px;
                        """,
                max_width=800, ),
            highlight_function=lambda x: {'weight': 3, 'fillColor': 'grey'},
        ).add_to(chloropleth)

    if fsp_or_fdp == 'FSP':
        colormap = branca.colormap.linear.BuGn_03.scale(0, 1)
    else:
        colormap = branca.colormap.linear.GnBu_03.scale(0, 1)

    colormap = colormap.to_step(index=threshold_scale)
    colormap.caption = fsp_or_fdp
    colormap.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    m.save(f'data/html/municipalities_{fsp_or_fdp}.html')
