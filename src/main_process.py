import os
import sys
import shutil
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import h5py  # Import h5py for HDF5 file handling
from scipy.sparse import csr_matrix
from scipy.io import mmwrite  # Import mmwrite for saving sparse matrix in Matrix Market format
import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules'))
from calibration_module import Calibration
from ftp_module import FTPManager

# Configuration FTP (use environment variables for security)
FTP_HOST = os.getenv('FTP_HOST')
FTP_USER = os.getenv('FTP_USER')
FTP_PASS = os.getenv('FTP_PASS')

# Check that environment variables are set
if not all([FTP_HOST, FTP_USER, FTP_PASS]):
    raise EnvironmentError("Environment variables FTP_HOST, FTP_USER, and FTP_PASS must be set.")

# Configuration of temporary local directories
BASE_DIR = "/home/ubuntu/gestionpluvio/temp"
RAW_DIR = os.path.join(BASE_DIR, "raw")
CONCAT_DIR = os.path.join(BASE_DIR, "concat")
OUT_DIR = os.path.join(BASE_DIR, "out")
BACKUP_DIR = os.path.join(BASE_DIR, "backup")  # New directory for backups

# Path to the calibration file
CALIBRATION_FILE = "/home/ubuntu/gestionpluvio/src/calib.csv"

# List of pluviometers to process
PLUVIOS = [
    'ARCHIOUEST', 'Mse', 'CRBM', 'CEFE', 'CHU1', 'CHU2', 'CHU3',
    'CHU4', 'CHU5', 'CHU6', 'CHU7', 'CNRS', 'IEM', 'Polytech',
    'UM', 'UM35', 'Hydropolis', 'RueBrives', 'CINES'
]

def ftp_operation_with_reconnect(ftp_manager, ftp_func, *args, max_attempts=3, **kwargs):
    attempts = 0
    while attempts < max_attempts:
        try:
            return ftp_func(*args, **kwargs)
        except Exception as e:
            attempts += 1
            print(f"FTP operation failed (attempt {attempts}/{max_attempts}): {e}")
            print("Attempting to reconnect to FTP...")
            try:
                ftp_manager.disconnect()
            except:
                pass  # Ignore errors on disconnect
            ftp_manager.connect()
    raise Exception(f"FTP operation failed after {max_attempts} attempts.")

def backup_concatenated_file(ftp_manager, remote_file_path, backup_dir_remote):
    # Check if backup directory exists on FTP server, if not, create it
    try:
        parent_dir = os.path.dirname(backup_dir_remote)
        # List all items in the parent directory
        items = ftp_manager.list_files(parent_dir)
        # Check if backup directory exists among the items
        backup_dir_name = os.path.basename(backup_dir_remote)
        if backup_dir_name not in items:
            ftp_manager.make_directory(backup_dir_remote)
    except Exception as e:
        print(f"Error checking or creating backup directory {backup_dir_remote}: {e}")
        return False

    # Generate backup file name with date
    backup_file_name = os.path.basename(remote_file_path).replace('.csv', f'_backup_{datetime.utcnow().strftime("%Y%m%d")}.csv')
    backup_remote_path = os.path.join(backup_dir_remote, backup_file_name)

    # Check if backup for this week already exists
    try:
        existing_backups = ftp_manager.list_files(backup_dir_remote)
        if any(backup_file_name in f for f in existing_backups):
            print(f"Backup for this week already exists: {backup_file_name}")
            return True  # Backup already exists
    except Exception as e:
        print(f"Error listing backups in {backup_dir_remote}: {e}")
        return False

    # Download the current concatenated file
    local_backup_path = os.path.join(BACKUP_DIR, backup_file_name)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    try:
        ftp_operation_with_reconnect(ftp_manager, ftp_manager.download_file, remote_file_path, local_backup_path)
    except Exception as e:
        print(f"Error downloading file for backup {remote_file_path}: {e}")
        return False

    # Upload the backup file to the backup directory on FTP server
    try:
        ftp_operation_with_reconnect(ftp_manager, ftp_manager.upload_file, local_backup_path, backup_remote_path)
        print(f"Backup created: {backup_remote_path}")
        return True
    except Exception as e:
        print(f"Error uploading backup file {backup_remote_path}: {e}")
        return False

