from synthesis_module import MonthlyReportGenerator
import argparse

def main():
    # Parse command line arguments for custom date range
    parser = argparse.ArgumentParser(description='Generate custom date range report')
    parser.add_argument('--start_date', type=str, required=True, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end_date', type=str, required=True, help='End date in YYYY-MM-DD format')
    args = parser.parse_args()

    # Configuration des chemins
    INPUT_DIR = '/home/ubuntu/gestionpluvio/processed/treated'
    OUTPUT_DIR = '/path/to/web/access/reports'

    # Générer le rapport pour la plage de dates spécifiée
    report_generator = MonthlyReportGenerator(INPUT_DIR, OUTPUT_DIR)
    report_generator.generate_custom_report(args.start_date, args.end_date)

if __name__ == "__main__":
    main()
