import os
from glob import glob
import pandas as pd
from datetime import datetime

class RainfallCumulMatrix:
    def __init__(self, station_list, coord_geo, input_dir, output_dir, output_name):
        self.station_list = station_list
        self.coord_geo = coord_geo
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.output_name = output_name
        self.dict_dat = {
            'site': self.station_list,
            'lon': self.coord_geo[0],
            'lat': self.coord_geo[1],
            'P72h': [],
            'P48h': [],
            'P24h': [],
            'P12h': [],
            'P4h': [],
            'P2h': [],
            'P1h': [],
            'P30min': [],
            'P15min': [],
            'P10min': [],
            'P5min': [],
        }

    def calculate_cumulative_rainfall(self, start_timestamp):
        data_list = []

        for station in self.station_list:
            for parent_dir, dirs, files in os.walk(self.input_dir):
                folders = dirs
                break

            for folder in folders:
                list_txt = glob(os.path.join(self.input_dir, folder) + '/*.csv')
                for file in list_txt:
                    with open(file, 'rt') as f:
                        data_in = pd.read_csv(f, sep=",", header=None, skiprows=1, low_memory=False)

                    if station == file.split(os.sep)[-1].split(".")[0].split("_")[0]:
                        # Filtrer les données à partir du timestamp de début
                        data_in = data_in[data_in[1] >= start_timestamp]

                        # Check for missing data points
                        if len(data_in) >= 4320:
                            somme_72H = sum(data_in[1][-4320:]).__round__(1)
                        else:
                            somme_72H = None

                        if len(data_in) >= 2880:
                            somme_48H = sum(data_in[1][-2880:]).__round__(1)
                        else:
                            somme_48H = None

                        if len(data_in) >= 1440:
                            somme_24H = sum(data_in[1][-1440:]).__round__(1)
                        else:
                            somme_24H = None

                        if len(data_in) >= 720:
                            somme_12H = sum(data_in[1][-720:]).__round__(1)
                        else:
                            somme_12H = None

                        if len(data_in) >= 240:
                            somme_4H = sum(data_in[1][-240:]).__round__(1)
                        else:
                            somme_4H = None

                        if len(data_in) >= 120:
                            somme_2H = sum(data_in[1][-120:]).__round__(1)
                        else:
                            somme_2H = None

                        if len(data_in) >= 60:
                            somme_1H = sum(data_in[1][-60:]).__round__(1)
                        else:
                            somme_1H = None

                        if len(data_in) >= 30:
                            somme_30Min = sum(data_in[1][-30:]).__round__(1)
                        else:
                            somme_30Min = None

                        if len(data_in) >= 15:
                            somme_15Min = sum(data_in[1][-15:]).__round__(1)
                        else:
                            somme_15Min = None

                        if len(data_in) >= 10:
                            somme_10Min = sum(data_in[1][-10:]).__round__(1)
                        else:
                            somme_10Min = None

                        if len(data_in) >= 5:
                            somme_5Min = sum(data_in[1][-5:]).__round__(1)
                        else:
                            somme_5Min = None

                        # Add data to dictionary if no None values
                        if all(value is not None for value in [somme_72H, somme_48H, somme_24H, somme_12H, somme_4H, somme_2H, somme_1H, somme_30Min, somme_15Min, somme_10Min, somme_5Min]):
                            data_list.append({
                                'site': station,
                                'lon': self.dict_dat['lon'][self.station_list.index(station)],
                                'lat': self.dict_dat['lat'][self.station_list.index(station)],
                                'P72h': somme_72H,
                                'P48h': somme_48H,
                                'P24h': somme_24H,
                                'P12h': somme_12H,
                                'P4h': somme_4H,
                                'P2h': somme_2H,
                                'P1h': somme_1H,
                                'P30min': somme_30Min,
                                'P15min': somme_15Min,
                                'P10min': somme_10Min,
                                'P5min': somme_5Min
                            })

        # Construct the DataFrame using the list of dictionaries
        df = pd.DataFrame(data_list)

        # Export the DataFrame to a CSV file
        output_file_path = os.path.join(self.output_dir, self.output_name + datetime.now().strftime('%Y%m%d%H%M') + '.csv')
        if os.path.exists(output_file_path):
            os.remove(output_file_path)
        df.to_csv(output_file_path, index=False)

        print(f'Cumulative rainfall matrix saved to {output_file_path}')
