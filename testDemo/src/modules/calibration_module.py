import pandas as pd

class Calibration:
    def __init__(self, calib_file):
        self.calibration = self.read_calibration_file(calib_file)

    def read_calibration_file(self, calib_file):
        calib_params = pd.read_csv(calib_file)
        calibration = {}
        for _, row in calib_params.iterrows():
            station = row['pluvio']
            a = row['a']
            b = row['b']
            c = row['c']
            calibration[station] = (a, b, c)
        return calibration

    def calibrate_data(self, data):
        station = data['Station'].iloc[0]
        if station in self.calibration:
            a, b, c = self.calibration[station]
            data['Rain'] = a * data['Rain'] ** 2 + b * data['Rain'] + c
        return data
