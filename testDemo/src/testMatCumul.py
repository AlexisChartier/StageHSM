import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class RainfallCumulMatrix:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file

    def calculate_cumulative_rainfall(self):
        # Lire les données de pluviométrie à partir du fichier de matrice creuse
        data = pd.read_csv(self.input_file)
        
        # Assurez-vous que le DataFrame est trié par timestamp
        data['Timestamp'] = pd.to_datetime(data['Timestamp'])
        data = data.sort_values(by='Timestamp')

        # Périodes de temps pour le calcul des cumuls (en minutes)
        periods = {
            'P5min': 5,
            'P10min': 10,
            'P30min': 30,
            'P1h': 60,
            'P2h': 120,
            'P4h': 240,
            'P12h': 720,
            'P24h': 1440,
            'P48h': 2880,
            'P72h': 4320
        }

        # Initialisation du dictionnaire pour stocker les cumuls
        cumuls = {key: [] for key in periods}

        # Calcul des cumuls pour chaque période
        for period_name, period_minutes in periods.items():
            cumuls[period_name] = self.calculate_period_cumul(data, period_minutes)

        # Construction de la matrice de cumul de pluie
        cumulative_matrix = self.construct_cumulative_matrix(data, cumuls)

        # Sauvegarde de la matrice de cumul dans un fichier CSV
        cumulative_matrix.to_csv(self.output_file, index=False)
        print(f'Matrice de cumul de pluie sauvegardée dans {self.output_file}')

    def calculate_period_cumul(self, data, period_minutes):
        period_cumul = []
        for current_time in data['Timestamp']:
            start_time = current_time - timedelta(minutes=period_minutes)
            period_data = data[(data['Timestamp'] > start_time) & (data['Timestamp'] <= current_time)]
            total_rain = period_data['Hydropolis'].sum()
            period_cumul.append(total_rain)
        return period_cumul

    def construct_cumulative_matrix(self, data, cumuls):
        cumuls_df = pd.DataFrame(cumuls)
        cumuls_df.insert(0, 'Timestamp', data['Timestamp'])
        return cumuls_df

def main():
    # Fichiers d'entrée et de sortie
    INPUT_FILE = '/Users/david/Desktop/StageHSM/Processed/treated/2024/Hydropolis_treated_2024_sparse.csv'  # Remplacez par le chemin réel du fichier d'entrée
    OUTPUT_FILE = '/Users/david/Desktop/StageHSM/Processed/treated/2024/output_cumulative_matrix.csv'  # Remplacez par le chemin réel du fichier de sortie

    # Création de l'instance de la classe RainfallCumulMatrix
    rainfall_cumul_matrix = RainfallCumulMatrix(INPUT_FILE, OUTPUT_FILE)

    # Calcul des cumuls de pluie et génération de la matrice
    rainfall_cumul_matrix.calculate_cumulative_rainfall()

if __name__ == "__main__":
    main()
