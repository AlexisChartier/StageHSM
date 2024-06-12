import ftplib
import os
import time

# Détails de connexion FTP
FTP_SERVER = 'ftp.hydrosciences.org'
FTP_USERNAME = 'userird'
FTP_PASSWORD = 'SfrA09=I'
FTP_BASE_DIR = '/divers/Pluvio_Urbain/'
FTP_TARGET_DIR = '/divers/copiePluvio/'
LOCAL_TEMP_DIR = '/Users/david/Desktop/StageHSM/temp'

# Pluviomètres spécifiques à copier
PLUVIOS = ['Hydropolis', 'Polytech']

# Fichiers déjà copiés
copied_files = {pluvio: set() for pluvio in PLUVIOS}

# Connexion au serveur FTP
ftp = ftplib.FTP(FTP_SERVER)
ftp.login(FTP_USERNAME, FTP_PASSWORD)

def download_directory(ftp, base_dir, local_dir, pluvios, copied_files):
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    for pluvio in pluvios:
        pluvio_source_dir = os.path.join(base_dir, pluvio)
        pluvio_local_dir = os.path.join(local_dir, pluvio)
        
        if not os.path.exists(pluvio_local_dir):
            os.makedirs(pluvio_local_dir)
        
        ftp.cwd(pluvio_source_dir)
        file_list = ftp.nlst()
        
        for file_name in file_list:
            if file_name not in copied_files[pluvio]:
                local_file_path = os.path.join(pluvio_local_dir, file_name)
                
                with open(local_file_path, 'wb') as local_file:
                    ftp.retrbinary(f'RETR {file_name}', local_file.write)
                copied_files[pluvio].add(file_name)

def upload_directory(ftp, local_dir, target_dir):
    try:
        ftp.mkd(target_dir)
    except ftplib.error_perm:
        # Directory probably exists
        pass
    
    for pluvio in os.listdir(local_dir):
        pluvio_local_dir = os.path.join(local_dir, pluvio)
        pluvio_target_dir = os.path.join(target_dir, pluvio)
        
        try:
            ftp.mkd(pluvio_target_dir)
        except ftplib.error_perm:
            # Directory probably exists
            pass
        
        for file_name in os.listdir(pluvio_local_dir):
            file_path = os.path.join(pluvio_local_dir, file_name)
            
            with open(file_path, 'rb') as local_file:
                ftp.storbinary(f'STOR {pluvio_target_dir}/{file_name}', local_file)

while True:
    # Télécharger les fichiers des pluviomètres spécifiques depuis le répertoire source
    download_directory(ftp, FTP_BASE_DIR, LOCAL_TEMP_DIR, PLUVIOS, copied_files)

    # Télécharger les fichiers vers le répertoire cible sur le serveur FTP
    upload_directory(ftp, LOCAL_TEMP_DIR, FTP_TARGET_DIR)

    # Nettoyer le répertoire temporaire local
    for pluvio in os.listdir(LOCAL_TEMP_DIR):
        pluvio_local_dir = os.path.join(LOCAL_TEMP_DIR, pluvio)
        for file_name in os.listdir(pluvio_local_dir):
            file_path = os.path.join(pluvio_local_dir, file_name)
            os.remove(file_path)
        os.rmdir(pluvio_local_dir)
    
    # Attendre un court laps de temps avant de recommencer (par exemple, 5 secondes)
    time.sleep(5)

# Fermer la connexion FTP
ftp.quit()
