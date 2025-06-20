import requests
from bs4 import BeautifulSoup
import json

# 저장되는 json 파일 이름
file_name = "../school_inf.json"



for d in all_notices:
    print(d)

with open(file_name, "w", encoding="utf-8") as f:
    json.dump(all_notices, f, ensure_ascii=False, indent=2)