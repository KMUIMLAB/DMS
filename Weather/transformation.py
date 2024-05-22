import math
# 평면지도에서 지리적 위치를 표현할 때 발생하는 왜곡을 보정
# 위도경도 격자선이 표시되어야 할 범위와 경도 위도 숫자 라벨이 표시되어야 하는 범위가 다르기 때문에 변환을 거침
# 경위도 좌표계를 평면 직각각좌표계(격자)로 변환
class Transformation:
    def __init__(self):
        self.NX = 149            # X축 격자점 수
        self.NY = 253            # Y축 격자점 수

        self.Re = 6371.00877     # 지구 반경 (km)
        self.grid = 5.0          # 격자 간격 (km)
        self.slat1 = 30.0        # 표준 위도 1
        self.slat2 = 60.0        # 표준 위도 2
        self.olon = 126.0        # 기준점 경도
        self.olat = 38.0         # 기준점 위도
        self.xo = 210 / self.grid   # 기준점 X좌표
        self.yo = 675 / self.grid   # 기준점 Y좌표

        self.PI = math.pi
        self.DEGRAD = self.PI / 180.0
        self.RADDEG = 180.0 / self.PI

        self.re = self.Re / self.grid
        self.slat1 = self.slat1 * self.DEGRAD
        self.slat2 = self.slat2 * self.DEGRAD
        self.olon = self.olon * self.DEGRAD
        self.olat = self.olat * self.DEGRAD

        # Lambert Conformal Conic 계수 계산
        self.sn = math.tan(self.PI * 0.25 + self.slat2 * 0.5) / math.tan(self.PI * 0.25 + self.slat1 * 0.5) 
        self.sn = math.log(math.cos(self.slat1) / math.cos(self.slat2)) / math.log(self.sn)
        # 스케일 팩터
        self.sf = math.tan(self.PI * 0.25 + self.slat1 * 0.5)
        self.sf = math.pow(self.sf, self.sn) * math.cos(self.slat1) / self.sn
        #원점에서의 각 투영 반경
        self.ro = math.tan(self.PI * 0.25 + self.olat * 0.5)        
        self.ro = self.re * self.sf / math.pow(self.ro, self.sn)

    def map_to_grid(self, lat, lon):
        ra = math.tan(self.PI * 0.25 + lat * self.DEGRAD * 0.5)         #입력 위도(lat)와 경도(lon)에 대해 라디얼 거리 ra 계산
        ra = self.re * self.sf / math.pow(ra, self.sn)
        theta = lon * self.DEGRAD - self.olon                           #경도 차이에 대한 각도 조정 theta
        if theta > self.PI:
            theta -= 2.0 * self.PI
        elif theta < -self.PI:
            theta += 2.0 * self.PI
        theta *= self.sn
        x = (ra * math.sin(theta)) + self.xo                            #x, y 최종 격자 좌표
        y = (self.ro - ra * math.cos(theta)) + self.yo
        x = int(x + 1.5)
        y = int(y + 1.5)    
        return x, y

    def grid_to_map(self, x, y):
        x = x - 1
        y = y - 1
        xn = x - self.xo
        yn = self.ro - y + self.yo
        ra = math.sqrt(xn * xn + yn * yn)
        if self.sn < 0.0:
            ra = -ra
        alat = math.pow((self.re * self.sf / ra), (1.0 / self.sn))
        alat = 2.0 * math.atan(alat) - self.PI * 0.5
        if math.fabs(xn) <= 0.0:
            theta = 0.0
        else:
            if math.fabs(yn) <= 0.0:
                theta = self.PI * 0.5
                if xn < 0.0:
                    theta = -theta
            else:
                theta = math.atan2(xn, yn)
        alon = theta / self.sn + self.olon
        lat = alat * self.RADDEG
        lon = alon * self.RADDEG
        return lat, lon
