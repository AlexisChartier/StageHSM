import os
import pandas as pd
import numpy as np
from datetime import datetime
from scipy.sparse import csr_matrix

# Répertoires locaux
LOCAL_DIR = '/Users/david/Desktop/StageHSM/temp/Hydropolis/'  # Remplacez par le chemin local de vos données Hydropolis
OUTPUT_DIR = '/Users/david/Desktop/StageHSM/Processed/'       # Remplacez par le chemin local de vos fichiers de sortie
CALIB_FILE = '/Users/david/Desktop/StageHSM/scripts/calib.csv'  # Remplacez par le chemin local de votre fichier de calibration

# Pluviomètre spécifique à traiter
PLUVIOS = ['Hydropolis']

# Fonction pour concaténer les fichiers par année pour chaque pluviomètre
def concatenate_files_by_year(local_dir, pluvios):
    concatenated_files = []
    for pluvio in pluvios:
        local_pluvio_dir = os.path.join(local_dir)
        annual_data = {}

        for file in os.listdir(local_pluvio_dir):
            print(file)
            file_path = os.path.join(local_pluvio_dir, file)
            data = pd.read_csv(file_path, header=None, names=['Station', 'Timestamp', 'Rain', 'Wind', 'Battery'])
            data['Year'] = pd.to_datetime(data['Timestamp'], unit='s').dt.year

            for year, group in data.groupby('Year'):
                if year not in annual_data:
                    annual_data[year] = []
                annual_data[year].append(group)

        for year, data_list in annual_data.items():
            concatenated_data = pd.concat(data_list).sort_values(by='Timestamp')
            concatenated_data = concatenated_data.drop(columns=['ReadableDate'], errors='ignore')
            output_year_dir = os.path.join(OUTPUT_DIR, 'concatenated', str(year))
            if not os.path.exists(output_year_dir):
                os.makedirs(output_year_dir)
            concatenated_file_path = os.path.join(output_year_dir, f'{pluvio}_concatenated_{year}.csv')
            concatenated_data.to_csv(concatenated_file_path, index=False)
            concatenated_files.append(concatenated_file_path)

    return concatenated_files

# Fonction pour lire le fichier de calibration
def read_calibration_file(calib_file):
    calib_params = pd.read_csv(calib_file)
    calibration = {}
    for _, row in calib_params.iterrows():
        station = row['pluvio']
        a = row['a']
        b = row['b']
        c = row['c']
        calibration[station] = (a, b, c)
    return calibration

# Fonction pour calibrer les données
def calibrate_data(data, calibration):
    station = data['Station'].iloc[0]
    if station in calibration:
        a, b, c = calibration[station]
        data['Rain'] = a * data['Rain'] ** 2 + b * data['Rain'] + c
    return data

# Fonction pour créer des matrices creuses et les sauvegarder au format CSV
def create_sparse_matrix_csv(file_path):
    data = pd.read_csv(file_path)
    # Suppression des colonnes de vent et de batterie
    data = data.drop(columns=['Wind', 'Battery'])
    timestamps = data['Timestamp'].values
    rain_values = data['Rain'].values
    stations = data['Station'].astype('category')

    # Création de la matrice creuse
    sparse_matrix = csr_matrix((rain_values, (np.arange(len(timestamps)), stations.cat.codes)), shape=(len(timestamps), stations.cat.categories.size), dtype=np.float32)

    # Convertir la matrice creuse en DataFrame pour sauvegarde en CSV
    df_sparse = pd.DataFrame.sparse.from_spmatrix(sparse_matrix, index=timestamps, columns=stations.cat.categories)
    df_sparse.reset_index(inplace=True)
    df_sparse.rename(columns={'index': 'Timestamp'}, inplace=True)

    # Sauvegarder au format CSV
    csv_file = file_path.replace('.csv', '_sparse.csv')
    df_sparse.to_csv(csv_file, index=False)

# Fonction principale
def main():
    # Concaténation des fichiers par année pour chaque pluviomètre
    concatenated_files = concatenate_files_by_year(LOCAL_DIR, PLUVIOS)

    # Lecture du fichier de calibration
    calibration = read_calibration_file(CALIB_FILE)

    # Traiter les fichiers concaténés
    for file_path in concatenated_files:
        data = pd.read_csv(file_path)
        data = calibrate_data(data, calibration)
        treated_file_path = file_path.replace('concatenated', 'treated')
        treated_dir = os.path.dirname(treated_file_path)
        if not os.path.exists(treated_dir):
            os.makedirs(treated_dir)
        data.to_csv(treated_file_path, index=False)
        # Création des matrices creuses et sauvegarde au format CSV
        create_sparse_matrix_csv(treated_file_path)

if __name__ == "__main__":
    main()
