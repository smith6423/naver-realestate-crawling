import time
import requests
import pandas as pd
from datetime import datetime

# 네이버 부동산 API 요청에 필요한 쿠키 정보
cookies = {
    'NNB': 'WBIWQ32QV3PWO',
    '_fwb': '80ixHYOpboUjw0q108szCH.1743030144941',
    'landHomeFlashUseYn': 'Y', 
    '_fwb': '80ixHYOpboUjw0q108szCH.1743030144941',
    'ASID': 'dc4c850e0000019628c2cea40000004e',
    'SHOW_FIN_BADGE': 'Y',
    '_ga_451MFZ9CFM': 'GS2.1.s1746926522$o8$g0$t1746926531$j0$l0$h0',
    'NAC': 'Z3DlBkQiXR37',
    '_ga': 'GA1.2.495057938.1743030467',
    '_ga_TSE3G32LNF': 'GS2.2.s1749042690$o1$g0$t1749042690$j60$l0$h0',
    'SRT30': '1749470484',
    'nhn.realestate.article.rlet_type_cd': 'A01',
    'nhn.realestate.article.trade_type_cd': '""',
    'nhn.realestate.article.ipaddress_city': '1100000000',
    'NACT': '1',
    'SRT5': '1749472822',
    'REALESTATE': 'Mon%20Jun%2009%202025%2021%3A40%3A50%20GMT%2B0900%20(Korean%20Standard%20Time)',
    'BUC': 'mCyEDh2M1N_Oz6sOjACy2YrYnUb47DaQmt-O6MdBNUc=',
}

# 네이버 부동산 API 요청에 필요한 헤더 정보
headers = {
    'accept': '*/*',
    'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IlJFQUxFU1RBVEUiLCJpYXQiOjE3NDk0NzI4NTAsImV4cCI6MTc0OTQ4MzY1MH0.1pRaG9HI3nRLk8NBNDHk2vlWyPpsyZ4vpJaYSIdVcbE',
    'priority': 'u=1, i',
    'referer': 'https://new.land.naver.com/complexes/672?ms=37.515131,126.8548401,15&a=APT:PRE&b=A1&e=RETAIL&g=70000&l=377&ad=true',
    'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
}

EXCEL_PATH = 'naver_property_data.xlsx'  # 데이터가 저장될 엑셀 파일명
MAX_PAGES = 3  # 한 번에 수집할 페이지 수(원하는 만큼 조정)

# 네이버 부동산에서 매물 데이터를 가져오는 함수
def get_property_data(max_pages):
    all_property_data = []  # 모든 매물 정보를 담을 리스트
    for page in range(1, max_pages + 1):  # 1페이지부터 max_pages까지 반복
        response = requests.get(
            f'https://new.land.naver.com/api/articles/complex/672?realEstateType=APT%3APRE&tradeType=A1&tag=%3A%3A%3A%3A%3A%3A%3A%3A&rentPriceMin=0&rentPriceMax=900000000&priceMin=0&priceMax=70000&areaMin=0&areaMax=900000000&oldBuildYears&recentlyBuildYears&minHouseHoldCount=377&maxHouseHoldCount&showArticle=true&sameAddressGroup=true&minMaintenanceCost&maxMaintenanceCost&priceType=RETAIL&directions=&page={page}&complexNo=672&buildingNos=&areaNos=&type=list&order=rank',
            cookies=cookies,
            headers=headers,
        )
        data = response.json()  # 응답을 JSON으로 파싱
        articles = data['articleList']  # 매물 리스트 추출
        for article in articles:
            # 각 매물의 주요 정보만 추출하여 딕셔너리로 저장
            property_info = {
                '매물번호': article['articleNo'],
                '단지명': article['articleName'],
                '거래유형': article['tradeTypeName'],
                '가격': article['dealOrWarrantPrc'],
                '면적(㎡)': article['area1'],
                '전용면적(㎡)': article['area2'],
                '층수': article['floorInfo'],
                '방향': article['direction'],
                '확인일자': article['articleConfirmYmd'],
                '특징': article.get('articleFeatureDesc', ''),
                '건물명': article['buildingName'],
                '공인중개사': article['realtorName'],
                '위도': article['latitude'],
                '경도': article['longitude']
            }
            all_property_data.append(property_info)  # 리스트에 추가
    return all_property_data

# 기존 엑셀 파일에서 데이터프레임을 불러오는 함수
def load_existing_data():
    try:
        df = pd.read_excel(EXCEL_PATH)
    except FileNotFoundError:
        df = pd.DataFrame()  # 파일이 없으면 빈 데이터프레임 반환
    return df

# 데이터프레임을 엑셀 파일로 저장하는 함수
def save_data(df):
    df.to_excel(EXCEL_PATH, index=False)

# 메인 실행 함수
def main():
    while True:
        print(f"[{datetime.now()}] 데이터 요청 중...")
        existing_df = load_existing_data()  # 기존 데이터 불러오기
        # 기존 매물번호(문자열) 집합 생성(중복 체크용)
        existing_ids = set(existing_df['매물번호'].astype(str)) if not existing_df.empty else set()
        new_data = get_property_data(MAX_PAGES)  # 새 데이터 크롤링
        # 기존에 없는(새로운) 매물만 필터링
        new_rows = [item for item in new_data if str(item['매물번호']) not in existing_ids]
        if new_rows:
            print(f"{len(new_rows)}건의 새로운 매물이 발견되어 추가합니다.")
            # 기존 데이터와 새 데이터를 합쳐서 저장
            updated_df = pd.concat([existing_df, pd.DataFrame(new_rows)], ignore_index=True)
            save_data(updated_df)
        else:
            print("새로운 매물이 없습니다.")
        print("1시간 대기...")
        time.sleep(3600)  # 1시간(3600초) 대기 후 반복

if __name__ == "__main__":
    main()