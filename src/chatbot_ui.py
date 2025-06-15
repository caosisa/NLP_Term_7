import gradio as gr
from chatbot_model import CompleteCampusChatBot  # 기존 모델 import
import os

# 전역 변수로 챗봇 인스턴스 저장
chatbot_model = None


def initialize_chatbot():
    """챗봇 초기화 (한 번만 실행)"""
    global chatbot_model
    if chatbot_model is None:
        print("🤖 챗봇 모델 초기화 중...")
        try:
            chatbot_model = CompleteCampusChatBot(
                model_name="Qwen/Qwen3-14B-AWQ"  # 또는 다른 모델명
            )
            print("✅ 챗봇 모델 초기화 완료!")
        except Exception as e:
            print(f"❌ 챗봇 초기화 실패: {e}")
            # fallback 모델 시도
            try:
                chatbot_model = CompleteCampusChatBot(
                    model_name="Qwen/Qwen2.5-7B-Instruct"
                )
                print("✅ Fallback 모델로 초기화 완료!")
            except Exception as fallback_error:
                print(f"❌ Fallback 모델도 실패: {fallback_error}")
                chatbot_model = None
    return chatbot_model


def chat_interface(user_input, history):
    """Gradio와 챗봇 연결 함수"""
    if user_input is None or user_input == "":
        return "", history

    # 챗봇 초기화 확인
    bot = initialize_chatbot()
    if bot is None:
        error_msg = "죄송합니다. 챗봇 모델을 로드할 수 없습니다. 관리자에게 문의하세요."
        history = history + [(user_input, error_msg)]
        return "", history

    try:
        print(f"🔍 사용자 질문: {user_input}")

        # 기존 챗봇의 generate_comprehensive_answer 메서드 사용
        response = bot.generate_comprehensive_answer(user_input)

        # 응답이 None이거나 빈 문자열인 경우 처리
        if not response or response.strip() == "":
            response = "죄송합니다. 적절한 답변을 생성할 수 없습니다. 다시 질문해 주세요."

        print(f"✅ 챗봇 응답 생성 완료")

    except Exception as e:
        print(f"❌ 답변 생성 중 오류: {e}")
        response = f"죄송합니다. 오류가 발생했습니다: {str(e)}"

    # 대화 히스토리에 추가
    history = history + [(user_input, response)]
    return "", history


# CSS 스타일 (기존 것 그대로 사용)
custom_css = """
    @import url('https://fonts.googleapis.com/css2?family=Pretendard&display=swap');
    .gradio-container {
        width: 800px;
        margin: 0 auto;
        padding: 10px;
        background-color: #ffffff;
        font-family: 'Pretendard', sans-serif;
        border: 1px solid #ddd;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    }
    .gr-chatbot .message.user {
        background-color: #f4f4f4;
        padding: 10px 20px;
        margin-bottom: 8px;
        font-size: 14px;
    }
    .gr-chatbot .message.assistant {
        background-color: #ffffff;
        padding: 10px 20px;
        font-size: 14px;
    }
    .gr-chatbot {
        background-color: #ffffff;
        border: none;
        padding: 10px;
    }
    .gr-textbox textarea {
        background-color: #fafafa;
        border-radius: 20px;
        padding: 12px 16px;
        font-size: 14px;
        border: 1px solid #d0d0d0;
        resize: none;
    }
    .gr-button {
        background: #007bff !important;
        border: none !important;
        border-radius: 20px !important;
        color: white !important;
        font-weight: bold !important;
        padding: 10px 20px !important;
    }
    .gr-button:hover {
        background: #0056b3 !important;
        transform: translateY(-1px);
    }
    .gr-markdown, .gr-markdown * {
        color: #000000 !important;
    }
    .loading-message {
        color: #666;
        font-style: italic;
    }
"""

# Gradio 인터페이스 생성
with gr.Blocks(css=custom_css, title="충남대 Campus Chatbot") as demo:
    gr.Markdown("""
    <div style="color: black; font-family: 'Pretendard', sans-serif;">

    # 🎓 충남대학교 Campus Chatbot
    **실시간 정보 크롤링 + AWQ 양자화 모델**

    📚 졸업요건, 학사일정, 셔틀버스, 식단, 공지사항 등을 문의하세요!

    </div>
    """)

    chatbot = gr.Chatbot(
        label="",
        height=400,
        bubble_full_width=False,
        show_copy_button=True,
        placeholder="질문을 입력해 주세요."
    )

    with gr.Row():
        txt = gr.Textbox(
            show_label=False,
            placeholder="질문을 입력해주세요. (예: 셔틀버스 시간표, 오늘 학식 메뉴, 졸업요건 등)",
            scale=10,
            container=False
        )
        send_btn = gr.Button("입력하기", scale=1, variant="primary")

    # 샘플 질문 버튼들
    with gr.Row():
        sample_questions = [
            "셔틀버스 시간표 알려줘",
            "오늘 학식 메뉴가 뭐야?",
            "졸업까지 몇 학점 필요해?",
            "최신 공지사항 알려줘"
        ]

        sample_buttons = []
        for question in sample_questions:
            btn = gr.Button(question, size="sm")
            sample_buttons.append(btn)

    # 이벤트 핸들러 연결
    txt.submit(chat_interface, [txt, chatbot], [txt, chatbot])
    send_btn.click(chat_interface, [txt, chatbot], [txt, chatbot])

    # 샘플 질문 버튼 이벤트
    for i, btn in enumerate(sample_buttons):
        btn.click(
            lambda q=sample_questions[i]: (q, []),
            outputs=[txt, chatbot]
        ).then(
            chat_interface,
            [txt, chatbot],
            [txt, chatbot]
        )

    # 앱 로드 시 챗봇 초기화 메시지
    demo.load(
        lambda: "🤖 충남대 캠퍼스 챗봇이 준비되었습니다! 궁금한 것을 물어보세요.",
        outputs=gr.Textbox(visible=False)
    )


# 앱 실행 함수
def launch_app():
    """앱 실행"""
    print("🚀 Gradio 앱 시작 중...")
    print("📡 첫 질문 시 모델 로딩으로 인해 시간이 걸릴 수 있습니다.")

    # 백그라운드에서 모델 미리 로드 (선택사항)
    try:
        print("🔄 백그라운드에서 모델 미리 로드 중...")
        initialize_chatbot()
    except Exception as e:
        print(f"⚠️ 백그라운드 로드 실패 (첫 질문 시 로드됩니다): {e}")

    demo.launch(
        share=True,  # 공유 링크 생성
        server_name="127.0.0.1",  # 외부 접속 허용
        server_port=7860,  # 포트 설정
        show_error=True
    )


if __name__ == "__main__":
    launch_app()