def process_pluvio(pluvio, ftp_manager):
    year = datetime.utcnow().year
    calibration = Calibration(CALIBRATION_FILE)

    # FTP paths
    concat_remote_path = f"/divers/dataPluvio/{pluvio}/{year}/{pluvio}_concatenated_{year}.csv"
    raw_remote_dir = f"/divers/Pluvio_Urbain/{pluvio}/"
    out_remote_dir = f"/divers/dataPluvio/{pluvio}/{year}/"
    backup_remote_dir = f"/divers/dataPluvio/{pluvio}/{year}/backups"  # Remote backup directory

    # Local paths
    concat_local_path = os.path.join(CONCAT_DIR, f"{pluvio}_concatenated_{year}.csv")
    raw_local_dir = os.path.join(RAW_DIR, pluvio)
    out_local_dir = os.path.join(OUT_DIR, pluvio, str(year))

    os.makedirs(os.path.dirname(concat_local_path), exist_ok=True)
    os.makedirs(raw_local_dir, exist_ok=True)
    os.makedirs(out_local_dir, exist_ok=True)

    # Download existing concatenated file (if it exists)
    concat_df = None
    try:
        ftp_operation_with_reconnect(ftp_manager, ftp_manager.download_file, concat_remote_path, concat_local_path)
        concat_df = pd.read_csv(concat_local_path)
        # Convertir 'Datetime_TU' en datetime avec gestion des erreurs
        concat_df['Datetime_TU'] = pd.to_datetime(concat_df['Datetime_TU'], utc=True, errors='coerce')
        # Supprimer les lignes avec des dates invalides
        invalid_dates = concat_df['Datetime_TU'].isna()
        if invalid_dates.any():
            print(f"Found {invalid_dates.sum()} invalid date(s) in concatenated file for {pluvio}. Removing invalid entries.")
            concat_df = concat_df[~invalid_dates]
    except Exception as e:
        print(f"Error downloading existing concatenated file for {pluvio}: {e}")
        print("Skipping processing for this pluviometer to avoid data loss.")
        return  # Skip processing this pluviometer to avoid overwriting data

    # Download raw data files
    try:
        raw_files = ftp_operation_with_reconnect(ftp_manager, ftp_manager.list_files, raw_remote_dir)
    except Exception as e:
        print(f"Error retrieving raw file list for {pluvio}: {e}")
        raw_files = []

    if not raw_files:
        print(f"No new raw data files for {pluvio}.")
        return  # No new data to process

    all_raw_data = []

    for raw_file in raw_files:
        raw_local_path = os.path.join(raw_local_dir, os.path.basename(raw_file))
        try:
            ftp_operation_with_reconnect(ftp_manager, ftp_manager.download_file, raw_file, raw_local_path)
        except Exception as e:
            print(f"Error downloading raw file {raw_file} for {pluvio}: {e}")
            continue  # Skip to the next file

        raw_df = pd.read_csv(raw_local_path, header=None, names=['Station', 'Timestamp', 'Rain', 'Wind', 'Battery'])
        raw_df['Timestamp'] = pd.to_numeric(raw_df['Timestamp'], errors='coerce')
        raw_df['Datetime_TU'] = pd.to_datetime(raw_df['Timestamp'], unit='s', utc=True)

        # Correct rain values
        raw_df['Rain'] = pd.to_numeric(raw_df['Rain'], errors='coerce')
        raw_df['Rain'] = raw_df['Rain'] * 0.2

        # Remove 'Timestamp' column
        raw_df.drop(columns=['Timestamp'], inplace=True)

        all_raw_data.append(raw_df)

    if all_raw_data:
        raw_data_df = pd.concat(all_raw_data)

        # Combine new data with the concatenated file
        combined_df = pd.concat([concat_df, raw_data_df]).drop_duplicates(subset=['Datetime_TU']).sort_values(by='Datetime_TU').reset_index(drop=True)

        # Generate complete time series
        start_time = combined_df['Datetime_TU'].min()
        end_time = combined_df['Datetime_TU'].max()
        time_index = pd.date_range(start=start_time, end=end_time, freq='1T', tz='UTC')
        full_time_df = pd.DataFrame({'Datetime_TU': time_index})

        combined_df = pd.merge(full_time_df, combined_df, on='Datetime_TU', how='left')

        # Replace missing values
        combined_df['Station'].fillna(pluvio, inplace=True)
        combined_df['Rain'] = combined_df['Rain'].fillna('na')
        combined_df['Wind'] = combined_df['Wind'].fillna('na')
        combined_df['Battery'] = combined_df['Battery'].fillna('na')

        # Rearrange columns in the specified order
        combined_df = combined_df[['Datetime_TU', 'Station', 'Rain', 'Wind', 'Battery']]

        # AJOUT : Filtrer les données pour l'année en cours seulement
        combined_df = combined_df[combined_df['Datetime_TU'].dt.year == year]
        if combined_df.empty:
            print(f"Toutes les données pour {pluvio} pour l'année {year} sont invalides ou hors année.")
            return

        # Save the updated concatenated file (raw data corrected without calibration)
        concat_output_path = os.path.join(out_local_dir, f"{pluvio}_concatenated_{year}.csv")
        combined_df.to_csv(concat_output_path, index=False)

        # Backup the concatenated file after correcting
        backup_success = backup_concatenated_file(ftp_manager, concat_remote_path, backup_remote_dir)
        if not backup_success:
            print(f"Backup failed for {pluvio}. Skipping further processing to avoid data loss.")
            return

        # Upload the updated concatenated file to the FTP server
        upload_success = False
        try:
            ftp_operation_with_reconnect(ftp_manager, ftp_manager.upload_file, concat_output_path, concat_remote_path)
            upload_success = True
            print(f"Successfully uploaded updated concatenated file for {pluvio}.")
        except Exception as e:
            print(f"Error uploading concatenated file for {pluvio}: {e}")

        if upload_success:
            # Apply calibration to generate treated data
            calibration = Calibration(CALIBRATION_FILE)
            treated_df = calibration.calibrate_data(combined_df.copy())

            # Save the treated file
            treated_file_path = os.path.join(out_local_dir, f"{pluvio}_treated_{year}.csv")
            treated_df.to_csv(treated_file_path, index=False)
            try:
                ftp_operation_with_reconnect(ftp_manager, ftp_manager.upload_file, treated_file_path, os.path.join(out_remote_dir, f"{pluvio}_treated_{year}.csv"))
                print(f"Successfully uploaded treated file for {pluvio}.")
            except Exception as e:
                print(f"Error uploading treated file for {pluvio}: {e}")

            # Generate sparse matrix from treated data
            sparse_files = generate_sparse_matrix(treated_df, out_local_dir, pluvio, year)
            hdf5_file, mtx_file = sparse_files

            # Upload HDF5 file
            try:
                ftp_operation_with_reconnect(ftp_manager, ftp_manager.upload_file, hdf5_file, os.path.join(out_remote_dir, f"{pluvio}_sparse_{year}.h5"))
                print(f"Successfully uploaded HDF5 sparse matrix for {pluvio}.")
            except Exception as e:
                print(f"Error uploading HDF5 sparse matrix for {pluvio}: {e}")

            # Upload MTX file
            try:
                ftp_operation_with_reconnect(ftp_manager, ftp_manager.upload_file, mtx_file, os.path.join(out_remote_dir, f"{pluvio}_sparse_{year}.mtx"))
                print(f"Successfully uploaded MTX sparse matrix for {pluvio}.")
            except Exception as e:
                print(f"Error uploading MTX sparse matrix for {pluvio}: {e}")

            # Delete raw files from FTP server
            for raw_file in raw_files:
                try:
                    ftp_operation_with_reconnect(ftp_manager, ftp_manager.delete_file, raw_file)
                    print(f"Deleted raw file {raw_file} from FTP server.")
                except Exception as e:
                    print(f"Error deleting raw file {raw_file} for {pluvio}: {e}")
        else:
            print(f"Upload failed for {pluvio}. Raw files will not be deleted to prevent data loss.")
    else:
        print(f"No raw data available for {pluvio}.")

