# 네이버 부동산 매물 크롤러

네이버 부동산에서 특정 단지의 매물 정보를 1시간마다 자동으로 수집하여,  
새로운 매물이 있을 때만 엑셀 파일에 추가 저장하는 파이썬 크롤러입니다.

## 주요 기능

- 네이버 부동산 API를 활용한 매물 정보 수집
- 1시간마다 자동으로 최신 매물 정보 갱신
- 중복 매물(매물번호 기준) 자동 스킵
- 엑셀 파일(`naver_property_data.xlsx`)로 저장

## 사용 방법

1. **필수 라이브러리 설치**
    ```bash
    pip install -r requirements.txt
    ```

2. **크롤러 실행**
    ```bash
    python naver_crawling.py
    ```

3. **엑셀 파일 확인**
    - `naver_property_data.xlsx` 파일이 생성되며, 새로운 매물이 있을 때마다 자동으로 추가됩니다.

## 파일 설명

- `naver_crawling.py` : 크롤러 메인 코드
- `requirements.txt` : 필요한 파이썬 패키지 목록
- `naver_property_data.xlsx` : 수집된 매물 데이터 (실행 후 생성)
- `README.md` : 프로젝트 설명 파일

## 참고 및 주의사항

- 네이버 부동산 API의 쿠키, 헤더, 토큰 등은 만료될 수 있으니, 필요시 갱신해 주세요.
- 본 프로젝트는 학습 및 포트폴리오 용도로만 사용해 주세요.

---

## Contact

궁금한 점이나 개선 제안은 [이메일](mailto:smith720@naver.com) 또는 [이슈 등록](https://github.com/smith6423/naver-realestate-crawling/issues) 부탁드립니다. 