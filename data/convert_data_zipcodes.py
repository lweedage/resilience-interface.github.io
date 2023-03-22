import csv
import pickle
import os
import matplotlib.pyplot as plt
import pandas as pd
import shapely.geometry
from shapely.geometry import MultiPolygon
from shapely.ops import transform
import scipy
import geopandas as gpd
import pyproj
from shapely.ops import unary_union
from shapely.geometry import Point
import matplotlib
import numpy as np
import pylab
# matplotlib.use('TkAgg')

disaster = True
user_increase = False
random_failure = False

radius_disaster = 2500 #500, 1000, 2500, 5000
percentage_increase = 200 #50, 100, 200
random_p = 0.1 #0.05, 0.1, 0.25, 0.5

def find_name(filename):
    if disaster:
        filename += 'disaster' + str(radius_disaster)
    elif user_increase:
        filename += 'user_increase' + str(percentage_increase)
    elif random_failure:
        filename += 'random' + str(random_p)
    return filename

def find_savename(province, fsp_or_fdp):
    filename = f'{province}{fsp_or_fdp}zipcodes'
    if disaster:
        filename += 'correlated_failure' + str(radius_disaster)
    elif user_increase:
        filename += 'user_increase' + str(percentage_increase)
    elif random_failure:
        filename += 'isolated_failure' + str(random_p)
    return filename

params = {'legend.fontsize': 'x-large',
         'axes.labelsize': 'x-large',
         'axes.titlesize':'x-large',
         'xtick.labelsize':'x-large',
         'ytick.labelsize':'x-large',
        'lines.markersize': 8}#,
          # 'figure.autolayout': True}
pylab.rcParams.update(params)

colors = ['#904C77', '#E49AB0', '#ECB8A5', '#96ACB7', '#957D95'] * 100


transformer = pyproj.Transformer.from_proj(pyproj.Proj(init = "epsg:28992"), pyproj.Proj(init="epsg:4326"))

percentage = 2
seed = 1
max_iterations = 5

mnos = ['KPN', 'T-Mobile', 'Vodafone', 'all_MNOs']
providers = ['MNO-1', 'MNO-2', 'MNO-3', 'National roaming']

areas =['Drenthe', 'Flevoland', 'Friesland', 'Groningen', 'Limburg', 'Overijssel', 'Utrecht', 'Zeeland',
         'Zuid-Holland', 'Gelderland', 'Noord-Brabant', 'Noord-Holland']
provinces =['Drenthe', 'Flevoland', 'Friesland', 'Groningen', 'Limburg', 'Overijssel', 'Utrecht', 'Zeeland',
         'Zuid-Holland', 'Gelderland', 'Noord-Brabant', 'Noord-Holland']

areas = ['Drenthe']
provinces = areas

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

# --- zip code level ----

zip_codes = gpd.read_file('raw_data/zip_codes.shp')

for province in provinces:
    print(province)
    areas = find_municipalities(province)
    data_figureFSP = dict()
    data_figureFDP = dict()

    for MNO in mnos:
        filename = f'{province}'
        filename = find_name(filename)
        print(filename)
        if not os.path.exists(f'converted_data/Measures/{filename}{MNO}_zipcodes.shp'):
            print(f'{filename}{MNO} does not exist yet.')
            if MNO == 'all_MNOs':
                share = 1
            else:
                share = 0.33

            df = gpd.GeoDataFrame(columns=['area', 'FSP', 'FDP'])
            # df['area'] = zip_codes['postcode']
            geom = []
            zipcodes = []

            for area in areas:
                print(area)
                zip_code_region_data = zip_codes[zip_codes['municipali'].isin([area])]
                df2 = gpd.GeoDataFrame(columns=['area', 'FSP', 'FDP'])

                df2['area'] = zip_code_region_data['postcode']
                df2['FSP'] = [1 for i in range(len(df2))]
                df2['FDP'] = [0 for i in range(len(df2))]

                for zipcode in zip_code_region_data['postcode']:
                    new_data = zip_code_region_data[zip_code_region_data['postcode'].isin([zipcode])]

                    FSP, FDP = [], []
                    # region = gpd.GeoSeries(unary_union(new_data['geometry']))
                    region = new_data.geometry.values
                    region = region.buffer(10).simplify(tolerance=200)
                    region = transform(transformer.transform, region[0])
                    geom.append(region)
                    zipcodes.append(zipcode)
                    # df2[df2['area'] == zipcode, 'geometry'] = region
                    # print(df2)

                    for seed in range(max_iterations):
                        # --- add FSP and FDP and capacity to df of users ---
                        filename1 = f'{province}{MNO}{percentage}{share}'
                        filename = find_name(filename1)
                        filename += str(seed)

                        if user_increase:
                            filename1 = filename
                        else:
                            filename1 += str(seed)

                        fsp = pickle.load(open(f'raw_data/FDPFSP/{filename}_FSP.p', 'rb'))
                        fdp = pickle.load(open(f'raw_data/FDPFSP/{filename}_FDP.p', 'rb'))

                        xs = pickle.load(open(f'raw_data/Users/{filename1}_xs.p', 'rb'))
                        ys = pickle.load(open(f'raw_data/Users/{filename1}_ys.p', 'rb'))
                        x, y = transformer.transform(xs, ys)

                        for i in range(len(x)):
                            user = Point(x[i], y[i])
                            if region.contains(user):
                                FSP.append(fsp[i])
                                FDP.append(fdp[i])

                    # print(df)

                    condition = df2['area'] == zipcode

                    df2.loc[condition, 'FSP'] = sum(FSP)/max(1, len(FSP))
                    df2.loc[condition, 'FDP'] = sum(FDP)/max(1, len(FDP))

                df = pd.concat([df, df2])

                data_figureFSP[MNO] = df['FSP'].tolist()
                data_figureFDP[MNO] = df['FDP'].tolist()

            df = df.set_geometry(geom)
            filename = f'{province}'
            filename = find_name(filename)
            df.to_file(f'converted_data/Measures/{filename}{MNO}_zipcodes.shp')

            boxplot_data = data_figureFSP.values()

            fig, ax = plt.subplots()
            bplot = plt.boxplot(boxplot_data, patch_artist=True, showfliers = False)
            for patch, color in zip(bplot['boxes'], colors[:4]):
                patch.set_facecolor(color)
            plt.xticks(np.arange(1, 5), providers)
            plt.ylabel('FSP')
            filename = find_savename(province, 'FSP')

            plt.savefig(f'figures/{filename}.png', dpi = 1000)

            boxplot_data = data_figureFDP.values()

            fig, ax = plt.subplots()
            bplot = plt.boxplot(boxplot_data, patch_artist=True, showfliers = False)
            for patch, color in zip(bplot['boxes'], colors[:4]):
                patch.set_facecolor(color)
            plt.xticks(np.arange(1, 5), providers)
            plt.ylabel('FDP')
            filename = find_savename(province, 'FDP')
            plt.savefig(f'figures/{filename}.png', dpi = 1000)
