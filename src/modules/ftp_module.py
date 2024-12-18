import ftplib
import os

class FTPManager:
    def __init__(self, host, user, passwd):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.ftp = None

    def connect(self):
        self.ftp = ftplib.FTP(self.host)
        self.ftp.login(user=self.user, passwd=self.passwd)

    def download_file(self, remote_path, local_path):
        with open(local_path, 'wb') as f:
            self.ftp.retrbinary(f'RETR {remote_path}', f.write)

    def upload_file(self, local_path, remote_path):
        with open(local_path, 'rb') as f:
            self.ftp.storbinary(f'STOR {remote_path}', f)

    def delete_file(self, remote_path):
        self.ftp.delete(remote_path)

    def list_files(self, remote_dir):
        file_list = []
        self.ftp.retrlines(f'NLST {remote_dir}', file_list.append)
        return [os.path.join(remote_dir, file_name) for file_name in file_list]

    def disconnect(self):
        if self.ftp:
            self.ftp.quit()

    def list_directories(self, path):
        directories = []
        self.ftp.cwd(path)
        self.ftp.retrlines('LIST', lambda x: directories.append(x.split()[-1]) if x.startswith('d') else None)
        return directories

    def make_directory(self, path):
        self.ftp.mkd(path)