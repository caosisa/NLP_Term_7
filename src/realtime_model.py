#실시간 모델
import json
import requests
from bs4 import BeautifulSoup
import datetime
import os
import time
from chatbot_model import CampusChatBot


class RealtimeCampusChatBot(CampusChatBot):
    def __init__(self, model_path="./model"):
        """실시간 정보 반영 캠퍼스 챗봇 초기화"""
        super().__init__(model_path)
        self.setup_realtime_sources()

    def setup_realtime_sources(self):
        """실시간 정보 소스 설정"""
        self.urls = {
            "notice": "https://www.cnu.ac.kr/UI/usr/cmn/bbs/BB0000006/list.do",  # 공지사항
            "academic": "https://www.cnu.ac.kr/UI/usr/cmn/bbs/BB0000007/list.do",  # 학사공지
            "shuttle": "https://www.cnu.ac.kr/UI/usr/lnb/910/subview.do",  # 셔틀버스
            "meal": "http://coop.cnu.ac.kr/dining/menu"  # 식단 (가상 URL)
        }

        # 캐시 시간 설정 (분)
        self.cache_duration = {
            "notice": 60,  # 1시간
            "academic": 60,  # 1시간
            "shuttle": 30,  # 30분
            "meal": 1440  # 24시간
        }

        # 캐시 저장소
        self.cache = {}

    def get_cached_or_fetch(self, data_type, fetch_function):
        """캐시된 데이터를 반환하거나 새로 가져오기"""
        current_time = datetime.datetime.now()

        # 캐시에 데이터가 있고 유효한지 확인
        if data_type in self.cache:
            cached_time = self.cache[data_type]['timestamp']
            cache_duration = datetime.timedelta(minutes=self.cache_duration[data_type])

            if current_time - cached_time < cache_duration:
                return self.cache[data_type]['data']

        # 캐시가 없거나 만료된 경우 새로 가져오기
        try:
            new_data = fetch_function()
            self.cache[data_type] = {
                'data': new_data,
                'timestamp': current_time
            }
            return new_data
        except Exception as e:
            print(f"데이터 가져오기 실패 ({data_type}): {e}")
            # 캐시된 데이터라도 반환
            if data_type in self.cache:
                return self.cache[data_type]['data']
            return None

    def fetch_notice_info(self):
        """공지사항 정보 가져오기"""
        try:
            # 실제 구현에서는 충남대 공지사항 페이지를 크롤링
            # 여기서는 샘플 데이터 반환
            notices = [
                {
                    "title": "2024학년도 2학기 기말고사 시행 안내",
                    "date": "2024-06-10",
                    "department": "학사지원과"
                },
                {
                    "title": "여름계절학기 수강신청 안내",
                    "date": "2024-06-09",
                    "department": "학사지원과"
                },
                {
                    "title": "2024년 하반기 장학금 신청 공고",
                    "date": "2024-06-08",
                    "department": "학생지원과"
                }
            ]
            return notices
        except Exception as e:
            print(f"공지사항 정보 가져오기 실패: {e}")
            return []

    def fetch_shuttle_info(self):
        """셔틀버스 정보 가져오기"""
        try:
            # 실제로는 실시간 셔틀버스 정보 API 호출
            # 여기서는 현재 시간 기반 샘플 데이터
            current_time = datetime.datetime.now()
            current_hour = current_time.hour

            if 7 <= current_hour <= 9:
                status = "등교 시간 운행 중"
                next_bus = "15분 후"
            elif 17 <= current_hour <= 18:
                status = "하교 시간 운행 중"
                next_bus = "20분 후"
            else:
                status = "운행 종료"
                next_bus = "내일 07:30"

            shuttle_info = {
                "status": status,
                "next_bus": next_bus,
                "routes": {
                    "A노선": "대전역 - 서대전역 - 충남대",
                    "B노선": "유성온천역 - 과기원 - 충남대",
                    "C노선": "정부청사역 - 시청역 - 충남대"
                },
                "last_update": current_time.strftime("%Y-%m-%d %H:%M")
            }
            return shuttle_info
        except Exception as e:
            print(f"셔틀버스 정보 가져오기 실패: {e}")
            return {}

    def fetch_meal_info(self):
        """식단 정보 가져오기"""
        try:
            # 실제로는 생협 홈페이지에서 식단 크롤링
            # 여기서는 샘플 데이터
            today = datetime.datetime.now()
            weekday = today.weekday()  # 0=월요일, 6=일요일

            meals = {
                "date": today.strftime("%Y-%m-%d"),
                "day": ["월", "화", "수", "목", "금", "토", "일"][weekday],
                "lunch": {
                    "main": "김치찌개",
                    "side": ["계란후라이", "김치", "콩나물무침", "밥"],
                    "price": "4,000원"
                },
                "dinner": {
                    "main": "제육볶음",
                    "side": ["된장찌개", "김치", "시금치나물", "밥"],
                    "price": "4,500원"
                }
            }

            # 주말에는 운영 안함
            if weekday >= 5:  # 토요일, 일요일
                meals["status"] = "주말 휴무"
            else:
                meals["status"] = "운영 중"

            return meals
        except Exception as e:
            print(f"식단 정보 가져오기 실패: {e}")
            return {}

    def fetch_academic_schedule(self):
        """학사일정 정보 가져오기"""
        try:
            # 실제로는 학사일정 페이지 크롤링
            current_date = datetime.datetime.now()

            # 샘플 학사일정
            schedule = [
                {
                    "event": "2024학년도 2학기 기말고사",
                    "start_date": "2024-06-17",
                    "end_date": "2024-06-21",
                    "status": "예정"
                },
                {
                    "event": "여름계절학기 수강신청",
                    "start_date": "2024-06-10",
                    "end_date": "2024-06-14",
                    "status": "진행 중"
                },
                {
                    "event": "2학기 종강",
                    "start_date": "2024-06-22",
                    "end_date": "2024-06-22",
                    "status": "예정"
                }
            ]

            return schedule
        except Exception as e:
            print(f"학사일정 정보 가져오기 실패: {e}")
            return []

    def generate_realtime_response(self, question, category):
        """실시간 정보를 반영한 응답 생성"""
        current_time = datetime.datetime.now()

        if category == 1:  # 공지사항
            notices = self.get_cached_or_fetch("notice", self.fetch_notice_info)
            if notices:
                recent_notices = notices[:3]  # 최신 3개
                response = "최신 공지사항입니다:\n\n"
                for notice in recent_notices:
                    response += f"• {notice['title']} ({notice['date']}, {notice['department']})\n"
                response += "\n자세한 내용은 충남대학교 홈페이지에서 확인하세요."
                return response

        elif category == 2:  # 학사일정
            schedule = self.get_cached_or_fetch("academic", self.fetch_academic_schedule)
            if schedule:
                response = "현재 학사일정입니다:\n\n"
                for event in schedule:
                    response += f"• {event['event']}: {event['start_date']} ~ {event['end_date']} ({event['status']})\n"
                return response

        elif category == 3:  # 식단
            meal_info = self.get_cached_or_fetch("meal", self.fetch_meal_info)
            if meal_info and meal_info.get("status") == "운영 중":
                response = f"오늘({meal_info['date']}, {meal_info['day']}요일) 식단입니다:\n\n"
                response += f"🍽️ 중식: {meal_info['lunch']['main']}\n"
                response += f"   반찬: {', '.join(meal_info['lunch']['side'])}\n"
                response += f"   가격: {meal_info['lunch']['price']}\n\n"
                response += f"🍽️ 석식: {meal_info['dinner']['main']}\n"
                response += f"   반찬: {', '.join(meal_info['dinner']['side'])}\n"
                response += f"   가격: {meal_info['dinner']['price']}"
                return response
            elif meal_info and meal_info.get("status") == "주말 휴무":
                return "주말에는 학생식당이 운영하지 않습니다. 평일 운영시간을 확인해주세요."

        elif category == 4:  # 셔틀버스
            shuttle_info = self.get_cached_or_fetch("shuttle", self.fetch_shuttle_info)
            if shuttle_info:
                response = f"🚌 셔틀버스 실시간 정보 (업데이트: {shuttle_info['last_update']}):\n\n"
                response += f"현재 상태: {shuttle_info['status']}\n"
                response += f"다음 버스: {shuttle_info['next_bus']}\n\n"
                response += "운행 노선:\n"
                for route, path in shuttle_info['routes'].items():
                    response += f"• {route}: {path}\n"
                return response

        # 실시간 정보가 없으면 기본 응답 사용
        return super().generate_response(question, category)

    def chat(self, question):
        """실시간 정보를 반영한 응답 생성"""
        category = self.predict_category(question)
        response = self.generate_realtime_response(question, category)

        return {
            "question": question,
            "category": category,
            "category_name": self.category_names[category],
            "response": response,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def process_realtime_test_file(self, test_file_path, output_file_path):
        """실시간 테스트 파일 처리"""
        try:
            # 테스트 데이터 로드
            with open(test_file_path, 'r', encoding='utf-8') as f:
                test_data = json.load(f)

            results = []

            print(f"실시간 테스트 데이터 처리 중... (총 {len(test_data)}개)")

            for i, item in enumerate(test_data):
                user_question = item['user']

                # 실시간 응답 생성
                chat_result = self.chat(user_question)

                results.append({
                    "user": user_question,
                    "model": chat_result["response"]
                })

                if (i + 1) % 5 == 0:
                    print(f"진행률: {i + 1}/{len(test_data)}")

            # 출력 디렉토리 생성
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

            # 결과 저장
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            print(f"실시간 결과 저장 완료: {output_file_path}")
            return True

        except Exception as e:
            print(f"실시간 테스트 파일 처리 중 오류: {e}")
            return False


def main():
    """메인 함수 - 실시간 테스트 파일 처리"""
    # 실시간 챗봇 초기화
    chatbot = RealtimeCampusChatBot()

    # 테스트 파일 경로
    test_file_path = "./data/test_realtime.json"
    output_file_path = "./outputs/realtime_output.json"

    # 테스트 파일이 존재하는지 확인
    if os.path.exists(test_file_path):
        print("실시간 테스트 파일을 찾았습니다. 처리를 시작합니다...")
        success = chatbot.process_realtime_test_file(test_file_path, output_file_path)

        if success:
            print("실시간 테스트 완료!")
        else:
            print("실시간 테스트 실패!")
    else:
        print("실시간 테스트 파일이 없습니다. 샘플 테스트를 진행합니다...")

        # 실시간 정보가 포함된 샘플 질문들
        sample_questions = [
            "새로 업데이트된 서버버스 정류장이 있을까요?",
            "5월 이후로 변동된 학사일정이 있을까요?",
            "다음주 학식 뭐 나와요?",
            "가장 최근에 올라온 공지사항은 언제 게시되었나요?",
            "오늘 셔틀버스 운행 여부를 알려주세요",
            "이번 주 식단표를 보여주세요",
            "최신 장학금 공지를 확인하고 싶어요",
            "현재 진행 중인 학사 일정이 있나요?",
            "실시간 셔틀버스 위치를 알 수 있을까요?",
            "오늘 저녁 메뉴가 뭔가요?"
        ]

        results = []
        print("\n=== 실시간 샘플 테스트 결과 ===")

        for question in sample_questions:
            chat_result = chatbot.chat(question)

            results.append({
                "user": question,
                "model": chat_result["response"]
            })

            print(f"\n질문: {question}")
            print(f"카테고리: {chat_result['category_name']}")
            print(f"시간: {chat_result['timestamp']}")
            print(f"답변: {chat_result['response']}")
            print("-" * 80)

        # 샘플 결과 저장
        os.makedirs("./outputs", exist_ok=True)
        with open("./outputs/realtime_output.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n실시간 샘플 결과가 ./outputs/realtime_output.json에 저장되었습니다.")


if __name__ == "__main__":
    main()