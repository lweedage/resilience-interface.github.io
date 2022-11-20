import pickle

import branca
import folium
import geopandas as gpd
import numpy as np
import pyproj
import shapely.ops
from folium.plugins import BeautifyIcon


def find_savename(province, fsp_or_fdp, show_BS):
    if show_BS:
        filename = f'{province}zipcodes_{fsp_or_fdp}BSs'
    else:
        filename = f'{province}zipcodes_{fsp_or_fdp}'

    if disaster:
        filename += 'correlated_failure' + str(radius_disaster)
    elif user_increase:
        filename += 'user_increase' + str(percentage_increase)
    elif random_failure:
        filename += 'isolated_failure' + str(random_p)
    return filename


def find_icon(shape, color):
    if shape == 'square':
        return BeautifyIcon(
            icon_shape='rectangle-dot',
            border_color=color,
            border_width=5,
        )
    elif shape == 'circle':
        return BeautifyIcon(
            icon_shape='circle-dot',
            border_color=color,
            border_width=5,
        )
    elif shape == 'star':
        return BeautifyIcon(
            icon='star',
            inner_icon_style=f'color:{color};font-size:5;',
            background_color='transparent',
            border_color='transparent',
        )
    else:
        return print('error')


disaster = False
user_increase = False
random_failure = False

radius_disaster = 2500  # 500, 1000, 2500, 5000
percentage_increase = 200  # 50, 100, 200
random_p = 0  # 0.05, 0.1, 0.25, 0.5


def find_name(province):
    filename = str(province)
    if disaster and radius_disaster > 0:
        filename += 'disaster' + str(radius_disaster)
    elif user_increase and percentage_increase > 0:
        filename += 'user_increase' + str(percentage_increase)
    elif random_failure and random_p > 0:
        filename += 'random' + str(random_p)
    return filename


transformer = pyproj.Transformer.from_proj(pyproj.Proj(init="epsg:28992"), pyproj.Proj(init="epsg:4326"))

style_function = lambda x: {'fillColor': '#ffffff',
                            'color': '#000000',
                            'fillOpacity': 0.1,
                            'weight': 0.1}


def find_municipalities(province):
    with open("raw_data/cities_per_province") as f:
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


provinces = ['Drenthe', 'Flevoland', 'Friesland', 'Groningen', 'Limburg', 'Overijssel', 'Utrecht', 'Zeeland',
             'Zuid-Holland', 'Gelderland', 'Noord-Brabant', 'Noord-Holland']
# provinces = ['Drenthe', 'Flevoland', 'Friesland', 'Limburg', 'Overijssel', 'Utrecht', 'Zeeland',
#              'Zuid-Holland', 'Gelderland', 'Noord-Brabant', 'Groningen']
provinces = ['Friesland']

# os.chdir(r'/home/lotte/PycharmProjects/Disaster Resilience - interface')
show_BS = False

