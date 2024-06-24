import ftplib
import os
import io

class FTPClient:
    def __init__(self, server, username, password, source_dir, target_dir):
        self.server = server
        self.username = username
        self.password = password
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.ftp = ftplib.FTP(self.server)
        self.ftp.login(self.username, self.password)

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
            try:
                self.ftp.cwd(pluvio_target_dir)
                file_list = self.ftp.nlst()
                for file_name in file_list:
                    copied_files[pluvio].add(file_name)
            except ftplib.error_perm:
                pass
        return copied_files

    def download_files(self, pluvio, local_temp_dir):
        pluvio_source_dir = os.path.join(self.source_dir, pluvio)
        pluvio_local_dir = os.path.join(local_temp_dir, pluvio)
        if not os.path.exists(pluvio_local_dir):
            os.makedirs(pluvio_local_dir)
        self.ftp.cwd(pluvio_source_dir)
        file_list = self.ftp.nlst()
        downloaded_files = []
        for file_name in file_list:
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
                if file_name not in copied_files[pluvio]:
                    bio = io.BytesIO()
                    self.ftp.retrbinary(f'RETR {file_name}', bio.write)
                    bio.seek(0)
                    self.ftp.cwd(pluvio_target_dir)
                    self.ftp.storbinary(f'STOR {file_name}', bio)
                    self.ftp.cwd(pluvio_source_dir)
                    copied_files[pluvio].add(file_name)
    
    def __del__(self):
        self.ftp.quit()
