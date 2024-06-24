import os
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix

class DataProcessor:
    def __init__(self, local_temp_dir, local_output_dir, calibration):
        self.local_temp_dir = local_temp_dir
        self.local_output_dir = local_output_dir
        self.calibration = calibration

    def update_concatenated_files(self, pluvio):
        local_pluvio_dir = os.path.join(self.local_temp_dir, pluvio)
        annual_data = {}
        processed_files = set()
        for file in os.listdir(local_pluvio_dir):
            file_path = os.path.join(local_pluvio_dir, file)
            data = pd.read_csv(file_path, header=None, names=['Station', 'Timestamp', 'Rain', 'Wind', 'Battery'])
            data['Year'] = pd.to_datetime(data['Timestamp'], unit='s').dt.year
            processed_files.add(file)
            for year, group in data.groupby('Year'):
                if year not in annual_data:
                    annual_data[year] = []
                annual_data[year].append(group)
        for year, data_list in annual_data.items():
            concatenated_data = pd.concat(data_list).sort_values(by='Timestamp')
            output_year_dir = os.path.join(self.local_output_dir, 'concatenated', str(year))
            if not os.path.exists(output_year_dir):
                os.makedirs(output_year_dir)
            concatenated_file_path = os.path.join(output_year_dir, f'{pluvio}_concatenated_{year}.csv')
            if os.path.exists(concatenated_file_path):
                existing_data = pd.read_csv(concatenated_file_path)
                concatenated_data = pd.concat([existing_data, concatenated_data]).sort_values(by='Timestamp').drop_duplicates()
            concatenated_data.to_csv(concatenated_file_path, index=False)
        return concatenated_file_path, processed_files

    def process_data(self, file_path):
        data = pd.read_csv(file_path)
        data = self.calibration.calibrate_data(data)
        treated_file_path = file_path.replace('concatenated', 'treated')
        treated_dir = os.path.dirname(treated_file_path)
        if not os.path.exists(treated_dir):
            os.makedirs(treated_dir)
        data.to_csv(treated_file_path, index=False)
        self.create_sparse_matrix_csv(treated_file_path)

    def create_sparse_matrix_csv(self, file_path):
        data = pd.read_csv(file_path)
        data = data.drop(columns=['Wind', 'Battery'])
        timestamps = data['Timestamp'].values
        rain_values = data['Rain'].values
        stations = data['Station'].astype('category')
        sparse_matrix = csr_matrix((rain_values, (np.arange(len(timestamps)), stations.cat.codes)), shape=(len(timestamps), stations.cat.categories.size), dtype=np.float32)
        df_sparse = pd.DataFrame.sparse.from_spmatrix(sparse_matrix, index=timestamps, columns=stations.cat.categories)
        df_sparse.reset_index(inplace=True)
        df_sparse.rename(columns={'index': 'Timestamp'}, inplace=True)
        csv_file = file_path.replace('.csv', '_sparse.csv')
        df_sparse.to_csv(csv_file, index=False)

    def upload_concatenated_files(self, ftp_client):
        ftp_client.upload_files(os.path.join(self.local_output_dir, 'concatenated'))
