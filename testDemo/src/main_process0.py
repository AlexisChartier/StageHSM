import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules'))


import time
from ftp_module import FTPClient
import ftplib
# Configuration des chemins et des détails de connexion
FTP_SERVER = 'ftp.hydrosciences.org'
FTP_USERNAME = 'userird'
FTP_PASSWORD = 'SfrA09=I'
FTP_BASE_DIR = '/divers/Pluvio_Urbain/'
FTP_TARGET_DIR = '/divers/copiePluvio/'
PLUVIOS = ['Hydropolis']
PROCESSED_FILE = 'Users/david/Desktop/StageHSM/testDemo/src/processed_files.txt'

def main():
    ftp_client = FTPClient(FTP_SERVER, FTP_USERNAME, FTP_PASSWORD, FTP_BASE_DIR, FTP_TARGET_DIR, PROCESSED_FILE)
    
    # Charger les fichiers déjà copiés
    copied_files = ftp_client.load_copied_files(PLUVIOS)

    print("Début de la copie des fichiers sur le serveur FTP...")
    while True:
        try:
            # Copier les fichiers des pluviomètres spécifiques directement sur le serveur FTP
            ftp_client.copy_files_on_ftp(PLUVIOS, copied_files)

            # Attendre un court laps de temps avant de recommencer (par exemple, 5 minutes)
            print("Attente avant la prochaine itération...")
            time.sleep(300)

        except ftplib.all_errors as e:
            print(f"Erreur FTP : {e}. Tentative de reconnexion...")
            ftp_client.connect()
        
        except KeyboardInterrupt:
            print("\nInterruption au clavier détectée. Arrêt du script.")
            break  # Sortir de la boucle principale en cas d'interruption au clavier

    print("Fermeture de la connexion FTP...")
    ftp_client.__del__()

if __name__ == "__main__":
    main()