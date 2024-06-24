from ftp_module import FTPClient
import time

# Configuration des chemins et des détails de connexion
FTP_SERVER = 'ftp.hydrosciences.org'
FTP_USERNAME = 'userird'
FTP_PASSWORD = 'SfrA09=I'
FTP_BASE_DIR = '/divers/Pluvio_Urbain/'
FTP_TARGET_DIR = '/divers/copiePluvio/'
PLUVIOS = ['Hydropolis']

def main():
    ftp_client = FTPClient(FTP_SERVER, FTP_USERNAME, FTP_PASSWORD, FTP_BASE_DIR, FTP_TARGET_DIR)
    
    # Charger les fichiers déjà copiés
    copied_files = ftp_client.load_copied_files(PLUVIOS)

    print("Début de la copie des fichiers sur le serveur FTP...")
    while True:
        try:
            # Copier les fichiers des pluviomètres spécifiques directement sur le serveur FTP
            ftp_client.copy_files_on_ftp(PLUVIOS, copied_files)

            # Attendre un court laps de temps avant de recommencer (par exemple, 5 secondes)
            print("Attente avant la prochaine itération...")
            time.sleep(5)

        except KeyboardInterrupt:
            print("\nInterruption au clavier détectée. Arrêt du script.")
            break  # Sortir de la boucle principale en cas d'interruption au clavier

    print("Fermeture de la connexion FTP...")
    ftp_client.__del__()

if __name__ == "__main__":
    main()
