#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import re
import requests
from datetime import datetime, date
import calendar
from bs4 import BeautifulSoup
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import torch.nn as nn
from tqdm import tqdm
import time
import os

# 환경변수로 설정
os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # GPU 1번만 사용

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
                "operation_overview": {
                    "period": "2025. 3. 4.(화) ~ 2025. 12. 19.(금), 총 150일",
                    "location": "교내(대덕캠퍼스) 및 캠퍼스 순환(대덕↔보운)",
                    "buses": "학교버스 총 2대, 41인승",
                    "operation_days": "학기 중 주간 운영(월~금)",
                    "non_operation": "공휴일·대체공휴일·개교기념일·방학·수학능력시험일(10시 이전까지) 등 미운영"
                },

                "campus_internal": {
                    "name": "교내 순환 (대덕캠퍼스 내)",
                    "operation_period": "학기 중 3.4.～12.19. 총 150일 (월～금)",
                    "buses": "1대",
                    "frequency": "1일 총 10회 운영",
                    "first_bus": "08:30",
                    "last_bus": "17:30",
                    "morning_special": "등교 1회차: 월평역 출발 08:20 → 정심화 국제문화회관 도착",
                    "schedule": [
                        "08:30", "09:30", "09:40", "10:30", "11:30",
                        "13:30", "14:30", "15:30", "16:30", "17:30"
                    ],

                    "route_stops": [
                        "정심화 국제문화회관", "사회과학대학 입구(한누리회관 뒤)",
                        "서문(공동실험실습관 앞)", "음악 2호관 앞", "공동동물실험센터(회차)",
                        "체육관 입구", "예술대학 앞", "도서관 앞(대학본부 옆)", "학생생활관 3거리",
                        "농업생명과학대학 앞", "동문주차장"
                    ]
                },

                "campus_circulation": {
                    "name": "캠퍼스 순환 (대덕↔보운)",
                    "operation_period": "학기 중 (월～금)",
                    "buses": "1대",
                    "frequency": "1일 총 1회 운영 (회차)",
                    "departure": "08:10 (대덕 골프연습장)",
                    "arrival": "08:50 (보운캠퍼스)",
                    "route": "골프연습장(08:10) → 중앙도서관(08:11) → 산학연교육연구관(08:12) → 충남대입구 버스정류장(08:13) → 월평역(08:15) → 보운캠퍼스(08:50)",
                    "return_route": "보운캠퍼스 → 다솔아파트 건너편 → 제2학생회관 → 중앙도서관 → 골프연습장"
                },

                "external_stops": {
                    "월평역": "3번 출구 건너편(테니스장 앞 버스정류장 부근)",
                    "충남대입구": "버스정류장(홈플러스유성점방면)",
                    "보운캠퍼스": "회차지점",
                    "다솔아파트": "건너편"
                },

                "important_notes": [
                    "교통상황 등으로 인해 전 구간에서 5분 내외 오차 발생 가능",
                    "탑승자는 사전 대기 필요",
                    "학교 버스가 보이면 탑승 의사를 알려주세요",
                    "운행시간은 천재지변, 학교행사, 교통상황, 탑승 인원 등에 따라 변경 가능",
                    "세부 운행시간은 이용자 및 운행 추이에 따라 논의를 거쳐 변동 가능"
                ],

                "contact": "총무과(042-821-5114) 또는 학생처 학생과",
                "last_updated": "2025. 2. 18.(화), 학생처 학생과"
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
    """완전한 캠퍼스 챗봇 - AWQ 양자화 모델 사용"""

    def __init__(self, model_name = "Qwen/Qwen3-14B-AWQ"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"🖥️ 디바이스: {self.device}")
        print(f"🤖 모델: {model_name}")
        print("🔧 AWQ 4-bit 양자화 모델 사용")

        # 완전한 지식 베이스 초기화
        self.knowledge_base = CompleteCampusKnowledgeBase()
        print("📚 완전한 지식 베이스 로드 완료")

        # 모델 로드
        self.load_model()
        print("🤖 AWQ 챗봇 초기화 완료")

    def load_model(self):
        """AWQ 양자화 모델 로드"""
        try:
            print("🔄 AWQ 양자화 Qwen 모델 로딩 중...")

            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )

            # pad_token 설정
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # AWQ 모델 로드 (이미 양자화되어 있음)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )

            self.model.eval()
            print("✅ AWQ 모델 로딩 완료 (메모리 절약: ~70%)")

        except Exception as e:
            print(f"❌ AWQ 모델 로딩 실패: {e}")
            print("💡 AWQ 모델이 없을 수 있습니다. 일반 모델로 fallback 시도...")

            # Fallback to regular model
            try:
                fallback_model = "Qwen/Qwen2.5-7B-Instruct"
                print(f"🔄 {fallback_model}로 fallback 시도...")

                self.tokenizer = AutoTokenizer.from_pretrained(fallback_model, trust_remote_code=True)
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token

                self.model = AutoModelForCausalLM.from_pretrained(
                    fallback_model,
                    device_map="auto",
                    torch_dtype=torch.float16,
                    trust_remote_code=True
                )

                self.model_name = fallback_model
                print("✅ Fallback 모델 로딩 완료")

            except Exception as fallback_error:
                print(f"❌ Fallback 모델도 실패: {fallback_error}")
                raise

    def create_rich_context(self, relevant_info):
        """풍부한 컨텍스트 생성 (길이 최적화)"""
        context = "=== 충남대학교 종합 정보 ===\n\n"

        for info_type, info_data in relevant_info:
            context += f"【{info_type}】\n"

            if info_type == "최신공지" and isinstance(info_data, list):
                for i, notice in enumerate(info_data[:2], 1):  # 3개 → 2개로 축소
                    context += f"{i}. {notice.get('title', 'N/A')}\n"

            elif info_type == "오늘메뉴":
                if info_data.get('status') == "크롤링 성공":
                    context += f"날짜: {info_data['date']} ({info_data['day']}요일)\n"
                    if 'items' in info_data and info_data['items']:
                        context += f"메뉴: {', '.join(info_data['items'][:3])}\n"  # 5개 → 3개로 축소
                else:
                    context += f"상태: {info_data.get('message', '정보 없음')}\n"

            elif isinstance(info_data, dict):
                # 핵심 정보만 포함하도록 축소
                key_count = 0
                for key, value in info_data.items():
                    if key_count >= 3:  # 최대 3개 항목만
                        break
                    if isinstance(value, dict):
                        context += f"• {key}: {str(value)[:50]}...\n"  # 길이 제한
                    else:
                        context += f"• {key}: {str(value)[:100]}\n"  # 길이 제한
                    key_count += 1

            context += "\n"

            # 전체 컨텍스트 길이 제한
            if len(context) > 1500:  # 길이 제한 강화
                context = context[:1500] + "...\n"
                break

        return context

    def create_balanced_prompt(self, question, context):
        """메모리 효율적인 프롬프트 생성"""
        now = datetime.now()
        today = date.today()
        weekday = today.strftime('%A')

        # 간단한 시간 정보만
        current_context = f"현재: {now.strftime('%Y-%m-%d %H:%M')} ({weekday})"

        prompt = f"""/no_think <|im_start|>system
                당신은 충남대학교 학생 도우미입니다. 
                다음 정보를 바탕으로 간결하고 정확한 답변을 해주세요.
                {current_context}
                {context}
                <|im_end|>
                <|im_start|>user
                {question}
                <|im_end|>
                <|im_start|>assistant
                """
        return prompt

    def extract_answer_from_response(self, full_response, prompt):
        """응답에서 실제 답변 부분만 추출 - 간소화된 버전"""
        try:
            # 1. 프롬프트 부분 제거
            if full_response.startswith(prompt):
                answer = full_response[len(prompt):].strip()
            else:
                # 2. assistant 토큰 이후 부분 추출
                if "<|im_start|>assistant" in full_response:
                    parts = full_response.split("<|im_start|>assistant")
                    answer = parts[-1].strip()
                else:
                    answer = full_response.strip()

            # 3. 특수 토큰들 제거
            answer = re.sub(r'<\|im_end\|>', '', answer)
            answer = re.sub(r'<\|im_start\|>.*?>', '', answer)

            # 4. 시스템 프롬프트가 답변에 포함된 경우 제거
            if "당신은 충남대학교 학생 도우미입니다" in answer:
                parts = answer.split("assistant")
                if len(parts) > 1:
                    answer = parts[-1].strip()

            # 5. 컨텍스트 정보가 답변에 포함된 경우 제거
            if "=== 충남대학교 종합 정보 ===" in answer:
                parts = answer.split("간결하고 정확한 답변을 해주세요.")
                if len(parts) > 1:
                    answer = parts[-1].strip()

            # 6. 역할 태그들 제거
            answer = re.sub(r'^(system|user|assistant)\s*', '', answer)
            answer = re.sub(r'\n(system|user|assistant)\s*', '\n', answer)

            # 7. 앞뒤 공백 및 개행 정리
            answer = answer.strip()

            # 8. 빈 답변이면 None 반환
            if not answer or len(answer.strip()) < 3:
                return None

            return answer

        except Exception as e:
            print(f"⚠️ 답변 추출 중 오류: {e}")
            return None


    def generate_comprehensive_answer(self, question, max_new_tokens=30000):
        """메모리 최적화된 답변 생성"""
        try:
            print(f"🔍 질문 분석 중: {question}")

            # 메모리 정리
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # 1. 관련 정보 검색
            relevant_info = self.knowledge_base.search_comprehensive_info(question)

            # 2. 컨텍스트 생성 (크기 제한)
            context = self.create_rich_context(relevant_info)

            # 3. 프롬프트 생성
            prompt = self.create_balanced_prompt(question, context)

            # 4. 토크나이징 (길이 제한 강화)
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=3000  # 더 짧게 제한
            ).to(self.device)

            # 메모리 정리
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # 5. 답변 생성 (메모리 절약 설정)
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,  # 더 짧게 제한
                    do_sample=True,
                    temperature=0.7,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )

            # 즉시 메모리 해제
            del inputs
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # 6. 디코딩
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

            # 메모리 해제
            del outputs
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # 7. 답변 추출 (프롬프트와 특수 토큰 제거)
            answer = self.extract_answer_from_response(full_response, prompt)

            # 8. 답변 품질 검사
            if not answer or len(answer) < 5:
                return self.get_fallback_answer(question)

            print("✅ 답변 생성 완료")
            return answer

        except torch.cuda.OutOfMemoryError:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print("❌ GPU 메모리 부족 - Fallback 사용")
            return self.get_fallback_answer(question)

        except Exception as e:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print(f"❌ 답변 생성 오류: {e}")
            return self.get_fallback_answer(question)

    def get_fallback_answer(self, question):
        """간단한 Fallback 답변 (메모리 절약)"""
        question_lower = question.lower()

        if any(word in question_lower for word in ['셔틀', '버스']):
            return """🚌 2025년 충남대 셔틀버스 안내

📍 교내순환: 08:30~17:30 (1일 10회)
시간: 08:30, 09:30, 09:40, 10:30, 11:30, 13:30, 14:30, 15:30, 16:30, 17:30

📍 등교전용: 월평역 08:20 출발 → 정심화 국제문화회관
📍 캠퍼스순환: 08:10 대덕 출발 → 08:50 보운 도착

📞 문의: 총무과 042-821-5114"""

        elif any(word in question_lower for word in ['졸업', '학점']):
            return "충남대학교 졸업요건은 130학점 이상입니다. 공학계열은 140학점이 필요합니다. 자세한 문의: 학사지원과 042-821-5025"

        elif any(word in question_lower for word in ['식단', '메뉴']):
            return "학생식당: 한식 4,000원, 양식 5,000원. 운영시간: 11:30-14:00, 17:30-19:00. 생협: 042-821-5890"

        else:
            return "문의사항은 관련 부서로 연락주세요. 학사지원과 042-821-5025, 총무과 042-821-5114"

    def process_test_file(self, test_file_path, output_file_path):
        """개별 처리로 메모리 절약"""
        try:
            if not os.path.exists(test_file_path):
                print(f"❌ 테스트 파일이 없습니다: {test_file_path}")
                return False

            with open(test_file_path, 'r', encoding='utf-8') as f:
                test_data = json.load(f)

            results = []
            print(f"📝 AWQ 모델 개별 처리 중... (총 {len(test_data)}개)")

            for i, item in enumerate(test_data):
                try:
                    print(f"🔄 {i+1}/{len(test_data)}: {item['user'][:30]}...")

                    # 각 질문마다 메모리 정리
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

                    answer = self.generate_comprehensive_answer(item['user'])

                    results.append({
                        "user": item['user'],
                        "model": answer
                    })

                    # 5개마다 중간 저장 및 메모리 정리
                    if (i + 1) % 3 == 0:
                        print(f"💾 중간 저장... ({i+1}개 완료)")
                        self.save_partial_results(results, output_file_path)
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()

                except Exception as e:
                    print(f"❌ 질문 {i+1} 실패: {e}")
                    results.append({
                        "user": item['user'],
                        "model": f"처리 실패: {str(e)}"
                    })
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

            # 최종 저장
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            print(f"✅ AWQ 모델 결과 저장 완료: {output_file_path}")
            return True

        except Exception as e:
            print(f"❌ 테스트 파일 처리 중 오류: {e}")
            return False

    def save_partial_results(self, results, output_file_path):
        """부분 결과 저장"""
        try:
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 중간 저장 실패: {e}")

    def chat_interactive(self):
        """대화형 채팅"""
        print("\n🤖 충남대 AWQ 양자화 RAG 챗봇입니다!")
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
    print("🎓 충남대 Campus RAG ChatBot (AWQ 양자화)")
    print("📡 실시간 크롤링 + 정적 정보 + AWQ 4-bit 양자화")
    print("🔧 메모리 최적화 버전")
    print("=" * 60)

    try:
        # AWQ 양자화 RAG 챗봇 초기화
        chatbot = CompleteCampusChatBot(
            model_name = "Qwen/Qwen3-14B-AWQ"
        )

        # 테스트 파일 처리
        test_file_path = "./data/shuttle_test_chat.json"
        output_file_path = "./outputs/think_shuttle_test_chat_output.json"

        if os.path.exists(test_file_path):
            print(f"📂 테스트 파일 발견: {test_file_path}")
            success = chatbot.process_test_file(test_file_path, output_file_path)

            if success:
                print("✅ AWQ 양자화 챗봇 테스트 완료!")

                # 결과 미리보기
                with open(output_file_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)

                print("\n📋 결과 미리보기 (처음 3개):")
                for i, result in enumerate(results[:3]):
                    print(f"\n{i + 1}. 질문: {result['user']}")
                    print(f"   답변: {result['model']}")
                    print("-" * 60)

                # 모델 정보 출력
                print(f"\n🤖 사용된 모델: {chatbot.model_name}")
                print(f"🔧 양자화: AWQ 4-bit")
                print(f"🖥️ 실행 디바이스: {chatbot.device}")
                print(f"💾 예상 메모리 절약: 70%")

            else:
                print("❌ 테스트 실패!")
        else:
            print(f"⚠️ 테스트 파일이 없습니다: {test_file_path}")
            print("대화형 모드로 전환합니다.")

            # 대화형 테스트
            sample_questions = [
                "셔틀버스 시간표를 알려주세요",
                "월평역에서 학교까지 셔틀버스 있나요?",
                "졸업까지 몇 학점이 필요한가요?",
                "오늘 학식 메뉴가 뭔가요?"
            ]

            print("\n🧪 샘플 질문으로 테스트:")
            for i, question in enumerate(sample_questions):
                print(f"\n🤖 질문 {i + 1}: {question}")
                answer = chatbot.generate_comprehensive_answer(question)
                print(f"📝 답변: {answer}")
                print("-" * 60)

    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        print("💡 AWQ 모델이 없거나 GPU 메모리 부족일 수 있습니다")
        print("💡 fallback 모델로 자동 전환됩니다")


if __name__ == "__main__":
    main()