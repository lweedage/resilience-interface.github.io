import pickle
import pickle

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pylab
import pyproj
from shapely.geometry import Point
from shapely.ops import transform
from shapely.ops import unary_union

matplotlib.use('TkAgg')

params = {'legend.fontsize': 'x-large',
          'axes.labelsize': 'x-large',
          'axes.titlesize': 'x-large',
          'xtick.labelsize': 'x-large',
          'ytick.labelsize': 'x-large',
          'lines.markersize': 8}  # ,
# 'figure.autolayout': True}
pylab.rcParams.update(params)

colors = ['#904C77', '#E49AB0', '#ECB8A5', '#96ACB7', '#957D95'] * 100

transformer = pyproj.Transformer.from_proj(pyproj.Proj(init="epsg:28992"), pyproj.Proj(init="epsg:4326"))

percentage = 2
max_iterations = 5

disaster = False
user_increase = False
random_failure = False

radius_disaster = 100  # 100, 500, 1000, 2500
percentage_increase = 50  # 50, 100, 200
random_p = 0.1  # 0.05, 0.1, 0.25, 0.5

mnos = ['KPN', 'T-Mobile', 'Vodafone', 'all_MNOs']
providers = ['MNO-1', 'MNO-2', 'MNO-3', 'National roaming']

# mnos, providers = ['all_MNOs'], ['Natioanl roaming']

areas = ['Drenthe', 'Flevoland', 'Friesland', 'Groningen', 'Limburg', 'Overijssel', 'Utrecht', 'Zeeland',
         'Zuid-Holland', 'Gelderland', 'Noord-Brabant', 'Noord-Holland']
provinces = ['Drenthe', 'Flevoland', 'Friesland', 'Groningen', 'Limburg', 'Overijssel', 'Utrecht', 'Zeeland',
             'Zuid-Holland', 'Gelderland', 'Noord-Brabant', 'Noord-Holland']


data_figureFSP = dict()
data_figureFDP = dict()
for MNO in mnos:
    df = gpd.GeoDataFrame(columns=['area', 'FSP', 'FDP'])
    df['area'] = areas
    geom = []
    for area in areas:
        region = pickle.load(open(f'raw_data/Regions/{area}region.p', 'rb'))
        region = region.geometry.values
        region = transform(transformer.transform, region[0])
        geom.append(region)

        if MNO == 'all_MNOs':
            share = 1
        else:
            share = 0.33

        # --- add FSP and FDP ---
        filename = f'{area}{MNO}{percentage}{share}'
        if disaster:
            filename += 'disaster' + str(radius_disaster)
        elif user_increase:
            filename += 'user_increase' + str(percentage_increase)
        elif random_failure:
            filename += 'random' + str(random_p)

        filename += str(max_iterations)

        fsp = pickle.load(open(f'raw_data/FSP/{filename}_totalfsp.p', 'rb'))
        fdp = pickle.load(open(f'raw_data/FDP/{filename}_totalfdp.p', 'rb'))

        fsp = sum(fsp) / len(fsp)
        fdp = sum(fdp) / len(fdp)

        condition = df['area'] == area
        df.loc[condition, 'FSP'] = fsp
        df.loc[condition, 'FDP'] = fdp

        # --- BSs ---
        xs = pickle.load(open(f'raw_data/BSs/{area}{MNO}_xs.p', 'rb'))
        ys = pickle.load(open(f'raw_data/BSs/{area}{MNO}_ys.p', 'rb'))
        radios = pickle.load(open(f'raw_data/BSs/{area}{MNO}_radios.p', 'rb'))
        xs_transform, ys_transform = transformer.transform(xs, ys)

        # remove duplicate BS coords
        # coords = []
        # radio = []
        # x_transform, y_transform = [], []
        # for i, x, y in zip(range(len(xs_transform)), xs_transform, ys_transform):
        #     if (x,y) not in coords:
        #         coords.append((x, y))
        #         x_transform.append(x)
        #         y_transform.append(y)
        #         radio.append(radios[i])

        df3 = pd.DataFrame(columns=['x', 'y', 'radio'], index=range(len(xs_transform)))

        df3['x'] = xs_transform
        df3['y'] = ys_transform
        df3['radio'] = radios

        filename = f'{area}{MNO}'
        if disaster:
            filename += 'disaster' + str(radius_disaster)
        df3.to_pickle(f'converted_data/BSs/{filename}_BSs')

    df = df.set_geometry(geom)

    filename = f'{MNO}'
    if disaster:
        filename += 'disaster' + str(radius_disaster)
    elif user_increase:
        filename += 'user_increase' + str(percentage_increase)
    elif random_failure:
        filename += 'random' + str(random_p)
    df.to_file(f'converted_data/Measures/{filename}_provinces.shp')
    data_figureFSP[MNO] = df['FSP'].tolist()
    data_figureFDP[MNO] = df['FDP'].tolist()

boxplot_data = data_figureFSP.values()

fig, ax = plt.subplots()
bplot = plt.boxplot(boxplot_data, patch_artist=True, showfliers=False)
for patch, color in zip(bplot['boxes'], colors[:4]):
    patch.set_facecolor(color)
plt.xticks(np.arange(1, 5), providers)
plt.ylabel('FSP')
if disaster:
    plt.savefig(f'figures/FSPprovincesdisaster{radius_disaster}.png', dpi=1000)
