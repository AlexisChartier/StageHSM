import os
from cumul_module import RainfallCumulMatrix

def main():
    # Configuration des variables globales
    Station_list = ['Hydropolis', 'Polytech']
    Coord_geo = [
        [3.859559, 3.852183],  # Coordinates for Hydropolis and Polytech
        [43.621241, 43.62889]
    ]

    # Chemins de fichiers
    input_dir = '/home/ubuntu/UMRHSM/observHSM/FilesFrom_ftp'
    output_dir = '/srv/shiny-server/VerdansonPluie'
    output_name = 'Pluvio_Mtp_'

    # Création de l'objet RainfallCumulMatrix et calcul du cumul des pluies
    rainfall_cumul_matrix = RainfallCumulMatrix(Station_list, Coord_geo, input_dir, output_dir, output_name)
    rainfall_cumul_matrix.calculate_cumulative_rainfall()

if __name__ == "__main__":
    main()
