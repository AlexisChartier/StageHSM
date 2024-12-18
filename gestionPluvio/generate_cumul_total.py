import sys
import os
import pandas as pd
from datetime import datetime, timezone

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 generate_cumul_total.py start_datetime end_datetime")
        sys.exit(1)

    start_datetime_str = sys.argv[1]
    end_datetime_str = sys.argv[2]

    # Conversion des dates en objets datetime avec fuseau horaire UTC
    start_datetime = datetime.strptime(start_datetime_str, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
    end_datetime = datetime.strptime(end_datetime_str, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)

    # Chemin vers le répertoire contenant les fichiers de données des pluviomètres
    data_dir = "/home/ubuntu/gestionpluvio/temp_concat_files/"  # À adapter selon votre structure

    # Liste des stations
    Station_list = [
        'ARCHIOUEST', 'MSE', 'CRBM', 'CEFE', 'CHU1', 'CHU2', 'CHU3',
        'CHU4', 'CHU5', 'CHU6', 'CHU7', 'CNRS', 'IEM', 'Polytech',
        'UM', 'UM35', 'Hydropolis', 'RueBrives', 'CINES'
    ]

    Station_coords = pd.DataFrame({
        'Station': Station_list,
        'lon': [3.856247, 3.865261, 3.865636, 3.862000, 3.852183, 3.853031, 3.850652,
                3.851633, 3.850291, 3.849433, 3.854902, 3.865228, 3.864156, 3.862627,
                3.868308, 3.860525, 3.859559, 3.864387, 3.84241],
        'lat': [43.636798, 43.636117, 43.637565, 43.637997, 43.62889, 43.629558, 43.630649,
                43.630649, 43.632465, 43.632913, 43.630112, 43.638624, 43.636195, 43.632598,
                43.631135, 43.632878, 43.621241, 43.62334, 43.6358]
    })

    stations_coords = Station_coords.set_index('Station')[['lon', 'lat']].to_dict('index')

    result = []

    # Générer l'index de temps attendu (une donnée par minute)
    expected_timestamps = pd.date_range(start_datetime, end_datetime, freq='T', tz='UTC')
    total_data_points = len(expected_timestamps)

    for station in Station_list:
        # Trouver les fichiers de données pour la station
        station_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) if station in f and f.endswith('.csv')]
        if not station_files:
            print(f"Aucun fichier de données trouvé pour la station {station}")
            # Créer un DataFrame vide avec les timestamps attendus et valeurs NaN
            station_data = pd.DataFrame({'Datetime_TU': expected_timestamps, 'Rain': [float('nan')] * total_data_points})
        else:
            station_data = pd.DataFrame()
            for file in station_files:
                df = pd.read_csv(file)

                required_columns = {'Datetime_TU', 'Rain', 'Station'}
                if not required_columns.issubset(df.columns):
                    continue

                try:
                    df['Datetime_TU'] = pd.to_datetime(df['Datetime_TU'], utc=True)
                except Exception as e:
                    print(f"Erreur lors de la conversion des dates dans le fichier {file}: {e}")
                    continue

                # Filtrer la période
                df = df[(df['Datetime_TU'] >= start_datetime) & (df['Datetime_TU'] <= end_datetime)]
                if df.empty:
                    continue

                station_data = pd.concat([station_data, df], ignore_index=True)

            if station_data.empty:
                print(f"Aucune donnée pour la station {station} dans la période sélectionnée")
                station_data = pd.DataFrame({'Datetime_TU': expected_timestamps, 'Rain': [float('nan')] * total_data_points})
            else:
                # Convertir Rain en numérique
                station_data['Rain'] = pd.to_numeric(station_data['Rain'], errors='coerce')
                # Supprimer les doublons de timestamps
                station_data = station_data.drop_duplicates(subset=['Datetime_TU'])
                # Réindexer sur les timestamps attendus
                station_data = station_data.set_index('Datetime_TU').reindex(expected_timestamps).reset_index()
                station_data.rename(columns={'index': 'Datetime_TU'}, inplace=True)

        non_missing_data_points = station_data['Rain'].notna().sum()
        missing_data_percentage = ((total_data_points - non_missing_data_points) / total_data_points) * 100
        missing_data_percentage = round(missing_data_percentage, 2)

        station_data['Rain'].fillna(0, inplace=True)
        total = station_data['Rain'].sum()
        total = round(total, 1)

        # Déterminer le dernier timestamp disponible
        if non_missing_data_points > 0:
            # Vérifier s'il y a des valeurs de pluie non nulles
            non_zero_data = station_data[station_data['Rain'] != 0]
            if not non_zero_data.empty:
                latest_time = non_zero_data['Datetime_TU'].max()
            else:
                # Aucune pluie non nulle, utiliser le dernier timestamp de la période sélectionnée
                latest_time = station_data['Datetime_TU'].max()
        else:
            # Aucun point non manquant (tout NaN remplacé par 0), latest_time = fin de la période
            latest_time = station_data['Datetime_TU'].max()

        if station not in stations_coords:
            print(f"Coordonnées non trouvées pour la station {station}")
            continue

        lon = stations_coords[station]['lon']
        lat = stations_coords[station]['lat']

        result.append({
            'site': station,
            'lon': lon,
            'lat': lat,
            'latest_time': latest_time.isoformat(),
            'total': total,
            'missing_data_percentage': missing_data_percentage
        })

    if not result:
        print("Aucune donnée disponible pour la période sélectionnée.")
        sys.exit(1)

    df_result = pd.DataFrame(result)

    output_file = f"Pluvio_Cumul_Total_{start_datetime_str}_{end_datetime_str}.csv"
    df_result.to_csv(output_file, index=False)
    print(f"Fichier de cumul généré : {output_file}")

if __name__ == "__main__":
    main()
