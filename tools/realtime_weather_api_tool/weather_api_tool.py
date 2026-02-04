import sys, os 
BASE_DIR = os.getcwd()
sys.path.insert(0, BASE_DIR)

import httpx
from datetime import datetime, timedelta
import json
from json import JSONDecodeError
import os 
from tools.realtime_weather_api_tool.weather_meta_info import CATEGORY, CITY
from fastapi_app.app.core.config import settings
from fastapi_app.app.utils.logger import get_logger

data_go_kr_key = settings.DATA_GO_KR_KEY
logger = get_logger(__name__)

class WeatherApiTool():
    def __init__(self):
        self.url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst'
        self.log = logger

    def _make_weather_info(self, item: list):
        '''
        공공데이터 포털 조회 결과(리스트)를 받아 필요한 날씨 정보를 조합하여 리턴하는 함수
        '''
        answer_info = {}
        for i in item:
            category = i['category']
            observe = i['obsrValue']
            category_type = CATEGORY.get(category)

            # 만약 category_type 값이 None인 경우 사용하지 않을 정보임 (풍향 등)
            if category_type is None:
                continue
            # category_type 값이 코드로 되어 있는 경우 한번 더 룩업 수행
            if isinstance(category_type, dict):
                weather_type = category_type['type']
                value = category_type[observe]
                answer_info[weather_type] = value
                
            # 그 외의 경우 obsrValue 값이 곧 관측 값임
            else:
                answer_info[category_type] = observe

        return str(answer_info)


    async def call_api(self, city: str, minute_ago: int):
        '''
        도시 ("시"로 끝나야 함) 를 입력받아 공공데이터 날씨 단기 예보 조회하여 결과값을 리턴하는 함수
        '''
        
        now = datetime.now()
        # 현재보다 minute_ago 만큼 과거 데이터로 데이터로 조회
        three_minutes_ago = now - timedelta(minutes=minute_ago)
        before_3min_str = three_minutes_ago.strftime('%Y%m%d%H%M')
        yyyymmdd = before_3min_str[:8]
        hhmm = before_3min_str[8:]

        try:
            nx = CITY[city]["nx"]
            ny = CITY[city]["ny"]
        except KeyError:
            raise KeyError('잘못된 도시명 입력. "시"로 끝나는 도시를 입력해주세요.')

        params ={
            'serviceKey' : data_go_kr_key,
            'pageNo' : '1',
            'numOfRows' : '1000',
            'dataType' : 'JSON',
            'base_date' : yyyymmdd,
            'base_time' : hhmm,
            'nx' : nx,
            'ny' : ny 
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(self.url, params=params)
            self.log.info(f"호출 주소: {self.url} , 리턴 결과: {response.text}")
        try:
            resp_json = json.loads(response.text)
        except JSONDecodeError:
            raise JSONDecodeError(f'response: {response}', str(response), 0)
        
        return resp_json
    

    async def get_weather_api(self, city: str):
        """
        주어진 도시(city) 기준으로 3분 전 데이터부터 최대 60분 전 데이터까지
        API를 재호출하여 최신 기상정보를 조회합니다.

        - NO_DATA(resultCode='03')일 경우 1분씩 점점 과거 데이터로 재시도.
        - 그 외 오류 발생 시 예외 발생.
        """
        minute_ago = 3          # 기본 3분 전 데이터로 조회
        retry_cnt = 0
        retry_max = 60
        while retry_cnt < retry_max:       # 최대 60분 전까지만 탐색하고 그래도 안나오면 API 서버 이상 상태로 간주
            api_rslt = await self.call_api(city=city, minute_ago=minute_ago)        

            rslt_code = api_rslt["response"]["header"]["resultCode"]
            rslt_msg = api_rslt["response"]["header"]["resultMsg"]
            if rslt_code == '03':   # NO_DATA 
                minute_ago += 1     # 1분씩 더 과거로 조회 시도
                retry_cnt += 1
                self.log.info(f"get_weather_api retry_cnt: {retry_cnt}")
                continue 

            # 그 외 오류들
            elif rslt_code != '00':
                raise Exception(f'Result Code: {rslt_code}, Result Message: {rslt_msg}')
            
            item = api_rslt["response"]["body"]["items"]["item"]
            if item[0].get('obsrValue') == '-999':
                raise Exception('잘못된 좌표 입력')
            else:
                return self._make_weather_info(item)
        
        raise Exception('NO_DATA, API 서버 사용 불가 상태')
    
    @property
    def tools_description(self) -> dict:
        city_list = list(CITY.keys())
        return {
            "type": "function",
            "function": {
                "name": "get_weather_api",
                "description": "주어진 city에 대한 현재 기상 상태와 온도, 습도, 풍속 리턴, 강수량(비가 올 경우) 리턴",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "날씨를 파악하고자 하는 도시, 예시) '서울시'",
                            "enum": city_list
                        },
                    },
                    "required": ["city"],
                },
            },
        }
    
### 테스트 수행
# import asyncio 
# tool = WeatherApiTool()
# print(asyncio.run(tool.get_weather_api('강릉시')))
