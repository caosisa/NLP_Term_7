#!/bin/bash

# 충남대 Campus ChatBot 실행 스크립트 (수정된 버전)
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

# Step 1: 의존성 설치 확인
echo ""
echo "Step 1: 의존성 확인 중..."
echo "----------------------------------------"

# 필수 패키지 확인
python -c "
import sys
required_packages = ['json', 'os', 'sklearn', 'torch']
missing_packages = []

for package in required_packages:
    try:
        __import__(package)
        print(f'✅ {package} - OK')
    except ImportError:
        print(f'❌ {package} - 설치 필요')
        missing_packages.append(package)

if missing_packages:
    print('\\n일부 패키지가 없습니다. 다음 명령어로 설치하세요:')
    print('pip install -r requirements.txt')
    sys.exit(1)
else:
    print('\\n모든 기본 패키지가 설치되어 있습니다.')
"

if [ $? -ne 0 ]; then
    echo "의존성 문제로 종료합니다."
    exit 1
fi

# Step 2: 챗봇 모델 실행 (수정된 버전)
echo ""
echo "Step 2: 챗봇 모델 실행 중..."
echo "----------------------------------------"

if [ -f "src/chatbot_model_fixed.py" ]; then
    echo "수정된 챗봇 모델 실행 중..."
    cd src
    python chatbot_model_fixed.py
    cd ..

    if [ -f "outputs/chat_output.json" ]; then
        echo "✅ 챗봇 결과 생성 완료: outputs/chat_output.json"
    else
        echo "❌ 챗봇 결과 생성 실패"
    fi
elif [ -f "src/chatbot_model.py" ]; then
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

# Step 3: 실시간 모델 실행 (Optional)
echo ""
echo "Step 3: 실시간 모델 실행 중... (Optional)"
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

# Step 4: 결과 확인
echo ""
echo "Step 4: 생성된 파일 확인"
echo "----------------------------------------"

echo "생성된 출력 파일들:"
if [ -d "outputs" ]; then
    ls -la outputs/

    # 결과 파일 미리보기
    if [ -f "outputs/chat_output.json" ]; then
        echo ""
        echo "챗봇 결과 미리보기 (처음 2개):"
        python -c "
import json
try:
    with open('outputs/chat_output.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    for i, item in enumerate(data[:2]):
        print(f'{i+1}. 질문: {item[\"user\"]}')
        print(f'   답변: {item[\"model\"][:100]}...')
        print()
except Exception as e:
    print(f'파일 읽기 오류: {e}')
"
    fi
else
    echo "outputs 디렉토리가 없습니다."
fi

# Step 5: 웹 UI 실행 확인
echo ""
echo "Step 5: 웹 UI 실행 가능 여부 확인"
echo "----------------------------------------"

# Streamlit 설치 확인
python -c "
try:
    import streamlit
    print('✅ Streamlit이 설치되어 있습니다.')
    print('웹 UI를 실행하려면 다음 명령어를 사용하세요:')
    print('cd src && streamlit run chatbot_ui.py')
except ImportError:
    print('❌ Streamlit이 설치되지 않았습니다.')
    print('다음 명령어로 설치하세요: pip install streamlit')
"

# 사용자에게 UI 실행 여부 묻기
echo ""
read -p "웹 UI를 바로 실행하시겠습니까? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
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
else
    echo "웹 UI를 실행하지 않습니다."
fi

echo ""
echo "========================================"
echo "   챗봇 실행 완료"
echo "========================================"
echo ""
echo "📁 생성된 파일:"
echo "  - outputs/chat_output.json (기본 챗봇 결과)"
if [ -f "outputs/realtime_output.json" ]; then
    echo "  - outputs/realtime_output.json (실시간 챗봇 결과)"
fi
echo ""
echo "🚀 웹 UI 실행:"
echo "  cd src && streamlit run chatbot_ui.py"
echo ""
echo "📞 문제 발생 시:"
echo "  1. Python 버전 확인: python --version"
echo "  2. 패키지 설치: pip install -r requirements.txt"
echo "  3. 수동 실행: cd src && python chatbot_model_fixed.py"