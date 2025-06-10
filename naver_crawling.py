import time
import requests
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread

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

class NaverPropertyCrawler:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("네이버 부동산 크롤러")
        self.root.geometry("900x600")
        self.is_running = False
        self.selected_complex_no = None
        self.collect_list = []  # 수집 목록: [{'complexNo':..., 'complexName':..., 'detailAddress':...}]
        self.setup_gui()
        self.load_sido()

    def setup_gui(self):
        # 지역 선택 프레임
        region_frame = ttk.Frame(self.root, padding="10")
        region_frame.pack(fill=tk.X)

        ttk.Label(region_frame, text="시/도:").pack(side=tk.LEFT)
        self.sido_cb = ttk.Combobox(region_frame, state="readonly", width=12)
        self.sido_cb.pack(side=tk.LEFT, padx=5)
        self.sido_cb.bind("<<ComboboxSelected>>", self.on_sido_selected)

        ttk.Label(region_frame, text="구/군:").pack(side=tk.LEFT)
        self.gugun_cb = ttk.Combobox(region_frame, state="readonly", width=12)
        self.gugun_cb.pack(side=tk.LEFT, padx=5)
        self.gugun_cb.bind("<<ComboboxSelected>>", self.on_gugun_selected)

        ttk.Label(region_frame, text="동:").pack(side=tk.LEFT)
        self.dong_cb = ttk.Combobox(region_frame, state="readonly", width=12)
        self.dong_cb.pack(side=tk.LEFT, padx=5)
        self.dong_cb.bind("<<ComboboxSelected>>", self.on_dong_selected)

        # 아파트(단지) 및 수집 목록 프레임
        list_frame = ttk.Frame(self.root, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=False)

        # 아파트(단지) 목록
        apt_frame = ttk.Frame(list_frame)
        apt_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(apt_frame, text="아파트(단지) 목록:").pack(anchor=tk.W)
        apt_listbox_frame = ttk.Frame(apt_frame)
        apt_listbox_frame.pack(fill=tk.BOTH, expand=True)
        self.complex_listbox = tk.Listbox(apt_listbox_frame, height=10, width=40)
        self.complex_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        complex_scroll = ttk.Scrollbar(apt_listbox_frame, orient=tk.VERTICAL, command=self.complex_listbox.yview)
        complex_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.complex_listbox.configure(yscrollcommand=complex_scroll.set)
        self.complex_listbox.bind("<Double-Button-1>", self.on_complex_double_click)

        # 수집 목록
        collect_frame = ttk.Frame(list_frame)
        collect_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20)
        ttk.Label(collect_frame, text="수집 목록:").pack(anchor=tk.W)
        collect_listbox_frame = ttk.Frame(collect_frame)
        collect_listbox_frame.pack(fill=tk.BOTH, expand=True)
        self.collect_listbox = tk.Listbox(collect_listbox_frame, height=10, width=40)
        self.collect_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        collect_scroll = ttk.Scrollbar(collect_listbox_frame, orient=tk.VERTICAL, command=self.collect_listbox.yview)
        collect_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.collect_listbox.configure(yscrollcommand=collect_scroll.set)
        self.remove_button = ttk.Button(collect_frame, text="선택 삭제", command=self.remove_from_collect_list)
        self.remove_button.pack(pady=5)

        # 버튼 프레임
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill=tk.X)
        self.start_button = ttk.Button(button_frame, text="크롤링 시작", command=self.start_crawling)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.stop_button = ttk.Button(button_frame, text="크롤링 중지", command=self.stop_crawling, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # 로그 출력 영역
        log_frame = ttk.Frame(self.root, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        log_text_frame = ttk.Frame(log_frame)
        log_text_frame.pack(fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(log_text_frame, height=15, width=100)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(log_text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def log(self, message):
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)

    def load_sido(self):
        url = 'https://new.land.naver.com/api/regions/list?cortarNo=0000000000'
        resp = requests.get(url, headers=headers, cookies=cookies)
        data = resp.json()
        self.sido_list = data['regionList']
        self.sido_cb['values'] = [item['cortarName'] for item in self.sido_list]
        self.sido_cb.set('')
        self.gugun_cb.set('')
        self.dong_cb.set('')
        self.complex_listbox.delete(0, tk.END)
        self.collect_listbox.delete(0, tk.END)
        self.collect_list.clear()
        self.selected_complex_no = None

    def on_sido_selected(self, event=None):
        idx = self.sido_cb.current()
        if idx < 0:
            return
        sido_cortarNo = self.sido_list[idx]['cortarNo']
        url = f'https://new.land.naver.com/api/regions/list?cortarNo={sido_cortarNo}'
        resp = requests.get(url, headers=headers, cookies=cookies)
        data = resp.json()
        self.gugun_list = data['regionList']
        self.gugun_cb['values'] = [item['cortarName'] for item in self.gugun_list]
        self.gugun_cb.set('')
        self.dong_cb.set('')
        self.complex_listbox.delete(0, tk.END)
        self.selected_complex_no = None

    def on_gugun_selected(self, event=None):
        idx = self.gugun_cb.current()
        if idx < 0:
            return
        gugun_cortarNo = self.gugun_list[idx]['cortarNo']
        url = f'https://new.land.naver.com/api/regions/list?cortarNo={gugun_cortarNo}'
        resp = requests.get(url, headers=headers, cookies=cookies)
        data = resp.json()
        self.dong_list = data['regionList']
        self.dong_cb['values'] = [item['cortarName'] for item in self.dong_list]
        self.dong_cb.set('')
        self.complex_listbox.delete(0, tk.END)
        self.selected_complex_no = None

    def on_dong_selected(self, event=None):
        idx = self.dong_cb.current()
        if idx < 0:
            return
        dong_cortarNo = self.dong_list[idx]['cortarNo']
        url = f'https://new.land.naver.com/api/regions/complexes?cortarNo={dong_cortarNo}&realEstateType=APT:ABYG:JGC:PRE'
        resp = requests.get(url, headers=headers, cookies=cookies)
        data = resp.json()
        self.complex_list = data.get('complexList', [])
        self.complex_listbox.delete(0, tk.END)
        for item in self.complex_list:
            self.complex_listbox.insert(tk.END, f"{item['complexName']} ({item['detailAddress']})")
        self.selected_complex_no = None

    def on_complex_double_click(self, event=None):
        idxs = self.complex_listbox.curselection()
        if not idxs:
            return
        idx = idxs[0]
        complex_info = self.complex_list[idx]
        # 중복 방지
        if any(c['complexNo'] == complex_info['complexNo'] for c in self.collect_list):
            self.log(f"이미 수집 목록에 있는 단지입니다: {complex_info['complexName']} ({complex_info['detailAddress']})")
            return
        self.collect_list.append(complex_info)
        self.collect_listbox.insert(tk.END, f"{complex_info['complexName']} ({complex_info['detailAddress']})")

    def remove_from_collect_list(self):
        idxs = self.collect_listbox.curselection()
        if not idxs:
            return
        idx = idxs[0]
        self.collect_listbox.delete(idx)
        del self.collect_list[idx]

    def get_property_data(self, max_pages, complex_no):
        all_property_data = []
        for page in range(1, max_pages + 1):
            if not self.is_running:
                break
            url = f'https://new.land.naver.com/api/articles/complex/{complex_no}?realEstateType=APT%3APRE&tradeType=A1&tag=%3A%3A%3A%3A%3A%3A%3A%3A&rentPriceMin=0&rentPriceMax=900000000&priceMin=0&priceMax=900000000&areaMin=0&areaMax=900000000&oldBuildYears&recentlyBuildYears&minHouseHoldCount=377&maxHouseHoldCount&showArticle=true&sameAddressGroup=true&minMaintenanceCost&maxMaintenanceCost&priceType=RETAIL&directions=&page={page}&complexNo={complex_no}&buildingNos=&areaNos=&type=list&order=dateDesc'
            response = requests.get(
                url,
                cookies=cookies,
                headers=headers,
            )
            data = response.json()
            articles = data['articleList']
            for article in articles:
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
                all_property_data.append(property_info)
        return all_property_data

    def crawling_task(self):
        if not self.collect_list:
            messagebox.showerror("오류", "수집 목록에 아파트(단지)를 추가해주세요.")
            self.stop_crawling()
            return
        while self.is_running:
            for idx, complex_info in enumerate(self.collect_list):
                if not self.is_running:
                    break
                complex_no = complex_info['complexNo']
                complex_name = complex_info['complexName']
                self.log(f"[{idx+1}/{len(self.collect_list)}] 단지번호 {complex_no} ({complex_name}) 매물 정보를 수집합니다.")
                try:
                    existing_df = pd.read_excel(EXCEL_PATH)
                except FileNotFoundError:
                    existing_df = pd.DataFrame()
                existing_ids = set(existing_df['매물번호'].astype(str)) if not existing_df.empty else set()
                new_data = self.get_property_data(MAX_PAGES, complex_no)
                if not self.is_running:
                    break
                new_rows = [item for item in new_data if str(item['매물번호']) not in existing_ids]
                if new_rows:
                    self.log(f"{len(new_rows)}건의 새로운 매물이 발견되어 추가합니다.")
                    updated_df = pd.concat([existing_df, pd.DataFrame(new_rows)], ignore_index=True)
                    updated_df.to_excel(EXCEL_PATH, index=False)
                else:
                    self.log("새로운 매물이 없습니다.")
                # 단지별 10초 대기
                for _ in range(5):
                    if not self.is_running:
                        break
                    time.sleep(1)
            if not self.is_running:
                break
            self.log("모든 단지 수집 완료. 30분 대기...")
            for _ in range(1800):
                if not self.is_running:
                    break
                time.sleep(1)

    def start_crawling(self):
        if not self.collect_list:
            messagebox.showerror("오류", "수집 목록에 아파트(단지)를 추가해주세요.")
            return
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.sido_cb.config(state=tk.DISABLED)
        self.gugun_cb.config(state=tk.DISABLED)
        self.dong_cb.config(state=tk.DISABLED)
        self.complex_listbox.config(state=tk.DISABLED)
        self.collect_listbox.config(state=tk.DISABLED)
        self.remove_button.config(state=tk.DISABLED)
        Thread(target=self.crawling_task, daemon=True).start()

    def stop_crawling(self):
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.sido_cb.config(state=tk.NORMAL)
        self.gugun_cb.config(state=tk.NORMAL)
        self.dong_cb.config(state=tk.NORMAL)
        self.complex_listbox.config(state=tk.NORMAL)
        self.collect_listbox.config(state=tk.NORMAL)
        self.remove_button.config(state=tk.NORMAL)
        self.log("크롤링이 중지되었습니다.")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = NaverPropertyCrawler()
    app.run()