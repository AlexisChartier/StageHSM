import os
import sys
import pandas as pd
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules'))
from datetime import datetime, timedelta, timezone
import numpy as np
import pytz
from ftp_module import FTPManager

# Ajouter le chemin du module FTPManager si nécessaire
# sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules'))
# from ftp_module import FTPManager

# Configuration FTP (use environment variables for security)
FTP_HOST = os.getenv('FTP_HOST')
FTP_USER = os.getenv('FTP_USER')
FTP_PASS = os.getenv('FTP_PASS')

# Liste des stations pluviométriques à traiter
Station_list = [
    'ARCHIOUEST', 'Mse', 'CRBM', 'CEFE', 'CHU1', 'CHU2', 'CHU3',
    'CHU4', 'CHU5', 'CHU6', 'CHU7', 'CNRS', 'IEM', 'Polytech',
    'UM', 'UM35', 'Hydropolis', 'RueBrives', 'CINES'
]

# Coordonnées géographiques des stations
Station_coords = pd.DataFrame({
    'Station': Station_list,
    'lon': [3.856247, 3.865261, 3.865636, 3.862000, 3.852183, 3.853031, 3.850652,
            3.851633, 3.850291, 3.849433, 3.854902, 3.865228, 3.864156, 3.862627,
            3.868308, 3.860525, 3.859559, 3.864387, 3.84241],
    'lat': [43.636798, 43.636117, 43.637565, 43.637997, 43.62889, 43.629558, 43.630649,
            43.630649, 43.632465, 43.632913, 43.630112, 43.638624, 43.636195, 43.632598,
            43.631135, 43.632878, 43.621241, 43.62334, 43.6358]
})

# Durées pour lesquelles on veut calculer le cumul de pluie (en minutes)
durations = {
    'P5min': 5,
    'P10min': 10,
    'P15min': 15,
    'P30min': 30,
    'P1h': 60,
    'P2h': 120,
    'P4h': 240,
    'P12h': 720,
    'P24h': 1440,
    'P48h': 2880,
    'P72h': 4320
}

# Répertoire de sortie pour les fichiers de cumul des pluies
dir_fold_out = '/srv/shiny-server/VerdansonPluie/'

def process_station_data(station, local_dir, day_date):
    year = day_date.year
    local_file = os.path.join(local_dir, f"{station}_concatenated_{year}.csv")
    if not os.path.exists(local_file):
        return None  # Retourne None si le fichier n'est pas trouvé

    data_in = pd.read_csv(local_file)
    # Convertir 'Datetime_TU' en datetime avec fuseau horaire UTC
    data_in['Datetime_TU'] = pd.to_datetime(data_in['Datetime_TU'], errors='coerce', utc=True)
    # Supprimer les lignes avec des dates invalides
    data_in = data_in.dropna(subset=['Datetime_TU'])
    # Filtrer les données pour le jour concerné
    day_start = datetime(day_date.year, day_date.month, day_date.day, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)
    mask = (data_in['Datetime_TU'] >= day_start) & (data_in['Datetime_TU'] < day_end)
    data_in = data_in.loc[mask]
    if data_in.empty:
        return None
    # Convertir 'Rain' en numérique, en conservant 'na' en NaN
    data_in['Rain'] = pd.to_numeric(data_in['Rain'], errors='coerce')
    # Trier les données par date croissante
    data_in = data_in.sort_values('Datetime_TU').reset_index(drop=True)
    return data_in[['Datetime_TU', 'Rain']]

def main():
    local_dir = "/home/ubuntu/gestionpluvio/temp_concat_files"
    os.makedirs(local_dir, exist_ok=True)
    ftp_manager = FTPManager(FTP_HOST, FTP_USER, FTP_PASS)
    ftp_manager.connect()

    # Télécharger les fichiers concaténés pour toutes les stations (une seule fois)
    now = datetime.now(timezone.utc)
    year = now.year

    for station in Station_list:
        concat_remote_path = f"/divers/dataPluvio/{station}/{year}/{station}_concatenated_{year}.csv"
        local_file_path = os.path.join(local_dir, f"{station}_concatenated_{year}.csv")
        # Télécharger le fichier via FTP
        try:
            ftp_manager.download_file(concat_remote_path, local_file_path)
        except Exception as e:
             print(f"Erreur lors du téléchargement du fichier pour la station {station}: {e}")

    # Générer les fichiers de cumul pour les 7 derniers jours
    for i in range(7):
        day_date = now - timedelta(days=i)
        day_str = day_date.strftime("%Y%m%d")
        station_cumul_dict = []

        for station in Station_list:
            data_in = process_station_data(station, local_dir, day_date)
            if data_in is None:
                print(f"Aucune donnée disponible pour la station {station} le {day_str}.")
                # Créer une entrée avec des zéros
                cumul_dict = {
                    'site': station,
                    'lon': Station_coords.loc[Station_coords['Station'] == station, 'lon'].values[0],
                    'lat': Station_coords.loc[Station_coords['Station'] == station, 'lat'].values[0]
                }

                # Ajouter un latest_time par défaut, par exemple le début du jour
                day_start = datetime(day_date.year, day_date.month, day_date.day, tzinfo=timezone.utc)
                cumul_dict['latest_time'] = day_start.isoformat()

                for duration_label in durations.keys():
                    cumul_dict[duration_label] = 0
                station_cumul_dict.append(cumul_dict)
                continue

            # Trouver le dernier timestamp disponible pour ce jour
            latest_time = data_in['Datetime_TU'].max()

            # Calculer les cumuls pour chaque durée
            cumul_dict = {'site': station}
            for duration_label, duration_minutes in durations.items():
                start_time = latest_time - timedelta(minutes=duration_minutes)
                # Filtrer les données entre start_time et latest_time
                mask = (data_in['Datetime_TU'] > start_time) & (data_in['Datetime_TU'] <= latest_time)
                cumul_rain = data_in.loc[mask, 'Rain'].sum(skipna=True)
                cumul_dict[duration_label] = cumul_rain
            # Ajouter les coordonnées
            coords = Station_coords[Station_coords['Station'] == station]
            cumul_dict['lon'] = coords['lon'].values[0]
            cumul_dict['lat'] = coords['lat'].values[0]
            # Ajouter le dernier temps disponible
            cumul_dict['latest_time'] = latest_time.isoformat()
            station_cumul_dict.append(cumul_dict)

        if not station_cumul_dict:
            print(f"Aucune donnée disponible pour le {day_str}.")
            continue

        # Créer le DataFrame final
        cumul_df = pd.DataFrame(station_cumul_dict)

        # Ordonner les colonnes selon le format attendu
        columns_order = ['site', 'lon', 'lat', 'latest_time'] + list(durations.keys())
        cumul_df = cumul_df[columns_order]

        # Enregistrer les données dans un fichier CSV
        output_file = os.path.join(dir_fold_out, f'Pluvio_Mtp_AAA_{day_str}.csv')
        cumul_df.to_csv(output_file, index=False)
        print(f"Données de cumul des pluies enregistrées dans {output_file}")

    # ftp_manager.disconnect()

if __name__ == "__main__":
    main()