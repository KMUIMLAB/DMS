from datetime import datetime, timedelta
import json
import pandas as pd
import sys
import os
from copy import deepcopy
import numpy as np

from .transformation import Transformation
# Transformation 객체 생성
trans = Transformation()

# url로 API return값 요청
import requests
serviceKey = "rJ6s9K+rG3JFOf4IhdqOPze8ASxzSf3c5t4vFoZ8kDA4KxyXWUQtGPokEs39G10aZjj35ZgF17bZ0k965GtJUQ==" # 본인의 서비스 키 입력
url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst' # 기상청 초단기실황조회 url

class WeatherReceiver:
    def __init__(self, save_path):
        self.weather_columns = ['Grid X', 'Grid Y', 'Temp', 'Precipitation', 'EWwind', 'SNwind' ,'Humidity', 'PrecipitationType', 'WindDirection', 'WindSpeed']

        # self.base_path = os.path.dirname(__file__)
        self.base_path = save_path

        self.info_df = pd.read_csv(os.path.join(self.base_path, 'info.csv'))
        self.info_df_copy = deepcopy(self.info_df)

    def recv_weather(self, time, nx, ny):
        base_date = ''.join(time.split('_')[:3])
        base_time = ''.join(time.split('_')[3:5])

        params ={'serviceKey' : serviceKey, 'pageNo' : '1', 'numOfRows' : '1000', 'dataType' : 'JSON', 'base_date' : base_date, 'base_time' : base_time, 'nx' : nx, 'ny' : ny}
        response = requests.get(url, params=params)
        res = json.loads(response.text)

        if int(res['response']['header']['resultCode'])>0:
            return None

        # 데이터 추출 및 정리
        items = res['response']['body']['items']['item']
        data = {item['category']: {'value': item['obsrValue'], 'nx': item['nx'], 'ny': item['ny']} for item in items}

        # 항목 정보
        category_info = {
            'T1H': {'name': '기온', 'unit': '℃'},
            'RN1': {'name': '1시간 강수량', 'unit': 'mm'},
            'UUU': {'name': '동서바람성분', 'unit': 'm/s'},
            'VVV': {'name': '남북바람성분', 'unit': 'm/s'},
            'REH': {'name': '습도', 'unit': '%'},
            'PTY': {'name': '강수형태', 'unit': '코드값'},
            'VEC': {'name': '풍향', 'unit': 'deg'},
            'WSD': {'name': '풍속', 'unit': 'm/s'}
        }

        # 데이터프레임 생성
        df = pd.DataFrame(columns=['항목 코드', '항목명', '예보값', '단위', 'nx', 'ny'])
        for code, info in category_info.items():
            if code in data:
                df_recv = pd.DataFrame([{
                    '항목 코드': code,
                    '항목명': info['name'],
                    '예보값': np.float32(data[code]['value']),
                    '단위': info['unit'],
                    'nx': data[code]['nx'],
                    'ny': data[code]['ny'],
                }])
                df = pd.concat([df, df_recv], ignore_index=True, axis=0)

        return df

    def logging_weather(self, odo_list):
        for i in range(len(odo_list)):
            path_gnss = os.path.join(self.base_path, f'data/{odo_list[i]}/GNSS')
            file_name = os.listdir(path_gnss)[0]

            if len(os.listdir(path_gnss))==0:
                print('GNSS is True in info.csv, but no data found')
                self.info_df_copy.loc[self.info_df_copy['start_odo']==odo_list[i], 'Weather'] = False
                continue

            df_gnss = pd.read_csv(os.path.join(path_gnss, file_name))
            gnss_timestamp = df_gnss['Timestamp'].values

            df_gnss_copy = deepcopy(df_gnss)
            df_gnss_copy[self.weather_columns] = None

            tmp_grid = None
            complete = True
            for j in range(len(df_gnss)):
                time_step = gnss_timestamp[j]

                latitude, longitude = df_gnss.loc[j,['Latitude', 'Longitude']].tolist()
                nx, ny = trans.map_to_grid(latitude, longitude)

                if (tmp_grid is None or (time_step.split('_')[4]=='00' and time_step.split('_')[5]=='00' and time_step.split('_')[6]=='000000') or (tmp_grid != [nx, ny])):
                    tmp_grid = [nx, ny]
                    weather_recv = self.recv_weather(time_step, nx, ny)
                    if weather_recv is None:
                        complete = False
                        break
                    df_gnss_copy.loc[j, self.weather_columns] = [nx, ny, *(weather_recv['예보값'].values)]
            if not complete:
                continue

            df_gnss_copy = df_gnss_copy.fillna(method='ffill')
            df_gnss_copy.to_csv(os.path.join(path_gnss, file_name), index=False)

            self.info_df_copy.loc[self.info_df_copy['start_odo']==odo_list[i], 'Weather'] = True
            self.info_df_copy.to_csv(os.path.join(self.base_path, 'info.csv'), index=False)
