import requests
from bs4 import BeautifulSoup
import json

date_str = "2025.06.18"

url = "https://mobileadmin.cnu.ac.kr/food/index.jsp?searchYmd="+str(date_str)+"&searchLang=OCL04.10&searchView=cafeteria&searchCafeteria=OCL03.02&Language_gb=OCL04.10"

response = requests.get(url)
response.raise_for_status()
response.encoding = "utf-8"

soup = BeautifulSoup(response.text, "html.parser")

def parse_meal_info(date_str):
    table = soup.find("table", class_="menu-tbl type-cap")
    meals = []
    current_meal_type = None

    if not table:
        print("식단표를 찾을 수 없습니다.")
        return meals

    # 실제 식당명 추출 (제2학생회관부터 시작)
    headers = table.find("thead").find_all("th")[2:]  # [0] = 구분, [1] = 제1학생회관 제외
    cafeteria_names = [th.get_text(strip=True) for th in headers]

    rows = table.find("tbody").find_all("tr")
    for row in rows:
        cols = row.find_all("td")

        if 'rowspan' in cols[0].attrs:
            current_meal_type = cols[0].get_text(strip=True)
            current_target = cols[1].get_text(strip=True)
            menu_cols = cols[2:]
        else:
            current_target = cols[0].get_text(strip=True)
            menu_cols = cols[1:]

        for idx, col in enumerate(menu_cols):
            if idx >= len(cafeteria_names):
                continue
            cafeteria = cafeteria_names[idx]
            menu_html = col.find("p")
            menu_text = menu_html.get_text(separator="\n", strip=True) if menu_html else col.get_text(strip=True)

            if "운영안함" in menu_text or not menu_text or "메뉴운영내역" in menu_text:
                continue

            menu_lines = menu_text.strip().split("\n")

            meals.append({
                "meal_type": current_meal_type,
                "target": current_target,
                "cafeteria": cafeteria,
                "menu": menu_lines
            })

    return {
        "date": date_str.replace(".", "-"),
        "meals": meals
    }

meal_data = parse_meal_info(date_str)
date_str = date_str.replace("-", "."),
json_filename = "meal_" + date_str[0] + ".json"
with open(json_filename, "w", encoding="utf-8") as f:
    json.dump(meal_data, f, ensure_ascii=False, indent=2)

print(f"✅ 식단 정보가 '{json_filename}'에 저장되었습니다.")