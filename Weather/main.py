import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from Weather.request_estimation import Estimator
from Weather.request_weather import WeatherReceiver

def weather_main(save_path):
    request_est = Estimator(save_path)
    interesting_odos = request_est.find_odos()
    print(f'ODO : {interesting_odos}')

    weather_recv = WeatherReceiver(save_path)
    if len(interesting_odos)!=0:
        weather_recv.logging_weather(interesting_odos)

if __name__ == '__main__':
    weather_main()
