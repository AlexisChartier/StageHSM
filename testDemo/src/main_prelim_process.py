import os
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules'))


from ftp_module import FTPClient
from calibration_module import Calibration
from processing_module import DataProcessor
from cumul_module import RainfallCumulMatrix
from utils import delete_local_files

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
PROCESSED_FILE = '/Users/david/Desktop/StageHSM/testDemo/src/processed_files.txt'

def process_data(pluvio, ftp_client, data_processor):
    # Télécharger les fichiers depuis le FTP en vérifiant s'ils sont déjà traités
    pluvio, downloaded_files = ftp_client.download_files(pluvio, LOCAL_TEMP_DIR, check_processed=True)
    if not downloaded_files:
        print(f"Aucune nouvelle donnée pour {pluvio}.")
        return

    # Mise à jour des fichiers concaténés
    concatenated_file_path, processed_files = data_processor.update_concatenated_files(pluvio)
    if concatenated_file_path and processed_files:
        data_processor.process_data(concatenated_file_path)
        
        # Marquer les fichiers comme traités après traitement
        for file_name in processed_files:
            ftp_client.mark_file_as_processed(file_name)

    # Envoi des fichiers concaténés et traités sur le FTP
    data_processor.upload_concatenated_files(ftp_client)
    data_processor.upload_treated_files(ftp_client)

    # Nettoyage des fichiers locaux et FTP
    #ftp_client.delete_files(FTP_SOURCE_DIR + pluvio, processed_files)
    delete_local_files(os.path.join(LOCAL_TEMP_DIR, pluvio))

def main():
    ftp_client = FTPClient(FTP_SERVER, FTP_USERNAME, FTP_PASSWORD, FTP_SOURCE_DIR, FTP_TARGET_DIR, PROCESSED_FILE)
    calibration = Calibration(CALIB_FILE)
    data_processor = DataProcessor(LOCAL_TEMP_DIR, LOCAL_OUTPUT_DIR, calibration)


    print("Début du traitement préliminaire des données...")
    for pluvio in PLUVIOS:
        process_data(pluvio, ftp_client, data_processor)

    print("Fermeture de la connexion FTP...")
    ftp_client.__del__()

if __name__ == "__main__":
    main()