import ftplib
import os
import pandas as pd
import numpy as np
from datetime import datetime
from scipy.sparse import csr_matrix, save_npz

# Détails de connexion FTP
FTP_SERVER = 'ftp.hydrosciences.org'
FTP_USERNAME = 'userird'
FTP_PASSWORD = 'SfrA09=I'
FTP_BASE_DIR = '/divers/Pluvio_Urbain/'
LOCAL_DIR = '/path/to/local/test/data/Pluvio_Urbain/'  # Remplacez par le chemin local de vos données de test
OUTPUT_DIR = '/path/to/local/test/output/Processed/'   # Remplacez par le chemin local de vos fichiers de sortie
CALIB_FILE = '/path/to/local/test/calib.csv'           # Remplacez par le chemin local de votre fichier de calibration

# Pluviomètres spécifiques à copier (seulement "Hydropolis" pour le test)
PLUVIOS = ['Hydropolis']

# Connexion au serveur FTP
ftp = ftplib.FTP(FTP_SERVER)
ftp.login(FTP_USERNAME, FTP_PASSWORD)

# Fonction pour télécharger les fichiers depuis le FTP
def download_files(ftp, base_dir, local_dir, pluvios):
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    for pluvio in pluvios:
        pluvio_dir = os.path.join(base_dir, pluvio)
        local_pluvio_dir = os.path.join(local_dir, pluvio)

        if not os.path.exists(local_pluvio_dir):
            os.makedirs(local_pluvio_dir)

        ftp.cwd(pluvio_dir)
        files = ftp.nlst()

        for file in files:
            local_file_path = os.path.join(local_pluvio_dir, file)
            if not os.path.exists(local_file_path):
                # Téléchargez le fichier si localement il n'existe pas
                with open(local_file_path, 'wb') as f:
                    ftp.retrbinary(f'RETR {file}', f.write)
            else:
                # Comparer la taille du fichier local et distant
                local_size = os.path.getsize(local_file_path)
                ftp.sendcmd(f'TYPE I')  # Mettre en mode binaire pour obtenir la taille correcte
                remote_size = ftp.size(file)
                if local_size != remote_size:
                    # Téléchargez le fichier si les tailles sont différentes
                    with open(local_file_path, 'wb') as f:
                        ftp.retrbinary(f'RETR {file}', f.write)

# Fonction pour concaténer les fichiers par année pour chaque pluviomètre
def concatenate_files_by_year(local_dir, pluvios):
    concatenated_files = []
    for pluvio in pluvios:
        local_pluvio_dir = os.path.join(local_dir, pluvio)
        annual_data = {}

        for file in os.listdir(local_pluvio_dir):
            file_path = os.path.join(local_pluvio_dir, file)
            data = pd.read_csv(file_path, header=None, names=['Station', 'Timestamp', 'Col3', 'Col4', 'Value'])
            data['Year'] = pd.to_datetime(data['Timestamp'], unit='s').dt.year

            for year, group in data.groupby('Year'):
                if year not in annual_data:
                    annual_data[year] = []
                annual_data[year].append(group)

        for year, data_list in annual_data.items():
            concatenated_data = pd.concat(data_list)
            output_year_dir = os.path.join(OUTPUT_DIR, str(year))
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
        station = row['station']
        a = row['a']
        b = row['b']
        c = row['c']
        calibration[station] = (a, b, c)
    return calibration

# Fonction pour calibrer les données
def calibrate_data(concatenated_files, calibration):
    for file_path in concatenated_files:
        data = pd.read_csv(file_path)
        station = data['Station'].iloc[0]
        if station in calibration:
            a, b, c = calibration[station]
            data['Calibrated'] = a * data['Value'] ** 2 + b * data['Value'] + c
            data.to_csv(file_path, index=False)

# Fonction pour créer des matrices creuses au format CSR
def create_sparse_matrix_csr(concatenated_files):
    for file_path in concatenated_files:
        data = pd.read_csv(file_path)
        # Suppression des colonnes de vent et de batterie
        data = data.drop(columns=['Col3', 'Col4'])
        timestamps = data['Timestamp'].values
        calibrated_values = data['Calibrated'].values
        stations = data['Station'].astype('category').cat.codes

        sparse_matrix = csr_matrix((calibrated_values, (timestamps, stations)), dtype=np.float32)
        sparse_matrix_file = file_path.replace('.csv', '_sparse.npz')
        save_npz(sparse_matrix_file, sparse_matrix)

# Fonction principale
def main():
    # Télécharger les fichiers depuis le FTP
    download_files(ftp, FTP_BASE_DIR, LOCAL_DIR, PLUVIOS)

    # Concaténation des fichiers par année pour chaque pluviomètre
    concatenated_files = concatenate_files_by_year(LOCAL_DIR, PLUVIOS)

    # Lecture du fichier de calibration
    calibration = read_calibration_file(CALIB_FILE)

    # Calibration des données
    calibrate_data(concatenated_files, calibration)

    # Création des matrices creuses au format CSR
    create_sparse_matrix_csr(concatenated_files)

    # Fermer la connexion FTP
    ftp.quit()

if __name__ == "__main__":
    main()
