import requests

import requests
import pandas as pd
import numpy as np

pd.set_option('display.max_rows', 1000)

key = 'gOQ8JRmMRd8a3jb2oR3Lq/J5CCTnEfB/b50miVoLr6QjVWqDXXhIAM77YUeKXjYA1xT4FQxneIKS/aRanL/Wtw=='
url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst'
params ={'serviceKey' : key, 'pageNo' : '1', 'numOfRows' : '1000', 'dataType' : 'JSON', 'base_date' : '20250727', 'base_time' : '0600', 'nx' : '55', 'ny' : '127' }

response = requests.get(url, params=params).content.decode('utf-8')
from pprint import pprint 
import json 
pprint(json.loads(response))


file = '/Users/hjkim/Downloads/기상청41_단기예보 조회서비스_오픈API활용가이드_241128/기상청41_단기예보 조회서비스_오픈API활용가이드_격자_위경도(2411).xlsx'
df = pd.read_excel(file)
city_mask = df['1단계'].str.endswith('시')

df_city = df[city_mask]
df_others = df[~city_mask]

# 2) '시'로 끝나는 행은 'a'열만 기준으로 중복 제거
df_city_dedup = df_city.drop_duplicates(subset=['1단계'], keep='first')
df_city_dedup['2단계'] = df_city_dedup['1단계']

df_others_dedup = df_others.drop_duplicates(subset=['1단계', '2단계'], keep='first')
df_others_dedup = df_others_dedup[df_others_dedup['2단계'].str.endswith('시', na=False)]
df_others_dedup = df_others_dedup.dropna(subset=['2단계'])
df_2step = pd.concat([df_city_dedup, df_others_dedup], axis=0)

dedup_city = ['수원시','성남시','안양시','부천시','안산시','고양시','용인시','청주시','천안시','포항시','창원시','전주시']

def find_target_city(text):
    for city in dedup_city:
        if city in text:
            return city
    return np.nan

df_2step['city'] = df_2step['2단계'].apply(find_target_city)
df_city_dedup = df_2step.dropna(subset=['city']).drop_duplicates(subset=['city'], keep='first')
df_city_dedup['2단계'] = df_city_dedup['city']
df_city_no_dedup= df_2step[df_2step['city'].isna()]

# 4) 합치기와 인덱스 재정렬
df_result = pd.concat([df_city_dedup, df_city_no_dedup], axis=0).sort_index().reset_index(drop=True)
df_result = df_result[['2단계','격자 X','격자 Y']]

result_dict = {}
for idx, row in df_result.iterrows():
    result_dict[row['2단계']] = {'nx': row['격자 X'], 'ny': row['격자 Y']}
print(result_dict)

## 결과
{'서울특별시': {'nx': 60, 'ny': 127}, '부산광역시': {'nx': 98, 'ny': 76}, '대구광역시': {'nx': 89, 'ny': 90}, '인천광역시': {'nx': 55, 'ny': 124}, '광주광역시': {'nx': 58, 'ny': 74}, '대전광역시': {'nx': 67, 'ny': 100}, '울산광역시': {'nx': 102, 'ny': 84}, '세종특별자치시': {'nx': 66, 'ny': 103}, '의정부시': {'nx': 61, 'ny': 130}, '광명시': {'nx': 58, 'ny': 125}, '평택시': {'nx': 62, 'ny': 114}, '동두천시': {'nx': 61, 'ny': 134}, '과천시': {'nx': 60, 'ny': 124}, '구리시': {'nx': 62, 'ny': 127}, '남양주시': {'nx': 64, 'ny': 128}, '오산시': {'nx': 62, 'ny': 118}, '시흥시': {'nx': 57, 'ny': 123}, '군포시': {'nx': 59, 'ny': 122}, '의왕시': {'nx': 60, 'ny': 122}, '하남시': {'nx': 64, 'ny': 126}, '파주시': {'nx': 56, 'ny': 131}, '이천시': {'nx': 68, 'ny': 121}, '안성시': {'nx': 65, 'ny': 115}, '김포시': {'nx': 55, 'ny': 128}, '화성시': {'nx': 57, 'ny': 119}, '광주시': {'nx': 65, 'ny': 123}, '양주시': {'nx': 61, 'ny': 131}, '포천시': {'nx': 64, 'ny': 134}, '여주시': {'nx': 71, 'ny': 121}, '충주시': {'nx': 76, 'ny': 114}, '제천시': {'nx': 81, 'ny': 118}, '공주시': {'nx': 63, 'ny': 102}, '보령시': {'nx': 54, 'ny': 100}, '아산시': {'nx': 60, 'ny': 110}, '서산시': {'nx': 51, 'ny': 110}, '논산시': {'nx': 62, 'ny': 97}, '계룡시': {'nx': 65, 'ny': 99}, '당진시': {'nx': 54, 'ny': 112}, '목포시': {'nx': 50, 'ny': 67}, '여수시': {'nx': 73, 'ny': 66}, '순천시': {'nx': 70, 'ny': 70}, '나주시': {'nx': 56, 'ny': 71}, '광양시': {'nx': 73, 'ny': 70}, '경주시': {'nx': 100, 'ny': 91}, '김천시': {'nx': 80, 'ny': 96}, '안동시': {'nx': 91, 'ny': 106}, '구미시': {'nx': 84, 'ny': 96}, '영주시': {'nx': 89, 'ny': 111}, '영천시': {'nx': 95, 'ny': 93}, '상주시': {'nx': 81, 'ny': 102}, '문경시': {'nx': 81, 'ny': 106}, '경산시': {'nx': 91, 'ny': 90}, '진주시': {'nx': 81, 'ny': 75}, '통영시': {'nx': 87, 'ny': 68}, '사천시': {'nx': 80, 'ny': 71}, '김해시': {'nx': 95, 'ny': 77}, '밀양시': {'nx': 92, 'ny': 83}, '거제시': {'nx': 90, 'ny': 69}, '양산시': {'nx': 97, 'ny': 79}, '제주시': {'nx': 53, 'ny': 38}, '서귀포시': {'nx': 52, 'ny': 33}, '춘천시': {'nx': 73, 'ny': 134}, '원주시': {'nx': 76, 'ny': 122}, '강릉시': {'nx': 92, 'ny': 131}, '동해시': {'nx': 97, 'ny': 127}, '태백시': {'nx': 95, 'ny': 119}, '속초시': {'nx': 87, 'ny': 141}, '삼척시': {'nx': 98, 'ny': 125}, '군산시': {'nx': 56, 'ny': 92}, '익산시': {'nx': 60, 'ny': 91}, '정읍시': {'nx': 58, 'ny': 83}, '남원시': {'nx': 68, 'ny': 80}, '김제시': {'nx': 59, 'ny': 88}}

{
    'PTY': {
        '0': '비 안옴',
        '1': '비',
        '2': '비/눈',
        '3': '눈',
        '4': '소나기',
        '5': '빗방울',
        '6': '빗방울/눈날림',
        '7': '눈날림'
    },
    'REH': '습도',
    'RN1': '1시간 강수량',
    'TH1': '기온',
    'WSD': {
        '1': '4m/s 이하의 약한 바람', 
        '2': '4m/s ~ 9m/s의 약간 강한 바람',
        '3': '9m/s 이상의 강한 바람'
    }
}