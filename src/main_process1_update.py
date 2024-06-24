import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from ftp_module import FTPClient
from calibration_module import Calibration
from processing_module import DataProcessor
from utils import delete_local_files

# Configuration des chemins et des détails de connexion
FTP_SERVER = 'ftp.hydrosciences.org'
FTP_USERNAME = 'userird'
FTP_PASSWORD = 'SfrA09=I'
FTP_SOURCE_DIR = '/source_directory/'
FTP_TARGET_DIR = '/divers/copiePluvio/'
LOCAL_TEMP_DIR = '/home/ubuntu/temp/'
LOCAL_OUTPUT_DIR = '/home/ubuntu/processed/'
CALIB_FILE = '/home/ubuntu/scripts/calib.csv'
PLUVIOS = ['Hydropolis', 'Polytech']

def main():
    ftp_client = FTPClient(FTP_SERVER, FTP_USERNAME, FTP_PASSWORD, FTP_SOURCE_DIR, FTP_TARGET_DIR)
    calibration = Calibration(CALIB_FILE)
    data_processor = DataProcessor(LOCAL_TEMP_DIR, LOCAL_OUTPUT_DIR, calibration)

    with ThreadPoolExecutor(max_workers=len(PLUVIOS)) as executor:
        future_to_pluvio = {executor.submit(ftp_client.download_files, pluvio, LOCAL_TEMP_DIR): pluvio for pluvio in PLUVIOS}
        downloaded_files = {}
        for future in as_completed(future_to_pluvio):
            pluvio, files = future.result()
            downloaded_files[pluvio] = files

    for pluvio in PLUVIOS:
        concatenated_file_path, processed_files = data_processor.update_concatenated_files(pluvio)
        data_processor.process_data(concatenated_file_path)

    data_processor.upload_concatenated_files(ftp_client)
    
    for pluvio in PLUVIOS:
        ftp_client.delete_files(pluvio, downloaded_files[pluvio])
        delete_local_files(os.path.join(LOCAL_TEMP_DIR, pluvio))
    
    # Fermer la connexion FTP
    ftp_client.__del__()

if __name__ == "__main__":
    main()