elif user_increase:
    plt.savefig(f'figures/FSPprovincesuser_increase{percentage_increase}.png', dpi=1000)
elif random_failure:
    plt.savefig(f'figures/FSPprovincesrandom{random_p}.png', dpi=1000)
else:
    plt.savefig(f'figures/FSPprovinces.png', dpi=1000)
boxplot_data = data_figureFDP.values()

fig, ax = plt.subplots()
bplot = plt.boxplot(boxplot_data, patch_artist=True, showfliers=False)
for patch, color in zip(bplot['boxes'], colors[:4]):
    patch.set_facecolor(color)
plt.xticks(np.arange(1, 5), providers)
plt.ylabel('FDP')
if disaster:
    plt.savefig(f'figures/FDPprovincesdisaster{radius_disaster}.png', dpi=1000)
elif user_increase:
    plt.savefig(f'figures/FDPprovincesuser_increase{percentage_increase}.png', dpi=1000)
elif random_failure:
    plt.savefig(f'figures/FDPprovincesrandom{random_p}.png', dpi=1000)
else:
    plt.savefig(f'figures/FDPprovinces.png', dpi=1000)


# --- municipality level ----
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


zip_codes = gpd.read_file('raw_data/zip_codes.shp')

data_figureFSP = dict()
data_figureFDP = dict()
for MNO in mnos:
    if MNO == 'all_MNOs':
        share = 1
    else:
        share = 0.33

    df = gpd.GeoDataFrame(columns=['area', 'FSP', 'FDP'])

    areas = []

    for i in provinces:
        for x in find_municipalities(i):
            areas.append(x)

    df['area'] = areas  # find_municipalities('Netherlands')

    geom = []
    for province in provinces:
        areas = find_municipalities(province)
        print(MNO, province)
        for area in areas:
            FSP, FDP = [], []
            zip_code_region_data = zip_codes[zip_codes['municipali'].isin([area])]
            region = gpd.GeoSeries(unary_union(zip_code_region_data['geometry'].buffer(50)))
            region = region.simplify(tolerance=200)
            region = region.geometry.values
            region = transform(transformer.transform, region[0])
            # df[df['area'] == area].set_geometry(gpd.GeoSeries(region))
            geom.append(region)

            for seed in range(max_iterations):
                # --- add FSP and FDP and capacity to df of users ---
                filename = f'{province}{MNO}{percentage}{share}'
                if disaster:
                    filename += 'disaster' + str(radius_disaster)
                elif user_increase:
                    filename += 'user_increase' + str(percentage_increase)
                elif random_failure:
                    filename += 'random' + str(random_p)
                filename += str(seed)

                fsp = pickle.load(open(f'raw_data/FSP/{filename}_FSP.p', 'rb'))
                fdp = pickle.load(open(f'raw_data/FDP/{filename}_FDP.p', 'rb'))

                xs = pickle.load(open(f'raw_data/Users/{filename}_xs.p', 'rb'))
                ys = pickle.load(open(f'raw_data/Users/{filename}_ys.p', 'rb'))
                x, y = transformer.transform(xs, ys)


                print(len(x), len(fsp))
                for i in range(len(x)):
                    user = Point(x[i], y[i])
                    if region.buffer(0).contains(user):
                        FSP.append(fsp[i])
                        FDP.append(fdp[i])

            condition = df['area'] == area
            df.loc[condition, 'FSP'] = sum(FSP) / max(1, len(FSP))
            df.loc[condition, 'FDP'] = sum(FDP) / max(1, len(FDP))
        data_figureFSP[MNO] = df['FSP'].tolist()
        data_figureFDP[MNO] = df['FDP'].tolist()

    df = df.set_geometry(geom)
    df.to_file(f'converted_data/Measures/{MNO}_municipalities.shp')

boxplot_data = data_figureFSP.values()

fig, ax = plt.subplots()
bplot = plt.boxplot(boxplot_data, patch_artist=True, showfliers=False)
for patch, color in zip(bplot['boxes'], colors[:4]):
    patch.set_facecolor(color)
plt.xticks(np.arange(1, 5), providers)
plt.ylabel('FSP')

if disaster:
    plt.savefig(f'figures/FSPmunicipalitiesdisaster{radius_disaster}.png', dpi=1000)
elif user_increase:
    plt.savefig(f'figures/FSPmunicipalitiesuser_increase{percentage_increase}.png', dpi=1000)
elif random_failure:
    plt.savefig(f'figures/FSPmunicipalitiesrandom{random_p}.png', dpi=1000)
else:
    plt.savefig(f'figures/FSPmunicipalities.png', dpi=1000)

boxplot_data = data_figureFDP.values()

fig, ax = plt.subplots()
bplot = plt.boxplot(boxplot_data, patch_artist=True, showfliers=False)
for patch, color in zip(bplot['boxes'], colors[:4]):
    patch.set_facecolor(color)
plt.xticks(np.arange(1, 5), providers)
plt.ylabel('FDP')

if disaster:
    plt.savefig(f'figures/FDPmunicipalitiesdisaster{radius_disaster}.png', dpi=1000)
elif user_increase:
    plt.savefig(f'figures/FDPmunicipalitiesuser_increase{percentage_increase}.png', dpi=1000)
elif random_failure:
    plt.savefig(f'figures/FDPmunicipalitiesrandom{random_p}.png', dpi=1000)
else:
    plt.savefig(f'figures/FDPmunicipalities.png', dpi=1000)
