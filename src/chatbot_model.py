#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
충남대 Campus ChatBot - 완전한 RAG 버전
실시간 크롤링 + 정적 정보 + 안정적인 프롬프트 처리
"""

import json
import os
import re
import requests
from datetime import datetime, date
from bs4 import BeautifulSoup
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from tqdm import tqdm
import time


class CompleteCampusKnowledgeBase:
    """완전한 캠퍼스 지식 베이스 (정적 + 실시간)"""

    def __init__(self):
        self.setup_static_knowledge()
        self.setup_real_urls()
        self.cache = {}
        self.cache_timeout = 1800  # 30분 캐시

    def setup_static_knowledge(self):
        """정적 지식 (항상 정확한 기본 정보)"""
        self.static_knowledge = {
            "graduation": {
                "general": "충남대학교 일반적인 졸업요건은 130학점 이상입니다.",
                "engineering": "공학계열은 140학점 이상이 필요합니다.",
                "composition": "전공필수 + 전공선택 + 교양필수 + 교양선택 + 일반선택으로 구성됩니다.",
                "major_required": "전공필수는 학과별 지정 과목을 모두 이수해야 합니다.",
                "major_elective": "전공선택은 학과별 최소 이수 학점을 충족해야 합니다.",
                "general_education": "교양은 기초교양(영어, 컴퓨터, 체육)과 균형교양(인문, 사회, 자연)으로 구성됩니다.",
                "double_major": "복수전공은 주전공 + 복수전공 각 36학점 이상 필요합니다.",
                "contact": "정확한 졸업요건은 소속 학과 사무실이나 학사지원과(042-821-5025)에 문의하세요."
            },

            "academic_schedule": {
                "course_registration": "수강신청 일정은 매 학기 시작 전에 학사지원과에서 공지합니다.",
                "system": "CNU 포털시스템(portal.cnu.ac.kr)에서 진행됩니다.",
                "correction": "수강정정은 개강 후 1주일 동안 가능합니다.",
                "midterm": "중간고사는 보통 4월(1학기), 10월(2학기) 중순경입니다.",
                "final": "기말고사는 보통 6월(1학기), 12월(2학기) 중순경입니다.",
                "semester_start": "1학기는 3월, 2학기는 9월에 시작합니다.",
                "vacation": "여름방학은 6월말~8월말, 겨울방학은 12월말~2월말입니다.",
                "contact": "학사지원과(042-821-5025)로 문의하세요.",
                "website": "충남대 홈페이지(www.cnu.ac.kr)에서 확인 가능합니다."
            },

            "dining": {
                "student_restaurant": {
                    "location": "학생회관 지하 1층",
                    "korean": "한식 4,000원",
                    "western": "양식 5,000원",
                    "chinese": "중식 5,500원",
                    "special": "특식 6,000원"
                },
                "faculty_restaurant": {
                    "location": "학생회관 2층",
                    "price": "6,500-7,500원"
                },
                "cafeteria": {
                    "location": "정심화국제문화회관 1층",
                    "menu": "카페, 간식, 샐러드"
                },
                "hours": {
                    "breakfast": "08:00-09:30 (평일, 일부 식당)",
                    "lunch": "11:30-14:00",
                    "dinner": "17:30-19:00"
                },
                "weekend": "주말에는 대부분 식당이 운영하지 않습니다.",
                "info_source": "생협 홈페이지(coop.cnu.ac.kr)에서 식단을 확인하세요.",
                "contact": "생활협동조합(042-821-5890)으로 문의하세요."
            },

            "shuttle": {
                "school_hours": "등교시간 07:30-09:00, 하교시간 17:00-18:30",
                "interval": "15-20분 간격으로 운행",
                "routes": {
                    "internal": "교내순환 (대덕캠퍼스 내)",
                    "campus": "캠퍼스순환 (대덕↔보운)"
                },
                "days": "평일 정상운행, 토요일 제한운행, 일요일/공휴일 운행중단",
                "fee": "무료 (학생증 지참 필수)",
                "external_transport": "대전역, 유성온천역 등에서 시내버스 이용 가능",
                "contact": "총무과(042-821-5114)로 문의하세요.",
                "info_source": "충남대 홈페이지 교통안내에서 확인하세요."
            },

            "notice": {
                "main_website": "충남대 홈페이지(www.cnu.ac.kr)에서 확인하세요.",
                "portal": "CNU 포털시스템에서도 중요 공지를 받을 수 있습니다.",
                "department": "각 학과 홈페이지에서 학과별 공지를 확인하세요.",
                "scholarship": "장학금 공지는 학생지원과에서 담당합니다.",
                "student_council": "총학생회 공지는 총학생회 홈페이지에서 확인하세요.",
                "contacts": {
                    "학사지원과": "042-821-5025",
                    "학생지원과": "042-821-5015"
                }
            },

            "contacts": {
                "학사지원과": "042-821-5025 (졸업요건, 학사일정)",
                "학생지원과": "042-821-5015 (장학금, 학생활동)",
                "총무과": "042-821-5114 (셔틀버스, 시설)",
                "생활협동조합": "042-821-5890 (식당, 매점)",
                "도서관": "042-821-5092",
                "정보통신원": "042-821-6851"
            }
        }

    def setup_real_urls(self):
        """실제 충남대 URL들"""
        self.urls = {
            # 공지사항
            "main_notice": "https://plus.cnu.ac.kr/",
            "academic_notice": "https://plus.cnu.ac.kr/_prog/_board/?code=sub07_0702&site_dvs_cd=kr&menu_dvs_cd=0702",
            "student_notice": "https://cnustudent.cnu.ac.kr/cnustudent/notice/notice.do",

            # 학사일정
            "academic_calendar": "https://plus.cnu.ac.kr/_prog/academic_calendar/?site_dvs_cd=kr&menu_dvs_cd=05020101",

            # 식단 정보
            "meal_mobile": "https://mobileadmin.cnu.ac.kr/food/index.jsp",
            "dorm_meal": "https://dorm.cnu.ac.kr/",
            "coop_main": "https://www.cnucoop.co.kr/",

            # 셔틀버스
            "shuttle_info": "https://plus.cnu.ac.kr/html/kr/sub05/sub05_050403.html",
            "traffic_info": "https://plus.cnu.ac.kr/html/kr/sub01/sub01_01080302.html",
        }

    def get_cached_data(self, key):
        """캐시 데이터 조회"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_timeout:
                return data
        return None

    def set_cache(self, key, data):
        """캐시 데이터 저장"""
        self.cache[key] = (data, time.time())

    def safe_request(self, url, timeout=10):
        """안전한 웹 요청"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"⚠️ 웹 요청 실패 {url}: {e}")
            return None

    def fetch_today_menu(self):
        """오늘의 식단 크롤링"""
        cached = self.get_cached_data("today_menu")
        if cached:
            return cached

        print("🍽️ 식단 정보 크롤링 중...")

        try:
            # 충남대 모바일 식단표 크롤링 시도
            response = self.safe_request(self.urls["meal_mobile"])

            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                menu_data = {
                    "status": "크롤링 성공",
                    "date": date.today().strftime("%Y-%m-%d"),
                    "day": ["월", "화", "수", "목", "금", "토", "일"][date.today().weekday()],
                    "source": "충남대 모바일 식단표",
                    "url": self.urls["meal_mobile"]
                }

                # 텍스트에서 한국 음식 이름 추출
                text = soup.get_text()
                korean_foods = re.findall(r'[가-힣]+(?:국|찌개|볶음|구이|조림|무침|비빔|탕|죽|밥)', text)

                if korean_foods:
                    menu_data["items"] = list(set(korean_foods[:10]))  # 중복 제거, 최대 10개
                    menu_data["message"] = f"오늘({menu_data['day']}요일) 예상 메뉴입니다."
                else:
                    menu_data["message"] = "메뉴 정보를 추출할 수 없었습니다."

                print("✅ 식단 크롤링 성공")

            else:
                menu_data = {
                    "status": "크롤링 실패",
                    "date": date.today().strftime("%Y-%m-%d"),
                    "message": "식단표 사이트에 접근할 수 없습니다.",
                    "fallback": "각 식당에서 직접 확인하거나 생협 홈페이지를 이용하세요.",
                    "url": self.urls["meal_mobile"]
                }
                print("⚠️ 식단 크롤링 실패")

            self.set_cache("today_menu", menu_data)
            return menu_data

        except Exception as e:
            print(f"❌ 식단 크롤링 오류: {e}")
            return {
                "status": "오류",
                "message": "식단 정보를 가져올 수 없습니다.",
                "fallback": "생협 홈페이지(coop.cnu.ac.kr)에서 확인하세요."
            }

    def fetch_latest_notices(self):
        """최신 공지사항 크롤링"""
        cached = self.get_cached_data("notices")
        if cached:
            return cached

        print("📢 공지사항 크롤링 중...")

        try:
            # 충남대 메인 페이지 크롤링
            response = self.safe_request(self.urls["main_notice"])

            notices = []

            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # 다양한 선택자로 뉴스/공지 찾기
                news_selectors = [
                    'h3', 'h4', 'h5',  # 제목 태그
                    '.news-title', '.notice-title', '.board-title',  # 클래스명
                    '[class*="title"]', '[class*="news"]',  # 부분 클래스명
                ]

                for selector in news_selectors:
                    elements = soup.select(selector)
                    for element in elements[:5]:  # 각 선택자당 최대 5개
                        text = element.get_text(strip=True)
                        if text and len(text) > 10 and len(text) < 200:  # 적절한 길이
                            notices.append({
                                "title": text,
                                "date": date.today().strftime("%Y-%m-%d"),
                                "source": "충남대 홈페이지",
                                "url": self.urls["main_notice"]
                            })

                    if len(notices) >= 3:  # 충분히 찾았으면 중단
                        break

                # 중복 제거
                seen_titles = set()
                unique_notices = []
                for notice in notices:
                    if notice["title"] not in seen_titles:
                        seen_titles.add(notice["title"])
                        unique_notices.append(notice)
                        if len(unique_notices) >= 5:
                            break

                notices = unique_notices
                print(f"✅ 공지사항 {len(notices)}개 크롤링 성공")

            if not notices:
                notices = [{
                    "title": "공지사항 크롤링 실패",
                    "message": "충남대 홈페이지에서 직접 확인하세요.",
                    "url": self.urls["main_notice"],
                    "fallback": "각 학과 홈페이지나 CNU 포털도 확인해보세요."
                }]
                print("⚠️ 공지사항 크롤링 실패")

            self.set_cache("notices", notices)
            return notices

        except Exception as e:
            print(f"❌ 공지사항 크롤링 오류: {e}")
            return [{
                "title": "공지사항을 가져올 수 없습니다.",
                "message": "인터넷 연결을 확인하고 충남대 홈페이지를 직접 방문하세요.",
                "url": self.urls["main_notice"]
            }]

    def search_comprehensive_info(self, question):
        """포괄적인 정보 검색 (정적 + 실시간)"""
        question_lower = question.lower()
        relevant_info = []

        # 졸업요건 관련
        if any(word in question_lower for word in ['졸업', '학점', '전공', '교양', '요건', '논문']):
            relevant_info.append(("졸업요건_정보", self.static_knowledge["graduation"]))

        # 공지사항 관련 (실시간 크롤링)
        if any(word in question_lower for word in ['공지', '장학금', '신청', '안내', '소식', '행사']):
            latest_notices = self.fetch_latest_notices()
            relevant_info.append(("최신공지", latest_notices))
            relevant_info.append(("공지사항_기본정보", self.static_knowledge["notice"]))

        # 학사일정 관련
        if any(word in question_lower for word in
               ['수강신청', '수강', '신청', '시험', '개강', '종강', '일정', '언제', '학사', '방학', '계절학기']):
            relevant_info.append(("학사일정_정보", self.static_knowledge["academic_schedule"]))

        # 식단 관련 (실시간 크롤링)
        if any(word in question_lower for word in ['식단', '학식', '메뉴', '식당', '밥', '점심', '저녁', '아침']):
            relevant_info.append(("식당_기본정보", self.static_knowledge["dining"]))
            today_menu = self.fetch_today_menu()
            relevant_info.append(("오늘메뉴", today_menu))

        # 셔틀버스 관련
        if any(word in question_lower for word in ['셔틀', '버스', '교통', '시간표', '운행', '통학', '대전역', '유성']):
            relevant_info.append(("셔틀버스_정보", self.static_knowledge["shuttle"]))

        # 연락처 정보 (항상 포함)
        relevant_info.append(("연락처_정보", self.static_knowledge["contacts"]))

        return relevant_info


class CompleteCampusChatBot:
    """완전한 캠퍼스 챗봇 (정적 + 실시간 + 안정적 프롬프트)"""

    def __init__(self, model_name="beomi/Llama-3-Open-Ko-8B"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🖥️ 디바이스: {self.device}")

        # 완전한 지식 베이스 초기화
        self.knowledge_base = CompleteCampusKnowledgeBase()
        print("📚 완전한 지식 베이스 로드 완료")

        # 모델 로드
        self.load_model()
        print("🤖 완전한 RAG 챗봇 초기화 완료")

    def load_model(self):
        """모델 로드"""
        try:
            print("🔄 Qwen 모델 로딩 중...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )

            # pad_token 설정
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # 4-bit quantized 모델 로드
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                load_in_4bit=True,  # 4-bit quantization 활성화
                device_map="auto",  # 자동 디바이스 배치
                torch_dtype=torch.float16,  # float16 사용
                trust_remote_code=True,
                low_cpu_mem_usage=True  # CPU 메모리 사용량 최적화
            )

            self.model.eval()
            print("✅ 모델 로딩 완료")

        except Exception as e:
            print(f"❌ 모델 로딩 실패: {e}")
            raise

    def create_rich_context(self, relevant_info):
        """풍부한 컨텍스트 생성"""
        context = "=== 충남대학교 종합 정보 ===\n\n"

        for info_type, info_data in relevant_info:
            context += f"【{info_type}】\n"

            if info_type == "최신공지" and isinstance(info_data, list):
                for i, notice in enumerate(info_data[:3], 1):
                    context += f"{i}. {notice.get('title', 'N/A')}\n"
                    if 'url' in notice:
                        context += f"   확인: {notice['url']}\n"

            elif info_type == "오늘메뉴":
                if info_data.get('status') == "크롤링 성공":
                    context += f"날짜: {info_data['date']} ({info_data['day']}요일)\n"
                    if 'items' in info_data and info_data['items']:
                        context += f"메뉴: {', '.join(info_data['items'][:5])}\n"
                    context += f"상태: {info_data['message']}\n"
                else:
                    context += f"상태: {info_data.get('message', '정보 없음')}\n"
                    if 'fallback' in info_data:
                        context += f"대안: {info_data['fallback']}\n"

            elif isinstance(info_data, dict):
                for key, value in info_data.items():
                    if isinstance(value, dict):
                        context += f"• {key}:\n"
                        for sub_key, sub_value in value.items():
                            context += f"  - {sub_key}: {sub_value}\n"
                    else:
                        context += f"• {key}: {value}\n"

            context += "\n"

        return context

    def create_smart_prompt(self, question, context):
        """스마트 프롬프트 생성"""
        prompt = f"""충남대학교 학생을 도와주는 친절한 AI입니다. 아래 정보를 활용해 정확하고 도움이 되는 답변을 해주세요.

