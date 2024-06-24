import os
from ftp_module import FTPClient
from utils import delete_local_files

# Configuration des chemins et des détails de connexion
FTP_SERVER = 'ftp.hydrosciences.org'
FTP_USERNAME = 'userird'
FTP_PASSWORD = 'SfrA09=I'
FTP_TARGET_DIR = '/divers/copiePluvio/'
LOCAL_OUTPUT_DIR = '/home/ubuntu/processed/'

# Pluviomètres spécifiques à traiter
PLUVIOS = ['Hydropolis', 'Polytech']

def main():
    ftp_client = FTPClient(FTP_SERVER, FTP_USERNAME, FTP_PASSWORD, FTP_TARGET_DIR, FTP_TARGET_DIR)

    for pluvio in PLUVIOS:
        pluvio_output_dir = os.path.join(LOCAL_OUTPUT_DIR, 'treated', pluvio)
        if not os.path.exists(pluvio_output_dir):
            print(f"Aucun fichier traité pour {pluvio}")
            continue

        # Lister les fichiers sur le FTP avant l'upload pour les supprimer après l'upload
        previous_files = ftp_client.list_files(os.path.join(FTP_TARGET_DIR, pluvio))

        # Upload des fichiers traités sur le FTP
        for root, dirs, files in os.walk(pluvio_output_dir):
            for file_name in files:
                local_file_path = os.path.join(root, file_name)
                remote_file_path = os.path.join(FTP_TARGET_DIR, pluvio, file_name)
                with open(local_file_path, 'rb') as local_file:
                    ftp_client.ftp.storbinary(f'STOR {remote_file_path}', local_file)
                print(f"Uploadé : {remote_file_path}")

        # Supprimer les fichiers précédents sur le FTP
        ftp_client.delete_files(os.path.join(FTP_TARGET_DIR, pluvio), previous_files)

    ftp_client.__del__()

if __name__ == "__main__":
    main()
