import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

class SynthesisReport:
    def __init__(self, input_dir, output_dir, station_list, coord_geo):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.station_list = station_list
        self.coord_geo = coord_geo

    def generate_report(self, start_date, end_date, report_name):
        data_list = []

        for station in self.station_list:
            file_path = os.path.join(self.input_dir, f'{station}_data.csv')
            if os.path.exists(file_path):
                data = pd.read_csv(file_path, parse_dates=['Timestamp'])
                data = data[(data['Timestamp'] >= start_date) & (data['Timestamp'] <= end_date)]
                data_list.append(data)
        
        if data_list:
            combined_data = pd.concat(data_list)
            self.create_plots(combined_data, report_name)
            self.create_summary_table(combined_data, report_name)

    def create_plots(self, data, report_name):
        plt.figure(figsize=(12, 8))
        for station in self.station_list:
            station_data = data[data['Station'] == station]
            plt.plot(station_data['Timestamp'], station_data['Rainfall'], label=station)
        
        plt.xlabel('Time')
        plt.ylabel('Rainfall (mm)')
        plt.title('Rainfall over Time')
        plt.legend()
        plt.grid(True)
        plot_path = os.path.join(self.output_dir, f'{report_name}_plot.png')
        plt.savefig(plot_path)
        plt.close()

    def create_summary_table(self, data, report_name):
        summary = data.groupby('Station').agg({
            'Rainfall': ['sum', 'mean', 'max'],
            'Wind_velocity': ['mean', 'max'],
            'Battery': 'mean'
        })
        summary.columns = ['Total Rainfall', 'Average Rainfall', 'Max Rainfall', 'Average Wind Velocity', 'Max Wind Velocity', 'Average Battery']
        summary_path = os.path.join(self.output_dir, f'{report_name}_summary.csv')
        summary.to_csv(summary_path)
        print(f'Summary table saved to {summary_path}')
