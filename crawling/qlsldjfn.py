import requests
from bs4 import BeautifulSoup
import json

# 저장되는 json 파일 이름
file_name = "../school_inf.json"

# 기본 URL
BASE_URL = "https://plus.cnu.ac.kr/_prog/_board/"

# 요청 파라미터
PARAMS = {
    "code": "sub07_0702",
    "site_dvs_cd": "kr",
    "menu_dvs_cd": "0702",
    "skey": "",
    "sval": "",
    "site_dvs": "",
    "ntt_tag": "",
    "GotoPage": 1
}

def get_notice_list(page=1):
    PARAMS["GotoPage"] = page
    response = requests.get(BASE_URL, params=PARAMS)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    # board_list 클래스의 div 객체 찾기
    board_div = soup.find('div', class_='board_list')
    if not board_div:
        print("📛 'board_list' 클래스를 가진 div를 찾지 못했습니다.")
        return []

    rows = board_div.find_all('tr')
    notices = []

    for row in rows[1:]:  # 첫 번째는 헤더
        cols = row.find_all('td')
        if len(cols) < 4:
            continue

        title_tag = cols[1].find('a')
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)

        # 작성자
        writer = cols[2].get_text(strip=True)

        # 날짜
        date = cols[3].get_text(strip=True)

        notices.append({
            'title': title,
            'writer': writer,
            'date': date
        })

    return notices

all_notices = []
for page in range(1, 6):  # 예: 5페이지까지 크롤링
    notices = get_notice_list(page)
    if not notices:
        break
    all_notices.extend(notices)

print(f"총 {len(all_notices)}개의 게시물 수집 완료")

for d in all_notices:
    print(d)

with open(file_name, "w", encoding="utf-8") as f:
    json.dump(all_notices, f, ensure_ascii=False, indent=2)