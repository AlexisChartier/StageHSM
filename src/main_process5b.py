from synthesis_module import SynthesisReport
from datetime import datetime

def main():
    # Configuration des variables globales
    Station_list = ['Hydropolis', 'Polytech']
    Coord_geo = [
        [3.859559, 3.852183],  # Coordinates for Hydropolis and Polytech
        [43.621241, 43.62889]
    ]
    input_dir = '/home/ubuntu/UMRHSM/observHSM/FilesFrom_ftp'
    output_dir = '/srv/shiny-server/VerdansonPluie'

    # Demander à l'utilisateur les dates de début et de fin
    start_date_str = input("Enter the start date (YYYY-MM-DD): ")
    end_date_str = input("Enter the end date (YYYY-MM-DD): ")
    
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    report_name = f'summary_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}'
    
    synthesis_report = SynthesisReport(input_dir, output_dir, Station_list, Coord_geo)
    synthesis_report.generate_report(start_date, end_date, report_name)

if __name__ == "__main__":
    main()
