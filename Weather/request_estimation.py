import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from copy import deepcopy

class Estimator:
    def __init__(self, save_path):
        self.now_date = datetime.now()
        self.day_ago = (self.now_date + timedelta(hours=-22, minutes=-59))

        # self.base_path = os.path.dirname(__file__)
        self.base_path = save_path

        self.info_df = pd.read_csv(os.path.join(self.base_path, 'info.csv'))

        self.info_df_copy = deepcopy(self.info_df)
        self.info_df_copy[self.info_df_copy['GNSS']==False]['Weather'] = False

    def find_odos(self):
        weather = np.array(deepcopy(self.info_df['Weather'].values))
        interesting_indexes = np.where(pd.isna(weather))[0]

        drive_start_time = deepcopy(self.info_df['start_time'].values)
        drive_start_time = pd.to_datetime(drive_start_time).tolist()
        for i in range(len(self.info_df)):
            drive_start_time[i] = pd.to_datetime(drive_start_time[i].astimezone().strftime("%Y-%m-%d %H:%M:%S"))
        drive_start_time = pd.to_datetime(drive_start_time)

        drive_end_time = deepcopy(self.info_df['end_time'].values)
        drive_end_time = pd.to_datetime(drive_end_time)

        update_after_drive_end = drive_end_time.map(lambda x: x.replace(minute=0, second=0) + pd.Timedelta(minutes=40))

        interesting_time_indexes = np.where(((drive_start_time>self.day_ago)&(update_after_drive_end<self.now_date))==True)[0]

        final_index = sorted(list(set(interesting_time_indexes) & set(interesting_indexes)))

        interesing_odo = self.info_df['start_odo'].values[final_index]

        self.info_df_copy.loc[np.where((drive_start_time<self.day_ago)&(weather!=True))[0], 'Weather'] = False
        self.info_df_copy.to_csv(os.path.join(self.base_path, 'info.csv'), index=False)

        return interesing_odo
