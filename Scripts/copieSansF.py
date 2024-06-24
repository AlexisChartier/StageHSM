import ftplib
import time
import os
import io

# Détails de connexion FTP
FTP_SERVER = 'ftp.hydrosciences.org'
FTP_USERNAME = 'userird'
FTP_PASSWORD = 'SfrA09=I'
FTP_BASE_DIR = '/divers/Pluvio_Urbain/'
FTP_TARGET_DIR = '/divers/copiePluvio/'

# Pluviomètres spécifiques à copier
PLUVIOS = ['Hydropolis']

# Fonction pour charger les fichiers déjà copiés en regardant sur le serveur FTP
def load_copied_files(ftp, base_dir, pluvios):
    print("Chargement des fichiers déjà copiés...")
    copied_files = {pluvio: set() for pluvio in pluvios}
    for pluvio in pluvios:
        pluvio_target_dir = f"{FTP_TARGET_DIR}{pluvio}/"
        try:
            ftp.cwd(pluvio_target_dir)
            file_list = ftp.nlst()
            for file_name in file_list:
                copied_files[pluvio].add(file_name)
            print(f"Fichiers chargés pour {pluvio}: {copied_files[pluvio]}")
        except ftplib.error_perm as e:
            print(f"Erreur lors de l'accès au répertoire {pluvio_target_dir}: {e}")
        except KeyboardInterrupt:
            print("\nInterruption au clavier détectée. Arrêt du chargement des fichiers.")
            return copied_files  # Retourner les fichiers déjà chargés jusqu'à présent en cas d'interruption

    return copied_files

# Connexion au serveur FTP
ftp = ftplib.FTP(FTP_SERVER)
try:
    print(f"Connexion au serveur FTP {FTP_SERVER}...")
    ftp.login(FTP_USERNAME, FTP_PASSWORD)

    # Charger les fichiers déjà copiés
    copied_files = load_copied_files(ftp, FTP_TARGET_DIR, PLUVIOS)

    def copy_files_on_ftp(ftp, base_dir, target_dir, pluvios, copied_files):
        for pluvio in pluvios:
            pluvio_source_dir = f"{base_dir}{pluvio}/"
            pluvio_target_dir = f"{target_dir}{pluvio}/"
            
            try:
                print(f"Création du répertoire cible {pluvio_target_dir}...")
                ftp.mkd(pluvio_target_dir)
            except ftplib.error_perm:
                # Directory probably exists
                pass
            
            try:
                print(f"Accès au répertoire source {pluvio_source_dir}...")
                ftp.cwd(pluvio_source_dir)
                file_list = ftp.nlst()
                
                for file_name in file_list:
                    if file_name not in copied_files[pluvio]:
                        try:
                            # Lire le fichier source dans un BytesIO
                            bio = io.BytesIO()
                            ftp.retrbinary(f'RETR {file_name}', bio.write)
                            bio.seek(0)  # Remettre le pointeur au début du BytesIO
                            
                            # Changer vers le répertoire cible et écrire le fichier
                            ftp.cwd(pluvio_target_dir)
                            ftp.storbinary(f'STOR {file_name}', bio)
                            
                            # Revenir au répertoire source
                            ftp.cwd(pluvio_source_dir)
                            
                            copied_files[pluvio].add(file_name)
                            print(f"Fichier {file_name} copié avec succès vers {pluvio_target_dir}.")
                        
                        except ftplib.error_perm as e:
                            print(f"Erreur lors de la copie du fichier {file_name}: {e}")
            
            except ftplib.error_perm as e:
                print(f"Erreur lors de l'accès au répertoire {pluvio_source_dir}: {e}")

    print("Début de la copie des fichiers sur le serveur FTP...")
    while True:
        try:
            # Copier les fichiers des pluviomètres spécifiques directement sur le serveur FTP
            copy_files_on_ftp(ftp, FTP_BASE_DIR, FTP_TARGET_DIR, PLUVIOS, copied_files)

            # Attendre un court laps de temps avant de recommencer (par exemple, 5 secondes)
            print("Attente avant la prochaine itération...")
            time.sleep(5)

        except KeyboardInterrupt:
            print("\nInterruption au clavier détectée. Arrêt du script.")
            break  # Sortir de la boucle principale en cas d'interruption au clavier

finally:
    print("Fermeture de la connexion FTP...")
    # Fermer la connexion FTP dans le bloc finally pour assurer la fermeture même en cas d'exception
    ftp.quit()
