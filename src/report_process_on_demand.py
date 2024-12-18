import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules'))

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from ftp_module import FTPManager

# Configuration FTP
FTP_HOST = "ftp.hydrosciences.org"
FTP_USER = "userird"
FTP_PASS = "SfrA09=I"

# Liste des stations pluviométriques à traiter
Station_list = [
    'ARCHIOUEST', 'Mse', 'CRBM', 'CEFE', 'CHU1', 'CHU2', 'CHU3',
    'CHU4', 'CHU5', 'CHU6', 'CHU7', 'CNRS', 'IEM', 'Polytech',
    'UM', 'UM35', 'Hydropolis', 'RueBrives', 'CINES'
]

def generate_graph_for_custom_period(station, start_date, end_date, ftp_manager):
    local_dir = "./temp_concat_files"
    files_to_concat = []

    if start_date.year != end_date.year:
        for year in range(start_date.year, end_date.year + 1):
            concat_remote_path = f"/divers/dataPluvio/{station}/{year}/{station}_concatenated_{year}.csv"
            local_file_path = os.path.join(local_dir, f"{station}_concatenated_{year}.csv")
            ftp_manager.download_file(concat_remote_path, local_file_path)
            files_to_concat.append(local_file_path)
    else:
        concat_remote_path = f"/divers/dataPluvio/{station}/{start_date.year}/{station}_concatenated_{start_date.year}.csv"
        local_file_path = os.path.join(local_dir, f"{station}_concatenated_{start_date.year}.csv")
        ftp_manager.download_file(concat_remote_path, local_file_path)
        files_to_concat.append(local_file_path)

    if files_to_concat:
        data = pd.concat([pd.read_csv(file) for file in files_to_concat])
        data['Timestamp'] = pd.to_datetime(data['Timestamp'], unit='s')
        data.set_index('Timestamp', inplace=True)

        data_custom_period = data[(data.index >= start_date) & (data.index <= end_date)]
        data_custom_period['Cumul'] = data_custom_period['Rain'].cumsum()

        fig, ax1 = plt.subplots(figsize=(12, 8))

        ax1.bar(data_custom_period.index, data_custom_period['Rain'], width=0.01, color='blue', label='intensity')
        ax1.set_ylabel('intensity (mm)', color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')

        ax2 = ax1.twinx()
        ax2.plot(data_custom_period.index, data_custom_period['Cumul'], color='red', label='cumul')
        ax2.set_ylabel('cumul (mm)', color='red')
        ax2.tick_params(axis='y', labelcolor='red')

        plt.title(f'{station}')
        plt.legend(loc="upper left")
        plt.grid()

        output_dir = f"./graphs/{station}"
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, f"{station}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.png")
        plt.savefig(output_path)
        print(f"Graphique sauvegardé sous {output_path}")
        plt.close()

def main():
    station = input(f"Sélectionnez une station parmi {Station_list}: ")

    start_date_str = input("Entrez la date de début (format YYYY-MM-DD) : ")
    end_date_str = input("Entrez la date de fin (format YYYY-MM-DD) : ")

    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    ftp_manager = FTPManager(FTP_HOST, FTP_USER, FTP_PASS)
    ftp_manager.connect()

    generate_graph_for_custom_period(station, start_date, end_date, ftp_manager)

    ftp_manager.disconnect()

if __name__ == "__main__":
    main()
