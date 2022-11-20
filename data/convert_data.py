import csv
import pickle
import pandas as pd
from pyproj import Transformer
import scipy

transformer = Transformer.from_crs("epsg:28992", "epsg:4326")

percentage = 2
seed = 1

mnos = ['KPN', 'T-Mobile', 'Vodafone', 'all_MNOs']
areas = ['Drenthe', 'Flevoland', 'Friesland', 'Groningen', 'Limburg', 'Overijssel', 'Utrecht', 'Zeeland',
         'Zuid-Holland', 'Gelderland', 'Noord-Brabant', 'Noord-Holland', 'Almere', 'Amsterdam', 'Enschede',
         "'s-Gravenhage", 'Elburg', 'Emmen', 'Groningen', 'Maastricht', 'Eindhoven', 'Middelburg']

for MNO in mnos:
    for area in areas:

        if MNO == 'all_MNOs':
            share = 1
        else:
            share = 0.33

        # --- users ---
        xs = pickle.load(open(f'raw_data/Users/{area}{MNO}{percentage}{share}{seed}_xs.p', 'rb'))
        ys = pickle.load(open(f'raw_data/Users/{area}{MNO}{percentage}{share}{seed}_ys.p', 'rb'))
        xs_transform, ys_transform = transformer.transform(xs, ys)



        df = pd.DataFrame(columns=['x', 'y'], index=range(len(xs_transform)))


        df['x'] = x_transform
        df['y'] = y_transform

        df.to_pickle(f'converted_data/Users/{area}{MNO}_users')

        # --- add FSP and FDP and capacity to df of users ---
        fsp = pickle.load(open(f'raw_data/FSP/{area}{MNO}{percentage}{share}{seed}_FSP.p', 'rb'))
        fdp = pickle.load(open(f'raw_data/FDP/{area}{MNO}{percentage}{share}{seed}_FDP.p', 'rb'))
        capacity = pickle.load(open(f'raw_data/Capacities/{area}{MNO}{percentage}{share}{seed}_capacities.p', 'rb'))
        snr = pickle.load(open(f'raw_data/SNR/{area}{MNO}{percentage}{share}{seed}_snrs.p', 'rb'))
        sinr = pickle.load(open(f'raw_data/SINR/{area}{MNO}{percentage}{share}{seed}_sinrs.p', 'rb'))

        snr = snr.sum(axis=1)
        sinr = sinr.sum(axis=1)

        df2 = pd.DataFrame(columns=['x', 'y', 'FDP', 'FSP', 'capacity', 'SNR', 'SINR'], index=range(len(xs_transform)))

        df2['x'] = xs_transform
        df2['y'] = ys_transform
        df2['FDP'] = fdp
        df2['FSP'] = fsp
        df2['capacity'] = capacity
        df2['SNR'] = snr
        df2['SINR'] = sinr

        df2.to_pickle(f'converted_data/Measures/{area}{MNO}')

        # --- BSs ---
        xs = pickle.load(open(f'raw_data/BSs/{area}{MNO}_xs.p', 'rb'))
        ys = pickle.load(open(f'raw_data/BSs/{area}{MNO}_ys.p', 'rb'))
        xs_transform, ys_transform = transformer.transform(xs, ys)

        #remove duplicate BS coords
        coords = []
        x_transform, y_transform = [], []
        for i, x, y in zip(range(len(xs_transform)), xs_transform, ys_transform):
            if (x,y) not in coords:
                coords.append((x, y))
                x_transform.append(x)
                y_transform.append(y)

        df3 = pd.DataFrame(columns=['x', 'y'], index=range(len(xs_transform)))

        df3['x'] = x_transform
        df3['y'] = y_transform

        df3.to_pickle(f'converted_data/BSs/{area}{MNO}_BSs')
