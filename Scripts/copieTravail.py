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
PLUVIOS = ['Hydropolis', 'Polytech']

# Fichier de suivi des fichiers copiés
TRACKING_FILE = '/Users/david/Desktop/StageHSM/Scripts/copied_files.txt'

def load_copied_files(tracking_file):
    if not os.path.exists(tracking_file):
        return {pluvio: set() for pluvio in PLUVIOS}
    copied_files = {pluvio: set() for pluvio in PLUVIOS}
    with open(tracking_file, 'r') as f:
        for line in f:
            if ',' in line:
                pluvio, file_name = line.strip().split(',', 1)
                if pluvio in copied_files:
                    copied_files[pluvio].add(file_name)
    return copied_files

def save_copied_file(tracking_file, pluvio, file_name):
    with open(tracking_file, 'a') as f:
        f.write(f"{pluvio},{file_name}\n")

# Charger les fichiers déjà copiés
copied_files = load_copied_files(TRACKING_FILE)

# Connexion au serveur FTP
ftp = ftplib.FTP(FTP_SERVER)
ftp.login(FTP_USERNAME, FTP_PASSWORD)

def copy_files_on_ftp(ftp, base_dir, target_dir, pluvios, copied_files):
    for pluvio in pluvios:
        pluvio_source_dir = os.path.join(base_dir, pluvio)
        pluvio_target_dir = os.path.join(target_dir, pluvio)
        
        try:
            ftp.mkd(pluvio_target_dir)
        except ftplib.error_perm:
            # Directory probably exists
            pass
        
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
                    save_copied_file(TRACKING_FILE, pluvio, file_name)
                except ftplib.error_perm as e:
                    print(f"Erreur lors de la copie du fichier {file_name}: {e}")

while True:
    # Copier les fichiers des pluviomètres spécifiques directement sur le serveur FTP
    copy_files_on_ftp(ftp, FTP_BASE_DIR, FTP_TARGET_DIR, PLUVIOS, copied_files)

    # Attendre un court laps de temps avant de recommencer (par exemple, 5 secondes)
    time.sleep(5)

# Fermer la connexion FTP
ftp.quit()
