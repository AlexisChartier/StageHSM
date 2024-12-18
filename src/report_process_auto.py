import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules'))
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
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

def generate_graph_for_last_month(station, ftp_manager):
    local_dir = "./temp_concat_files"
    current_year = datetime.now().year

    if datetime.now().month == 1:
        year_to_fetch = current_year - 1
    else:
        year_to_fetch = current_year

    concat_remote_path = f"/divers/dataPluvio/{station}/{year_to_fetch}/{station}_concatenated_{year_to_fetch}.csv"
    local_file_path = os.path.join(local_dir, f"{station}_concatenated_{year_to_fetch}.csv")

    ftp_manager.download_file(concat_remote_path, local_file_path)

    if os.path.exists(local_file_path):
        data = pd.read_csv(local_file_path)
        data['Timestamp'] = pd.to_datetime(data['Timestamp'], unit='s')
        data.set_index('Timestamp', inplace=True)

        last_month = datetime.now() - timedelta(days=datetime.now().day)
        data_last_month = data[data.index.month == last_month.month]

        data_last_month['Cumul'] = data_last_month['Rain'].cumsum()

        fig, ax1 = plt.subplots(figsize=(12, 8))

        ax1.bar(data_last_month.index, data_last_month['Rain'], width=0.01, color='blue', label='intensity')
        ax1.set_ylabel('intensity (mm)', color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')

        ax2 = ax1.twinx()
        ax2.plot(data_last_month.index, data_last_month['Cumul'], color='red', label='cumul')
        ax2.set_ylabel('cumul (mm)', color='red')
        ax2.tick_params(axis='y', labelcolor='red')

        plt.title(f'{station}')
        plt.legend(loc="upper left")
        plt.grid()

        output_dir = f"./graphs/{station}"
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, f"{station}_last_month.png")
        plt.savefig(output_path)
        print(f"Graphique sauvegardé sous {output_path}")
        plt.close()

def main():
    ftp_manager = FTPManager(FTP_HOST, FTP_USER, FTP_PASS)
    ftp_manager.connect()

    for station in Station_list:
        generate_graph_for_last_month(station, ftp_manager)

    ftp_manager.disconnect()

if __name__ == "__main__":
    main()
