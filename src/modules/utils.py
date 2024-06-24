import os

def delete_local_files(local_dir):
    for root, dirs, files in os.walk(local_dir):
        for file_name in files:
            os.remove(os.path.join(root, file_name))
        for dir_name in dirs:
            os.rmdir(os.path.join(root, dir_name))
