#!/bin/bash

# 충남대 Campus ChatBot 실행 스크립트 (개선 버전)
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

# requirements.txt가 있으면 설치
if [ -f "requirements.txt" ]; then
    echo "requirements.txt 발견. 패키지 설치 중..."
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt 파일이 없습니다."
fi

# 필수 패키지 확인
python -c "
import sys
required_packages = ['json', 'os', 'torch', 'transformers', 'requests', 'beautifulsoup4']
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
    for pkg in missing_packages:
        if pkg == 'beautifulsoup4':
            print(f'pip install {pkg}')
        else:
            print(f'pip install {pkg}')
else:
    print('\\n모든 기본 패키지가 설치되어 있습니다.')
"

# Step 2: 챗봇 모델 실행
echo ""
echo "Step 2: 챗봇 모델 실행 중..."
echo "----------------------------------------"

# 여러 가능한 챗봇 모델 파일 확인 및 실행
CHATBOT_EXECUTED=false

if [ -f "src/chatbot_model_fixed.py" ]; then
    echo "수정된 챗봇 모델 실행 중..."
    cd src
    python chatbot_model_fixed.py
    cd ..
    CHATBOT_EXECUTED=true
elif [ -f "src/chatbot_model.py" ]; then
    echo "기본 챗봇 모델 실행 중..."
    cd src
    python chatbot_model.py
    cd ..
    CHATBOT_EXECUTED=true
else
    echo "❌ 챗봇 모델 파일을 찾을 수 없습니다."
fi

# 챗봇 결과 확인
if [ -f "outputs/chat_output.json" ]; then
    echo "✅ 챗봇 결과 생성 완료: outputs/chat_output.json"
else
    echo "❌ 챗봇 결과 생성 실패"
    if [ "$CHATBOT_EXECUTED" = true ]; then
        echo "💡 모델이 실행되었지만 출력 파일이 생성되지 않았습니다."
    fi
fi

# Step 3: 웹 UI 실행 확인
echo ""
echo "Step 3: 웹 UI 실행 가능 여부 확인"
echo "----------------------------------------"

# UI 파일 확인
UI_FILE=""
if [ -f "src/chatbot_ui.py" ]; then
    UI_FILE="src/chatbot_ui.py"
elif [ -f "chatbot_ui.py" ]; then
    UI_FILE="chatbot_ui.py"
fi

if [ -n "$UI_FILE" ]; then
    echo "✅ UI 파일 발견: $UI_FILE"

    # 필요한 UI 라이브러리 확인
    python -c "
ui_libraries = ['gradio', 'streamlit', 'flask']
available_ui = []

for lib in ui_libraries:
    try:
        __import__(lib)
        available_ui.append(lib)
        print(f'✅ {lib}이 설치되어 있습니다.')
    except ImportError:
        print(f'❌ {lib}이 설치되지 않았습니다.')

if available_ui:
    print(f'\\n사용 가능한 UI 라이브러리: {\", \".join(available_ui)}')
else:
    print('\\n웹 UI를 위해 다음 중 하나를 설치하세요:')
    print('pip install gradio  # 또는')
    print('pip install streamlit  # 또는')
    print('pip install flask')
"

    # 사용자에게 UI 실행 여부 묻기
    echo ""
    read -p "웹 UI를 바로 실행하시겠습니까? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "웹 UI를 실행합니다..."
        echo "브라우저에서 표시되는 주소를 열어주세요."
        echo ""
        echo "UI 종료하려면 Ctrl+C를 누르세요."
        echo ""

        # UI 파일이 src 폴더에 있는지 확인하고 실행
        if [[ "$UI_FILE" == src/* ]]; then
            cd src
            python chatbot_ui.py
            cd ..
        else
            python $UI_FILE
        fi
    else
        echo "웹 UI를 실행하지 않습니다."
        echo ""
        echo "나중에 UI를 실행하려면 다음 명령어를 사용하세요:"
        if [[ "$UI_FILE" == src/* ]]; then
            echo "cd src && python chatbot_ui.py"
        else
            echo "python $UI_FILE"
        fi
    fi
else
    echo "❌ UI 파일을 찾을 수 없습니다."
    echo "💡 다음 파일 중 하나가 필요합니다:"
    echo "   - src/chatbot_ui.py"
    echo "   - chatbot_ui.py"
fi

echo ""
echo "========================================"
echo "   챗봇 실행 완료"
echo "========================================"
echo ""
echo "📁 생성된 파일:"
echo "  - outputs/chat_output.json (기본 챗봇 결과)"
if [ -f "outputs/cls_output.json" ]; then
    echo "  - outputs/cls_output.json (분류 결과)"
fi
echo ""
echo "🚀 수동 실행 명령어:"
if [ -n "$UI_FILE" ]; then
    if [[ "$UI_FILE" == src/* ]]; then
        echo "  웹 UI: cd src && python chatbot_ui.py"
    else
        echo "  웹 UI: python $UI_FILE"
    fi
fi
echo "  챗봇 모델: cd src && python chatbot_model.py"
echo ""
echo "📞 문제 발생 시:"
echo "  1. Python 버전 확인: python --version"
echo "  2. 패키지 설치: pip install -r requirements.txt"
echo "  3. GPU 메모리 확인: nvidia-smi (GPU 사용 시)"
echo "  4. 로그 확인: 실행 중 오류 메시지 참고"