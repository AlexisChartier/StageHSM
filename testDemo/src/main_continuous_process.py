
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules'))

import pytz
import time
from datetime import datetime
from ftp_module import FTPClient
from calibration_module import Calibration
from processing_module import DataProcessor
from cumul_module import RainfallCumulMatrix
from utils import delete_local_files
import ftplib

# Configuration des chemins et des détails de connexion
FTP_SERVER = 'ftp.hydrosciences.org'
FTP_USERNAME = 'userird'
FTP_PASSWORD = 'SfrA09=I'
FTP_SOURCE_DIR = '/divers/copiePluvio/'
FTP_TARGET_DIR = '/divers/copiePluvio/Processed/'
LOCAL_TEMP_DIR = '/Users/david/Desktop/StageHSM/testDemo/Raw/'
LOCAL_OUTPUT_DIR = '/Users/david/Desktop/StageHSM/testDemo/Processed/'
CALIB_FILE = '/Users/david/Desktop/StageHSM/testDemo/src/calib.csv'
PLUVIOS = ['Hydropolis']
COORD_GEO = [
    [3.859559, 3.852183],  # Coordonnées pour Hydropolis et Polytech
    [43.621241, 43.62889]
]
OUTPUT_NAME = 'Pluvio_Mtp_'
PROCESSED_FILE = '/Users/david/Desktop/StageHSM/testDemo/src/processed_files.txt'

def main():
    while True:
        try:
            ftp_client = FTPClient(FTP_SERVER, FTP_USERNAME, FTP_PASSWORD, FTP_SOURCE_DIR, FTP_TARGET_DIR, PROCESSED_FILE)
            calibration = Calibration(CALIB_FILE)
            data_processor = DataProcessor(LOCAL_TEMP_DIR, LOCAL_OUTPUT_DIR, calibration)
            rainfall_cumul_matrix = RainfallCumulMatrix(PLUVIOS, COORD_GEO, LOCAL_TEMP_DIR, LOCAL_OUTPUT_DIR, OUTPUT_NAME)

            print("Téléchargement des nouvelles données...")
            for pluvio in PLUVIOS:
                pluvio, downloaded_files = ftp_client.download_files(pluvio, LOCAL_TEMP_DIR)
                if not downloaded_files:
                    print(f"Aucune nouvelle donnée pour {pluvio}.")
                    continue

                print("Mise à jour des données concaténées...")
                concatenated_file_path, processed_files = data_processor.update_concatenated_files(pluvio)
                if concatenated_file_path and processed_files:
                    data_processor.process_data(concatenated_file_path)
                    ftp_client.upload_files(os.path.join(LOCAL_OUTPUT_DIR, 'concatenated'))

                    # Marquer les fichiers comme traités après traitement
                    for file_name in processed_files:
                        ftp_client.mark_file_as_processed(file_name)

                print("Nettoyage des données brutes déjà traitées...")
                ftp_client.delete_files(os.path.join(FTP_SOURCE_DIR, pluvio), processed_files)
                delete_local_files(os.path.join(LOCAL_TEMP_DIR, pluvio))

            print("Génération de la matrice de cumul de pluie...")
            local_tz = pytz.timezone('Europe/Paris')
            local_time = datetime.now(local_tz)
            utc_time = local_time.astimezone(pytz.utc)
            start_timestamp = int(utc_time.timestamp())
            rainfall_cumul_matrix.calculate_cumulative_rainfall(start_timestamp)

            print("Attente de 5 minutes avant la prochaine mise à jour...")
            time.sleep(300)

        except ftplib.all_errors as e:
            print(f"Erreur FTP : {e}. Tentative de reconnexion...")
            ftp_client.connect()

        except Exception as e:
            print(f"Erreur inattendue : {e}. Nouvelle tentative dans 5 secondes...")
            time.sleep(5)

        except KeyboardInterrupt:
            print("\nInterruption au clavier détectée. Arrêt du script.")
            break

    print("Fermeture de la connexion FTP...")
    ftp_client.__del__()

if __name__ == "__main__":
    main()