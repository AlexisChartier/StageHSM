import ftplib
import os

# Détails de connexion FTP
FTP_SERVER = 'ftp.hydrosciences.org'
FTP_USERNAME = 'userird'
FTP_PASSWORD = 'SfrA09=I'
FTP_SOURCE_DIR = '/divers/Pluvio_Urbain/Polytech'
FTP_TARGET_DIR = '/divers/copiePluvio/Polytech'
LOCAL_TEMP_DIR = '/Users/david/Desktop/StageHSM/temp2'

# Connexion au serveur FTP
ftp = ftplib.FTP(FTP_SERVER)
ftp.login(FTP_USERNAME, FTP_PASSWORD)

def download_directory(ftp, source_dir, local_dir):
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    ftp.cwd(source_dir)
    file_list = ftp.nlst()

    for file_name in file_list:
        local_file_path = os.path.join(local_dir, file_name)
        
        with open(local_file_path, 'wb') as local_file:
            ftp.retrbinary(f'RETR {file_name}', local_file.write)

def upload_directory(ftp, local_dir, target_dir):
    try:
        ftp.mkd(target_dir)
    except ftplib.error_perm:
        # Directory probably exists
        pass
    
    os.chdir(local_dir)
    for file_name in os.listdir(local_dir):
        file_path = os.path.join(local_dir, file_name)
        
        with open(file_path, 'rb') as local_file:
            ftp.storbinary(f'STOR {target_dir}/{file_name}', local_file)

# Télécharger le répertoire source
download_directory(ftp, FTP_SOURCE_DIR, LOCAL_TEMP_DIR)

# Télécharger le répertoire vers le répertoire cible
upload_directory(ftp, LOCAL_TEMP_DIR, FTP_TARGET_DIR)

# Fermer la connexion FTP
ftp.quit()

# Nettoyer le répertoire temporaire local
for file_name in os.listdir(LOCAL_TEMP_DIR):
    file_path = os.path.join(LOCAL_TEMP_DIR, file_name)
    os.remove(file_path)
os.rmdir(LOCAL_TEMP_DIR)
