#!/bin/bash

# 충남대 Campus ChatBot 실행 스크립트
echo "========================================"
echo "   충남대 Campus ChatBot 실행 중..."
echo "========================================"

# 현재 디렉토리 확인
echo "현재 작업 디렉토리: $(pwd)"

# Python 버전 확인
echo "Python 버전:"
python --version

# 필요한 디렉토리 생성
echo "출력 디렉토리 생성 중..."
mkdir -p outputs
mkdir -p model

# Step 1: 챗봇 모델 실행 (JSON 출력 생성)
echo ""
echo "Step 1: 챗봇 모델 실행 중..."
echo "----------------------------------------"

if [ -f "src/chatbot_model.py" ]; then
    echo "기본 챗봇 모델 실행 중..."
    cd src
    python chatbot_model.py
    cd ..

    if [ -f "outputs/chat_output.json" ]; then
        echo "✅ 기본 챗봇 결과 생성 완료: outputs/chat_output.json"
    else
        echo "❌ 기본 챗봇 결과 생성 실패"
    fi
else
    echo "❌ chatbot_model.py 파일을 찾을 수 없습니다."
fi

# Step 2: 실시간 모델 실행 (Optional)
echo ""
echo "Step 2: 실시간 모델 실행 중... (Optional)"
echo "----------------------------------------"

if [ -f "src/realtime_model.py" ]; then
    echo "실시간 챗봇 모델 실행 중..."
    cd src
    python realtime_model.py
    cd ..

    if [ -f "outputs/realtime_output.json" ]; then
        echo "✅ 실시간 챗봇 결과 생성 완료: outputs/realtime_output.json"
    else
        echo "❌ 실시간 챗봇 결과 생성 실패"
    fi
else
    echo "⚠️ realtime_model.py 파일을 찾을 수 없습니다. (선택사항)"
fi

# Step 3: 결과 확인
echo ""
echo "Step 3: 생성된 파일 확인"
echo "----------------------------------------"

echo "생성된 출력 파일들:"
if [ -d "outputs" ]; then
    ls -la outputs/
else
    echo "outputs 디렉토리가 없습니다."
fi

# Step 4: 웹 UI 실행
echo ""
echo "Step 4: 웹 UI 실행"
echo "----------------------------------------"

if [ -f "src/chatbot_ui.py" ]; then
    echo "Streamlit 웹 UI를 실행합니다..."
    echo "브라우저에서 http://localhost:8501 을 열어주세요."
    echo ""
    echo "UI 종료하려면 Ctrl+C를 누르세요."
    echo ""

    # UI 실행
    cd src
    streamlit run chatbot_ui.py --server.port 8501 --server.address 0.0.0.0
    cd ..
else
    echo "❌ chatbot_ui.py 파일을 찾을 수 없습니다."
fi

echo ""
echo "========================================"
echo "   챗봇 실행 완료"
echo "========================================"