def generate_sparse_matrix(treated_df, out_dir, pluvio, year):
    # Convert 'Rain' to numeric, keep 'na' as NaN
    treated_df['Rain_numeric'] = pd.to_numeric(treated_df['Rain'], errors='coerce')

    # Generate complete time series
    start_time = treated_df['Datetime_TU'].min()
    end_time = treated_df['Datetime_TU'].max()
    time_index = pd.date_range(start=start_time, end=end_time, freq='1T', tz='UTC')

    treated_df.set_index('Datetime_TU', inplace=True)
    treated_df = treated_df.reindex(time_index)
    treated_df.reset_index(inplace=True)
    treated_df.rename(columns={'index': 'Datetime_TU'}, inplace=True)

    timestamps = (treated_df['Datetime_TU'].astype(np.int64) // 10**9).values
    rain_values = treated_df['Rain_numeric'].values
    row_indices = np.arange(len(rain_values))
    col_indices = np.zeros(len(rain_values), dtype=int)
    data_values = rain_values

    valid_mask = ~np.isnan(data_values)
    sparse_matrix = csr_matrix((data_values[valid_mask], (row_indices[valid_mask], col_indices[valid_mask])), shape=(len(rain_values), 1))

    hdf5_file = os.path.join(out_dir, f'{pluvio}_sparse_{year}.h5')

    with h5py.File(hdf5_file, 'w') as f:
        grp = f.create_group('sparse_matrix')
        grp.create_dataset('data', data=sparse_matrix.data)
        grp.create_dataset('indices', data=sparse_matrix.indices)
        grp.create_dataset('indptr', data=sparse_matrix.indptr)
        grp.attrs['shape'] = sparse_matrix.shape

        f.create_dataset('timestamps', data=timestamps)

    mtx_file = os.path.join(out_dir, f'{pluvio}_sparse_{year}.mtx')
    mmwrite(mtx_file, sparse_matrix)

    return hdf5_file, mtx_file

def cleanup_raw_directory():
    if os.path.exists(RAW_DIR):
        shutil.rmtree(RAW_DIR)
        print(f"Raw files directory {RAW_DIR} cleaned up.")

def main():
    ftp_manager = FTPManager(FTP_HOST, FTP_USER, FTP_PASS)
    ftp_manager.connect()

    for pluvio in PLUVIOS:
        print(f"Processing pluviometer {pluvio}...")
        process_pluvio(pluvio, ftp_manager)

    ftp_manager.disconnect()
    cleanup_raw_directory()

if __name__ == "__main__":
    main()
