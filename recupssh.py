import paramiko
from scp import SCPClient
import os
import stat
import time

# Détails de connexion SSH pour OVH
SSH_HOST = '37.187.122.112'
SSH_PORT = 22
SSH_USERNAME = 'ubuntu'
SSH_PASSWORD = 'Uzd9IEO2jaOcK5Mu'
REMOTE_DIR = '/home/ubuntu/UMRHSM/observHSM/'
LOCAL_DIR = '/Users/david/Desktop/StageHSM/Existant/'

# Fonction pour établir une connexion SSH avec plusieurs tentatives
def ssh_connect(max_retries=3, delay=5):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    for attempt in range(max_retries):
        try:
            print(f"Tentative de connexion SSH {attempt + 1}/{max_retries}...")
            ssh.connect(SSH_HOST, port=SSH_PORT, username=SSH_USERNAME, password=SSH_PASSWORD, banner_timeout=200)
            print("Connexion SSH établie.")
            return ssh
        except (paramiko.ssh_exception.SSHException, paramiko.ssh_exception.NoValidConnectionsError) as e:
            print(f"Erreur de connexion SSH : {e}. Nouvelle tentative dans {delay} secondes.")
            time.sleep(delay)
    
    print("Connexion SSH échouée après plusieurs tentatives.")
    return None

# Connexion SSH
ssh = ssh_connect()

def create_scp_client(ssh_client):
    return SCPClient(ssh_client.get_transport())

def download_directory(ssh_client, remote_dir, local_dir):
    scp = create_scp_client(ssh_client)
    
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    
    stdin, stdout, stderr = ssh_client.exec_command(f"ls -l {remote_dir}")
    for line in stdout:
        file_attr = line.split()
        if len(file_attr) >= 9:
            permissions = file_attr[0]
            is_directory = permissions.startswith('d')
            filename = file_attr[-1]
            remote_file_path = os.path.join(remote_dir, filename)
            local_file_path = os.path.join(local_dir, filename)
            
            if is_directory:
                download_directory(ssh_client, remote_file_path, local_file_path)
            else:
                scp.get(remote_file_path, local_file_path)
    
    scp.close()

if ssh:
    # Télécharger le répertoire distant
    download_directory(ssh, REMOTE_DIR, LOCAL_DIR)
    
    # Fermer la connexion SSH
    ssh.close()
else:
    print("Connexion SSH non établie.")
