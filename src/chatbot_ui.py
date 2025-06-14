#챗봇 ui
import streamlit as st
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os
import datetime

# 페이지 설정
st.set_page_config(
    page_title="충남대 Campus ChatBot",
    page_icon="🤖",
    layout="wide"
)

# CSS 스타일
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
    font-weight: bold;
}

.chat-container {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 10px;
    margin: 1rem 0;
}

.user-message {
    background-color: #007bff;
    color: white;
    padding: 0.8rem;
    border-radius: 10px;
    margin: 0.5rem 0;
    text-align: right;
}

.bot-message {
    background-color: #e9ecef;
    color: #333;
    padding: 0.8rem;
    border-radius: 10px;
    margin: 0.5rem 0;
    text-align: left;
}

.category-badge {
    background-color: #28a745;
    color: white;
    padding: 0.2rem 0.5rem;
    border-radius: 5px;
    font-size: 0.8rem;
    margin-left: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_model_and_tokenizer():
    """모델과 토크나이저를 로드합니다."""
    try:
        model_path = "./model"
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        return model, tokenizer
    except:
        st.error("모델을 로드할 수 없습니다. 먼저 분류기를 훈련해주세요.")
        return None, None


def predict_category(question, model, tokenizer):
    """질문의 카테고리를 예측합니다."""
    if model is None or tokenizer is None:
        return 0

    encoding = tokenizer(
        question,
        truncation=True,
        padding='max_length',
        max_length=128,
        return_tensors='pt'
    )

    with torch.no_grad():
        outputs = model(**encoding)
        logits = outputs.logits
        predicted_label = torch.argmax(logits, dim=-1).item()

    return predicted_label


def get_response(question, category):
    """카테고리에 따른 응답을 생성합니다."""

    responses = {
        0: {  # 졸업요건
            "keywords": ["졸업", "학점", "전공", "교양", "요건"],
            "default": "졸업 요건에 대한 자세한 정보는 소속 학과 사무실이나 학사지원과에 문의하시기 바랍니다.",
            "specific": {
                "학점": "일반적으로 총 130학점 이상을 이수해야 졸업할 수 있습니다. 전공학점, 교양학점, 일반선택학점을 모두 충족해야 합니다.",
                "전공": "전공 졸업요건은 학과마다 다릅니다. 전공필수, 전공선택 학점을 확인하시고 소속 학과에 문의해보세요.",
                "교양": "교양 과목은 기초교양과 균형교양으로 나뉩니다. 각 영역별 최소 이수학점을 확인하세요."
            }
        },
        1: {  # 학교 공지사항
            "keywords": ["공지", "공지사항", "알림", "소식"],
            "default": "최신 공지사항은 충남대학교 홈페이지(www.cnu.ac.kr)에서 확인하실 수 있습니다.",
            "specific": {
                "장학금": "장학금 관련 공지는 학생지원과 홈페이지를 확인하세요.",
                "행사": "각종 행사 및 이벤트 정보는 학교 홈페이지 공지사항을 참고하세요.",
                "시험": "시험 관련 공지는 해당 과목 담당교수 또는 학과 공지를 확인하세요."
            }
        },
        2: {  # 학사일정
            "keywords": ["일정", "수강신청", "시험", "휴강", "개강", "종강"],
            "default": "학사일정은 충남대학교 학사지원과 홈페이지에서 확인할 수 있습니다.",
            "specific": {
                "수강신청": "수강신청 일정은 매 학기 시작 전 학사지원과에서 공지합니다. 포탈에서 확인하세요.",
                "시험": "중간고사 및 기말고사 일정은 각 학과별로 다를 수 있습니다.",
                "개강": "개강일은 학사일정표를 참고하시기 바랍니다."
            }
        },
        3: {  # 식단 안내
            "keywords": ["식단", "메뉴", "학식", "식당", "밥"],
            "default": "교내 식당 식단은 충남대학교 생활협동조합 홈페이지에서 확인하실 수 있습니다.",
            "specific": {
                "오늘": "오늘의 식단은 생협 홈페이지나 각 식당에 게시된 메뉴판을 확인하세요.",
                "이번주": "주간 식단표는 매주 업데이트되며 생협 홈페이지에서 볼 수 있습니다.",
                "가격": "학생식당 가격은 한식 4,000원, 양식 5,000원 내외입니다."
            }
        },
        4: {  # 통학/셔틀버스
            "keywords": ["버스", "셔틀", "통학", "교통", "시간표"],
            "default": "셔틀버스 시간표와 노선은 충남대학교 홈페이지 교통안내를 참고하세요.",
            "specific": {
                "시간표": "셔틀버스는 등교시간(07:30~09:00)과 하교시간(17:00~18:30)에 운행합니다.",
                "노선": "대전역, 서대전역, 유성온천역 등 주요 지점에서 운행합니다.",
                "요금": "셔틀버스는 무료로 이용할 수 있습니다."
            }
        }
    }

    category_info = responses.get(category, responses[0])

    # 키워드 매칭으로 구체적인 답변 찾기
    for keyword, specific_response in category_info["specific"].items():
        if keyword in question:
            return specific_response

    # 기본 답변 반환
    return category_info["default"]


def main():
    # 헤더
    st.markdown('<h1 class="main-header">🤖 충남대 Campus ChatBot</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # 모델 로드
    model, tokenizer = load_model_and_tokenizer()

    # 사이드바 - 정보
    with st.sidebar:
        st.header("📋 도움말")
        st.write("**지원하는 질문 유형:**")
        st.write("• 졸업요건")
        st.write("• 학교 공지사항")
        st.write("• 학사일정")
        st.write("• 식단 안내")
        st.write("• 통학/셔틀버스")

        st.markdown("---")
        st.write("**예시 질문:**")
        st.write("• 졸업까지 몇 학점을 들어야 하나요?")
        st.write("• 이번 학기 수강신청은 언제인가요?")
        st.write("• 오늘 학식 메뉴가 뭔가요?")
        st.write("• 셔틀버스 시간표를 알려주세요")
        st.write("• 최근 공지사항을 확인하고 싶어요")

    # 세션 상태 초기화
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # 채팅 인터페이스
    st.subheader("💬 채팅")

    # 채팅 히스토리 표시
    chat_container = st.container()
    with chat_container:
        for chat in st.session_state.chat_history:
            if chat['type'] == 'user':
                st.markdown(f'<div class="user-message">👤 {chat["message"]}</div>',
                            unsafe_allow_html=True)
            else:
                category_name = ["졸업요건", "학교공지", "학사일정", "식단안내", "통학버스"][chat['category']]
                st.markdown(
                    f'<div class="bot-message">🤖 {chat["message"]}<span class="category-badge">{category_name}</span></div>',
                    unsafe_allow_html=True)

    # 질문 입력
    with st.form(key='chat_form', clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            user_input = st.text_input("질문을 입력하세요:", placeholder="예: 졸업까지 몇 학점을 들어야 하나요?")
        with col2:
            submit_button = st.form_submit_button("전송", use_container_width=True)

    # 질문 처리
    if submit_button and user_input:
        # 사용자 메시지 추가
        st.session_state.chat_history.append({
            'type': 'user',
            'message': user_input
        })

        # 카테고리 예측
        predicted_category = predict_category(user_input, model, tokenizer)

        # 응답 생성
        response = get_response(user_input, predicted_category)

        # 봇 응답 추가
        st.session_state.chat_history.append({
            'type': 'bot',
            'message': response,
            'category': predicted_category
        })

        st.rerun()

    # 채팅 기록 초기화 버튼
    if st.button("대화 기록 초기화"):
        st.session_state.chat_history = []
        st.rerun()

    # 하단 정보
    st.markdown("---")
    st.markdown("**📍 충남대학교 | 컴퓨터공학과 | 자연어처리 Term Project**")
    st.markdown(f"*마지막 업데이트: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}*")


if __name__ == "__main__":
    main()