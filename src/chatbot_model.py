import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os


class CampusChatBot:
    def __init__(self, model_path="./model"):
        """캠퍼스 챗봇 초기화"""
        self.model_path = model_path
        self.load_model()
        self.setup_responses()

    def load_model(self):
        """모델과 토크나이저 로드"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)
            self.model.eval()
            print(f"모델 로드 완료: {self.model_path}")
        except Exception as e:
            print(f"모델 로드 실패: {e}")
            self.tokenizer = None
            self.model = None

    def setup_responses(self):
        """응답 템플릿 설정"""
        self.category_names = {
            0: "졸업요건",
            1: "학교공지사항",
            2: "학사일정",
            3: "식단안내",
            4: "통학셔틀버스"
        }

        self.responses = {
            0: {  # 졸업요건
                "keywords": {
                    "학점": [
                        "일반적으로 총 130학점 이상을 이수해야 졸업할 수 있습니다.",
                        "전공필수, 전공선택, 교양필수, 교양선택, 일반선택 학점을 모두 충족해야 합니다.",
                        "정확한 졸업학점은 입학년도와 학과에 따라 다르므로 학과 사무실에 문의하세요."
                    ],
                    "전공": [
                        "전공 졸업요건은 학과마다 다릅니다.",
                        "전공필수와 전공선택 과목을 확인하시고, 소속 학과 사무실에 문의해보세요.",
                        "전공심화과정 또는 다전공 이수 시 요건이 달라질 수 있습니다."
                    ],
                    "교양": [
                        "교양 과목은 기초교양과 균형교양으로 구분됩니다.",
                        "영어, 컴퓨터, 체육 등 기초교양과 인문, 사회, 자연과학 균형교양을 이수해야 합니다.",
                        "교양 최소 이수학점은 학과별로 다를 수 있습니다."
                    ]
                },
                "default": "졸업 요건에 대한 자세한 정보는 소속 학과 사무실이나 학사지원과(042-821-5025)에 문의하시기 바랍니다."
            },
            1: {  # 학교공지사항
                "keywords": {
                    "공지": [
                        "최신 공지사항은 충남대학교 홈페이지(www.cnu.ac.kr) 공지사항에서 확인하실 수 있습니다.",
                        "각 학과별 공지사항은 해당 학과 홈페이지를 확인해주세요.",
                        "중요한 공지는 CNU 포털시스템에서도 알림을 받을 수 있습니다."
                    ],
                    "장학": [
                        "장학금 관련 공지는 학생지원과 홈페이지를 확인하세요.",
                        "교내장학금, 교외장학금, 국가장학금 정보를 제공합니다.",
                        "장학금 신청 기간과 자격요건을 꼼꼼히 확인하시기 바랍니다."
                    ],
                    "행사": [
                        "각종 행사 및 이벤트 정보는 학교 홈페이지 공지사항을 참고하세요.",
                        "축제, 특강, 취업박람회 등 다양한 행사가 개최됩니다.",
                        "학과별 특별 행사는 해당 학과 공지를 확인해주세요."
                    ]
                },
                "default": "충남대학교 공식 홈페이지(www.cnu.ac.kr)와 각 학과 홈페이지에서 최신 공지사항을 확인하실 수 있습니다."
            },
            2: {  # 학사일정
                "keywords": {
                    "수강신청": [
                        "수강신청 일정은 매 학기 시작 전 학사지원과에서 공지합니다.",
                        "수강신청은 CNU 포털시스템(portal.cnu.ac.kr)에서 진행됩니다.",
                        "수강신청 및 정정 기간을 놓치지 않도록 주의하세요."
                    ],
                    "시험": [
                        "중간고사: 매년 4월, 10월 중순경",
                        "기말고사: 매년 6월, 12월 중순경",
                        "정확한 시험일정은 학사일정표와 각 과목 강의계획서를 확인하세요."
                    ],
                    "개강": [
                        "1학기 개강: 매년 3월 첫째 주",
                        "2학기 개강: 매년 9월 첫째 주",
                        "정확한 개강일은 학사일정표를 참고하시기 바랍니다."
                    ],
                    "방학": [
                        "여름방학: 6월 말 ~ 8월 말",
                        "겨울방학: 12월 말 ~ 2월 말",
                        "방학 중에도 계절학기가 운영됩니다."
                    ]
                },
                "default": "학사일정은 충남대학교 학사지원과 홈페이지에서 확인할 수 있습니다. 학사지원과(042-821-5025)로 문의하시기 바랍니다."
            },
            3: {  # 식단안내
                "keywords": {
                    "식단": [
                        "교내 식당 식단은 충남대학교 생활협동조합 홈페이지에서 확인하실 수 있습니다.",
                        "학생식당, 교직원식당, 카페테리아 등 다양한 식당이 운영됩니다.",
                        "주간 식단표는 매주 월요일에 업데이트됩니다."
                    ],
                    "메뉴": [
                        "오늘의 메뉴는 각 식당 입구에 게시된 메뉴판을 확인하세요.",
                        "한식, 양식, 중식, 일식 등 다양한 메뉴를 제공합니다.",
                        "생협 앱을 통해서도 실시간 메뉴를 확인할 수 있습니다."
                    ],
                    "가격": [
                        "학생식당 한식: 4,000원 ~ 4,500원",
                        "학생식당 양식: 5,000원 ~ 5,500원",
                        "교직원식당: 6,000원 ~ 7,000원",
                        "카페테리아: 메뉴에 따라 상이"
                    ],
                    "시간": [
                        "조식: 08:00 ~ 09:30 (일부 식당)",
                        "중식: 11:30 ~ 14:00",
                        "석식: 17:30 ~ 19:00",
                        "식당별로 운영시간이 다를 수 있습니다."
                    ]
                },
                "default": "교내 식당 정보는 충남대학교 생활협동조합 홈페이지(http://coop.cnu.ac.kr)에서 확인하실 수 있습니다."
            },
            4: {  # 통학셔틀버스
                "keywords": {
                    "시간표": [
                        "등교 시간: 07:30 ~ 09:00 (15~20분 간격)",
                        "하교 시간: 17:00 ~ 18:30 (15~20분 간격)",
                        "토요일은 제한적으로 운행하며, 일요일과 공휴일은 운행하지 않습니다."
                    ],
                    "노선": [
                        "A노선: 대전역 - 서대전역 - 충남대",
                        "B노선: 유성온천역 - 과기원 - 충남대",
                        "C노선: 정부청사역 - 시청역 - 충남대",
                        "자세한 노선도는 학교 홈페이지를 참고하세요."
                    ],
                    "정류장": [
                        "대전역 서광장, 서대전역 2번 출구",
                        "유성온천역 1번 출구, 정부청사역 3번 출구",
                        "교내 정류장: 정문, 후문, 학생회관 앞"
                    ],
                    "요금": [
                        "셔틀버스는 무료로 이용할 수 있습니다.",
                        "학생증 또는 교직원증을 소지해야 이용 가능합니다.",
                        "만석 시에는 탑승이 제한될 수 있습니다."
                    ]
                },
                "default": "셔틀버스 시간표와 노선은 충남대학교 홈페이지 교통안내를 참고하세요. 총무과(042-821-5114)로 문의 가능합니다."
            }
        }

    def predict_category(self, question):
        """질문의 카테고리를 예측"""
        if self.model is None or self.tokenizer is None:
            return 0

        encoding = self.tokenizer(
            question,
            truncation=True,
            padding='max_length',
            max_length=128,
            return_tensors='pt'
        )

        # GPU로 이동
        encoding = {k: v.to(self.device) for k, v in encoding.items()}

        with torch.no_grad():
            outputs = self.model(**encoding)
            logits = outputs.logits
            predicted_label = torch.argmax(logits, dim=-1).item()

        return predicted_label

    def generate_response(self, question, category):
        """카테고리에 따른 응답 생성"""
        category_data = self.responses.get(category, self.responses[0])

        # 키워드 기반 매칭
        for keyword, responses in category_data["keywords"].items():
            if keyword in question:
                # 여러 응답 중 적절한 것 선택 (여기서는 첫 번째 응답)
                return responses[0]

        # 기본 응답 반환
        return category_data["default"]

    def chat(self, question):
        """질문에 대한 완전한 응답 생성"""
        category = self.predict_category(question)
        response = self.generate_response(question, category)

        return {
            "question": question,
            "category": category,
            "category_name": self.category_names[category],
            "response": response
        }

    def process_test_file(self, test_file_path, output_file_path):
        """테스트 파일을 처리하여 결과 저장"""
        try:
            # 테스트 데이터 로드
            with open(test_file_path, 'r', encoding='utf-8') as f:
                test_data = json.load(f)

            results = []

            print(f"테스트 데이터 처리 중... (총 {len(test_data)}개)")

            for i, item in enumerate(test_data):
                user_question = item['user']

                # 응답 생성
                chat_result = self.chat(user_question)

                results.append({
                    "user": user_question,
                    "model": chat_result["response"]
                })

                if (i + 1) % 10 == 0:
                    print(f"진행률: {i + 1}/{len(test_data)}")

            # 출력 디렉토리 생성
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

            # 결과 저장
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            print(f"결과 저장 완료: {output_file_path}")
            return True

        except Exception as e:
            print(f"테스트 파일 처리 중 오류: {e}")
            return False


def main():
    """메인 함수 - 테스트 파일 처리"""
    # 챗봇 초기화
    chatbot = CampusChatBot()

    # 테스트 파일 경로
    test_file_path = "./data/test_chat.json"
    output_file_path = "./outputs/chat_output.json"

    # 테스트 파일이 존재하는지 확인
    if os.path.exists(test_file_path):
        print("테스트 파일을 찾았습니다. 처리를 시작합니다...")
        success = chatbot.process_test_file(test_file_path, output_file_path)

        if success:
            print("테스트 완료!")
        else:
            print("테스트 실패!")
    else:
        print("테스트 파일이 없습니다. 샘플 테스트를 진행합니다...")

        # 샘플 질문들
        sample_questions = [
            "졸업까지 몇 학점을 들어야 하나요?",
            "이번 학기 수강신청은 언제 시작하나요?",
            "오늘 학식 뭐 나와요?",
            "다음주에 셔틀버스는 정상 운행하나요?",
            "이번에 올라온 공지사항 어디서 볼 수 있어요?",
            "전공 졸업요건이 궁금해요",
            "중간고사 일정이 언제인가요?",
            "학생식당 가격이 얼마예요?",
            "셔틀버스 노선을 알려주세요",
            "장학금 공지는 어디서 보나요?"
        ]

        results = []
        print("\n=== 샘플 테스트 결과 ===")

        for question in sample_questions:
            chat_result = chatbot.chat(question)

            results.append({
                "user": question,
                "model": chat_result["response"]
            })

            print(f"\n질문: {question}")
            print(f"카테고리: {chat_result['category_name']}")
            print(f"답변: {chat_result['response']}")

        # 샘플 결과 저장
        os.makedirs("./outputs", exist_ok=True)
        with open("./outputs/chat_output.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n샘플 결과가 ./outputs/chat_output.json에 저장되었습니다.")


if __name__ == "__main__":
    main()