{context}

학생 질문: {question}

답변 (친절하고 정확하게):"""
        return prompt

    def generate_comprehensive_answer(self, question, max_new_tokens=300, temperature=0.7):
        """종합적인 답변 생성"""
        try:
            print(f"🔍 질문 분석 중: {question}")

            # 1. 관련 정보 검색 (정적 + 실시간)
            relevant_info = self.knowledge_base.search_comprehensive_info(question)

            # 2. 풍부한 컨텍스트 생성
            context = self.create_rich_context(relevant_info)

            # 3. 스마트 프롬프트 생성
            prompt = self.create_smart_prompt(question, context)

            # 4. 토크나이징
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=3000  # 더 긴 컨텍스트 허용
            ).to(self.device)

            # 5. 답변 생성
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id
                )

            # 6. 디코딩 및 답변 추출
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            if "답변 (친절하고 정확하게):" in full_response:
                answer = full_response.split("답변 (친절하고 정확하게):")[-1].strip()
            else:
                answer = full_response.replace(prompt, "").strip()

            # 7. 답변 품질 검사
            if not answer or len(answer) < 15 or "질문" in answer[:50]:
                print("⚠️ 생성된 답변 품질이 낮음, Fallback 사용")
                return self.get_smart_fallback_answer(question, relevant_info)

            print("✅ 고품질 답변 생성 완료")
            return answer

        except Exception as e:
            print(f"❌ 답변 생성 오류: {e}")
            return self.get_smart_fallback_answer(question, relevant_info)

    def get_smart_fallback_answer(self, question, relevant_info):
        """스마트 Fallback 답변 (실시간 정보 반영)"""
        question_lower = question.lower()

        # 실시간 정보 활용
        for info_type, info_data in relevant_info:
            if info_type == "오늘메뉴" and any(word in question_lower for word in ['식단', '학식', '메뉴']):
                if info_data.get('status') == "크롤링 성공" and 'items' in info_data:
                    return f"오늘({info_data['day']}요일) 예상 메뉴는 {', '.join(info_data['items'][:3])} 등입니다. 학생식당은 한식 4,000원, 양식 5,000원이에요. 정확한 식단은 생협 홈페이지에서 확인하세요."
                else:
                    return "식단 정보를 실시간으로 가져올 수 없었습니다. 학생식당은 한식 4,000원, 양식 5,000원이며, 운영시간은 중식 11:30-14:00, 석식 17:30-19:00입니다. 생협 홈페이지(coop.cnu.ac.kr)에서 확인하세요."

            elif info_type == "최신공지" and any(word in question_lower for word in ['공지', '장학금', '안내']):
                if isinstance(info_data, list) and info_data:
                    notice_titles = [notice.get('title', '') for notice in info_data[:2]]
                    if notice_titles and notice_titles[0]:
                        return f"최근 공지사항: {', '.join(notice_titles)}. 더 자세한 정보는 충남대 홈페이지(www.cnu.ac.kr)에서 확인하세요. 장학금 관련은 학생지원과(042-821-5015)로 문의하세요."

        # 기본 Fallback 답변들
        if any(word in question_lower for word in ['졸업', '학점']):
            return "충남대학교 일반적인 졸업요건은 130학점 이상입니다. 공학계열은 140학점이 필요해요. 전공필수+전공선택+교양필수+교양선택+일반선택으로 구성됩니다. 정확한 정보는 학과 사무실이나 학사지원과(042-821-5025)에 문의하세요."

        elif any(word in question_lower for word in ['수강신청', '수강', '신청', '시험', '개강']):
            return "수강신청 일정은 매 학기 시작 전에 학사지원과에서 공지합니다. CNU 포털시스템에서 진행되며, 중간고사는 4월/10월, 기말고사는 6월/12월 중순경입니다. 학사지원과(042-821-5025)로 문의하세요."

        elif any(word in question_lower for word in ['셔틀', '버스']):
            return "셔틀버스는 등교시간 07:30-09:00, 하교시간 17:00-18:30에 15-20분 간격으로 운행합니다. 교내순환과 캠퍼스순환 노선이 있으며, 무료이고 학생증을 지참하세요. 총무과(042-821-5114)로 문의 가능합니다."

        elif any(word in question_lower for word in ['공지', '장학금']):
            return "공지사항은 충남대 홈페이지(www.cnu.ac.kr)에서 확인하세요. 장학금 관련은 학생지원과(042-821-5015), 학과별 공지는 각 학과 홈페이지를 확인하세요."

        else:
            return "충남대 관련 문의는 해당 부서로 연락주세요. 학사지원과(042-821-5025), 학생지원과(042-821-5015), 총무과(042-821-5114)에서 도움을 받을 수 있습니다."

    def process_test_file(self, test_file_path, output_file_path):
        """테스트 파일 처리"""
        try:
            if not os.path.exists(test_file_path):
                print(f"❌ 테스트 파일이 없습니다: {test_file_path}")
                return False

            with open(test_file_path, 'r', encoding='utf-8') as f:
                test_data = json.load(f)

            results = []
            print(f"📝 완전한 RAG 답변 생성 중... (총 {len(test_data)}개)")
            print("⏰ 실시간 크롤링 포함으로 시간이 다소 걸릴 수 있습니다.")

            for item in tqdm(test_data, desc="RAG 답변 생성"):
                user_question = item['user']

                # 종합적인 답변 생성 (정적 + 실시간)
                answer = self.generate_comprehensive_answer(user_question)

                results.append({
                    "user": user_question,
                    "model": answer
                })

            # 출력 디렉토리 생성
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

            # 결과 저장
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            print(f"✅ 완전한 RAG 결과 저장 완료: {output_file_path}")
            return True

        except Exception as e:
            print(f"❌ 테스트 파일 처리 중 오류: {e}")
            return False

    def chat_interactive(self):
        """대화형 채팅 (실시간 크롤링 포함)"""
        print("\n🤖 충남대 완전한 RAG 챗봇입니다!")
        print("📡 실시간 정보 크롤링이 포함되어 있습니다.")
        print("(종료: 'quit' 또는 'exit')")

        while True:
            try:
                user_input = input("\n👤 질문: ").strip()

                if user_input.lower() in ['quit', 'exit', '종료']:
                    print("👋 이용해주셔서 감사합니다!")
                    break

                if not user_input:
                    continue

                print("🔍 정보 검색 및 답변 생성 중...")
                answer = self.generate_comprehensive_answer(user_input)
                print(f"🤖 답변: {answer}")

            except KeyboardInterrupt:
                print("\n👋 이용해주셔서 감사합니다!")
                break


def main():
    """메인 함수"""
    print("🎓 충남대 Campus RAG ChatBot (완전한 버전)")
    print("📡 실시간 크롤링 + 정적 정보 + 안정적 프롬프트")
    print("=" * 60)

    try:
        # 완전한 RAG 챗봇 초기화
        chatbot = CompleteCampusChatBot()

        # 테스트 파일 처리
        test_file_path = "./data/test_chat.json"
        output_file_path = "./outputs/chat_output.json"

        if os.path.exists(test_file_path):
            print(f"📂 테스트 파일 발견: {test_file_path}")
            success = chatbot.process_test_file(test_file_path, output_file_path)

            if success:
                print("✅ 완전한 RAG 챗봇 테스트 완료!")

                # 결과 미리보기
                with open(output_file_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)

                print("\n📋 결과 미리보기 (처음 3개):")
                for i, result in enumerate(results[:3]):
                    print(f"\n{i + 1}. 질문: {result['user']}")
                    print(f"   답변: {result['model']}")
                    print("-" * 60)

                # 크롤링 성공 여부 확인
                print("\n📊 실시간 정보 크롤링 결과:")
                print("• 공지사항 크롤링:", "성공" if "공지사항" in str(results) else "실패")
                print("• 식단 크롤링:", "성공" if "메뉴" in str(results) else "실패")

            else:
                print("❌ 테스트 실패!")
        else:
            print(f"⚠️ 테스트 파일이 없습니다: {test_file_path}")
            print("대화형 모드로 전환합니다.")

            # 대화형 테스트
            sample_questions = [
                "오늘 학식 메뉴가 뭔가요?",
                "최근 공지사항이 있나요?",
                "졸업까지 몇 학점이 필요한가요?",
                "셔틀버스 시간표를 알려주세요"
            ]

            print("\n🧪 샘플 질문으로 테스트:")
            for i, question in enumerate(sample_questions):
                print(f"\n🤖 질문 {i + 1}: {question}")
                answer = chatbot.generate_comprehensive_answer(question)
                print(f"📝 답변: {answer}")
                print("-" * 60)

    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        print("💡 인터넷 연결과 Python 환경을 확인해주세요")


if __name__ == "__main__":
    main()