for fsp_or_fdp in ['FSP', 'FDP']:
    for show_BS in [False]:
        for province in provinces:
            region = pickle.load(open(f'raw_data/Regions/{province}region.p', 'rb'))
            centre = gpd.GeoSeries(region).centroid
            y, x = transformer.transform(centre.x, centre.y)
            center = (x[0], y[0])
            # initialize the map
            Netherlands = [52.23212312992836, 5.409836285734089]
            m = folium.Map(location=(x[0], y[0]), zoom_start=10, tiles=None, prefer_canvas=True)  # , crs="EPSG:4326")
            base_m = folium.FeatureGroup(name='BaseMap', overlay=True, control=False)
            folium.TileLayer(tiles='OpenStreetMap').add_to(base_m)
            base_m.add_to(m)

            df = gpd.read_file('raw_data/zip_codes.shp')

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
            filename = find_name(province)
            print(filename)
            tmobile_measures = gpd.read_file(f"converted_data/Measures/{filename}T-Mobile_zipcodes.shp")
            kpn_measures = gpd.read_file(f"converted_data/Measures/{filename}KPN_zipcodes.shp")
            vodafone_measures = gpd.read_file(f"converted_data/Measures/{filename}Vodafone_zipcodes.shp")
            allMNO_measures = gpd.read_file(f"converted_data/Measures/{filename}all_MNOs_zipcodes.shp")
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
                threshold_scale = np.arange(0, maximum + 1e-6 + (maximum + 2e-6) / 8, (maximum + 1e-6) / 8)

            else:
                maximum = 1
                minimum = 1
                for measure in all_measures:
                    if min(measure[fsp_or_fdp].astype('float')) < minimum:
                        minimum = min(measure[fsp_or_fdp].astype('float')) - 0.1
                threshold_scale = np.arange(minimum - 1e-6, 1 + (1 - minimum + 2e-6) / 8, (1 - minimum + 1e-6) / 8)
                colormap = 'BuGn'


            # minimum, maximum = -0.01, 1.1
            for measures, fg, provider in zip(all_measures, feature_groups, providers):

                if show_BS:
                    # plot Base Stations
                    tmobile_bs = pickle.load(open(f"converted_data/BSs/{province}T-Mobile_BSs", "rb"))
                    kpn_bs = pickle.load(open(f"converted_data/BSs/{province}KPN_BSs", "rb"))
                    vodafone_bs = pickle.load(open(f"converted_data/BSs/{province}Vodafone_BSs", "rb"))
                    allMNO_bs = pickle.load(open(f"converted_data/BSs/{province}all_MNOs_BSs", "rb"))

                    markers = {'LTE': 'circle', '5G NR': 'square', 'UMTS': 'star'}

                    for i in range(0, len(tmobile_bs)):
                        y, x, radio = tmobile_bs.get('x')[i], tmobile_bs.get('y')[i], tmobile_bs.get('radio')[i]
                        folium.Marker([x, y], tooltip=tmobile_bs.get('radio')[i],
                                      icon=find_icon(markers[radio], 'green')).add_to(fg_tmobile)
                        folium.Marker([x, y], tooltip=str('MNO-1, ' + tmobile_bs.get('radio')[i]),
                                      icon=find_icon(markers[radio], 'green')).add_to(fg_allMNO)

                    for i in range(0, len(kpn_bs)):
                        y, x, radio = kpn_bs.get('x')[i], kpn_bs.get('y')[i], kpn_bs.get('radio')[i]
                        folium.Marker([x, y], tooltip=kpn_bs.get('radio')[i],
                                      icon=find_icon(markers[radio], 'red')).add_to(fg_kpn)
                        folium.Marker([x, y], tooltip=str('MNO-2, ' + kpn_bs.get('radio')[i]),
                                      icon=find_icon(markers[radio], 'red')).add_to(fg_allMNO)

                    for i in range(0, len(vodafone_bs)):
                        y, x, radio = vodafone_bs.get('x')[i], vodafone_bs.get('y')[i], vodafone_bs.get('radio')[i]
                        folium.Marker([x, y], tooltip=vodafone_bs.get('radio')[i],
                                      icon=find_icon(markers[radio], 'blue')).add_to(fg_vodafone)
                        folium.Marker([x, y], tooltip=str('MNO-3, ' + vodafone_bs.get('radio')[i]),
                                      icon=find_icon(markers[radio], 'blue')).add_to(fg_allMNO)

                measures.insert(0, 'ID', range(0, len(measures)))
                measures['ID'] = measures['ID'].astype('str')
                measures['FSP'] = measures['FSP'].astype('float')
                measures['FDP'] = measures['FDP'].astype('float')

                measures.crs = "EPSG:4326"
                for i, row in measures.iterrows():
                    if str(row[fsp_or_fdp]) == "nan":
                        measures = measures.drop(index=i, axis=0)
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
                    bins=threshold_scale
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

            if disaster:
                folium.Circle(location=center, color='red', fill = True, opacity = 0.5, fill_opacity = 0.3, radius=radius_disaster).add_to(m)

            if fsp_or_fdp == 'FSP':
                colormap = branca.colormap.linear.BuGn_03.scale(0, 1)
            else:
                colormap = branca.colormap.linear.GnBu_03.scale(0, 1)

            colormap = colormap.to_step(index=threshold_scale)
            colormap.caption = fsp_or_fdp
            colormap.add_to(m)

            filename = find_savename(province, fsp_or_fdp, show_BS)

            folium.LayerControl(collapsed=False).add_to(m)

            m.save(f'html/{filename}.html')
