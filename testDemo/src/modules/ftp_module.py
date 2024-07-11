import ftplib
import os
import io
import time

class FTPClient:
    def __init__(self, server, username, password, source_dir, target_dir, processed_file, timeout=60):
        self.server = server
        self.username = username
        self.password = password
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.processed_file = processed_file
        self.timeout = timeout
        self.max_retries = 5  # Nombre maximum de tentatives de reconnexion
        self.connect()

    def connect(self):
        attempt = 0
        while attempt < self.max_retries:
            try:
                self.ftp = ftplib.FTP(self.server, timeout=self.timeout)
                self.ftp.login(self.username, self.password)
                print("Connexion réussie au serveur FTP.")
                return
            except ftplib.all_errors as e:
                attempt += 1
                print(f"Tentative de connexion {attempt} échouée : {e}. Nouvelle tentative dans 5 secondes...")
                time.sleep(5)
        raise ConnectionError(f"Impossible de se connecter au serveur FTP après {self.max_retries} tentatives.")

    def list_files(self, directory):
        """Liste les fichiers dans un répertoire FTP."""
        self.ftp.cwd(directory)
        files = self.ftp.nlst()
        return files

    def delete_files(self, directory, files_to_delete):
        """Supprime les fichiers spécifiés d'un répertoire FTP."""
        self.ftp.cwd(directory)
        for file in files_to_delete:
            try:
                self.ftp.delete(file)
                print(f"Supprimé : {file}")
            except ftplib.error_perm as e:
                print(f"Erreur lors de la suppression de {file}: {e}")

    def load_copied_files(self, pluvios):
        copied_files = {pluvio: set() for pluvio in pluvios}
        for pluvio in pluvios:
            pluvio_target_dir = f"{self.target_dir}{pluvio}/"
            attempt = 0
            while attempt < self.max_retries:
                try:
                    self.ftp.cwd(pluvio_target_dir)
                    file_list = self.ftp.nlst()
                    for file_name in file_list:
                        copied_files[pluvio].add(file_name)
                    break  # Sortir de la boucle si l'opération est réussie
                except ftplib.all_errors as e:
                    attempt += 1
                    print(f"Tentative de chargement {attempt} échouée pour {pluvio_target_dir} : {e}. Nouvelle tentative dans 5 secondes...")
                    time.sleep(5)
            else:
                print(f"Impossible de charger les fichiers pour {pluvio_target_dir} après {self.max_retries} tentatives.")
        return copied_files

    def download_files(self, pluvio, local_temp_dir, check_processed=False):
        pluvio_source_dir = os.path.join(self.source_dir, pluvio)
        pluvio_local_dir = os.path.join(local_temp_dir, pluvio)
        if not os.path.exists(pluvio_local_dir):
            os.makedirs(pluvio_local_dir)
        self.ftp.cwd(pluvio_source_dir)
        file_list = self.ftp.nlst()
        downloaded_files = []
        for file_name in file_list:
            if check_processed and file_name in self.processed_file:
                continue
            local_file_path = os.path.join(pluvio_local_dir, file_name)
            with open(local_file_path, 'wb') as local_file:
                self.ftp.retrbinary(f'RETR {file_name}', local_file.write)
            downloaded_files.append(file_name)
        return pluvio, downloaded_files

    def upload_files(self, local_dir):
        for root, dirs, files in os.walk(local_dir):
            for file_name in files:
                local_file_path = os.path.join(root, file_name)
                remote_file_path = os.path.join(self.target_dir, file_name)
                # Suppression du fichier distant s'il existe
                try:
                    self.ftp.delete(remote_file_path)
                except ftplib.error_perm:
                    pass
                with open(local_file_path, 'rb') as local_file:
                    self.ftp.storbinary(f'STOR {remote_file_path}', local_file)

    def copy_files_on_ftp(self, pluvios, copied_files):
        for pluvio in pluvios:
            pluvio_source_dir = f"{self.source_dir}{pluvio}/"
            pluvio_target_dir = f"{self.target_dir}{pluvio}/"
            try:
                self.ftp.mkd(pluvio_target_dir)
            except ftplib.error_perm:
                pass
            self.ftp.cwd(pluvio_source_dir)
            file_list = self.ftp.nlst()
            for file_name in file_list:
                if file_name not in copied_files[pluvio] and not self.is_file_processed(file_name):
                    bio = io.BytesIO()
                    self.ftp.retrbinary(f'RETR {file_name}', bio.write)
                    bio.seek(0)
                    self.ftp.cwd(pluvio_target_dir)
                    self.ftp.storbinary(f'STOR {file_name}', bio)
                    self.ftp.cwd(pluvio_source_dir)
                    copied_files[pluvio].add(file_name)

    def is_file_processed(self, file_name):
        if os.path.exists(self.processed_file):
            with open(self.processed_file, 'r') as f:
                processed_files = f.read().splitlines()
                if file_name in processed_files:
                    return True
        return False

    def mark_file_as_processed(self, file_name):
        with open(self.processed_file, 'a') as f:
            f.write(f"{file_name}\n")

    def __del__(self):
        try:
            self.ftp.quit()
        except (ftplib.error_reply, ftplib.error_temp, ftplib.error_perm, ftplib.error_proto, EOFError) as e:
            print(f"Erreur lors de la fermeture de la connexion FTP : {e}")
