# 충남대 Campus ChatBot

충남대학교 재학생들을 위한 AI 챗봇 시스템

## 📋 프로젝트 개요

이 프로젝트는 충남대학교 재학생들이 학교 생활에 필요한 정보를 쉽게 얻을 수 있도록 도와주는 AI 챗봇입니다.

### 지원하는 질문 유형
- **졸업요건** (0): 졸업학점, 전공/교양 졸업 요건 등
- **학교 공지사항** (1): 학교/학과 공지사항
- **학사일정** (2): 수강 신청/정정 기간, 학기 일정 등
- **식단 안내** (3): 교내 식당의 주간/일일 시간표
- **통학/셔틀 버스** (4): 버스 시간표, 정류장 위치, 운행 여부 등

## 🚀 설치 및 실행

### 1. 환경 설정

```bash
# 패키지 설치
pip install -r requirements.txt
```

### 2. 모델 훈련 (분류기)

```bash
# Jupyter 노트북으로 실행
jupyter notebook src/classifier.ipynb

# 또는 Colab에서 실행
```

### 3. 챗봇 실행

```bash
# 실행 권한 부여
chmod +x chatbot.sh

# 챗봇 실행
./chatbot.sh
```

## 📁 디렉토리 구조

```
Termproject_{조}/
├── data/                          # 데이터 파일들
│   ├── train.json                 # 학습 데이터
│   ├── valid.json                 # 검증 데이터 (선택)
│   ├── test_cls.json              # 분류기 테스트 데이터
│   ├── test_chat.json             # 챗봇 테스트 데이터
│   └── test_realtime.json         # 실시간 테스트 데이터
├── src/                           # 소스 코드
│   ├── classifier.ipynb           # 질문 유형 분류기
│   ├── chatbot_model.py           # 챗봇 모델
│   ├── chatbot_ui.py              # 웹 UI
│   └── realtime_model.py          # 실시간 정보 모델
├── model/                         # 학습된 모델 파일
│   ├── config.json
│   ├── pytorch_model.bin
│   └── tokenizer files...
├── outputs/                       # 결과 파일들
│   ├── cls_output.json            # 분류기 결과
│   ├── chat_output.json           # 챗봇 결과
│   └── realtime_output.json       # 실시간 결과
├── chatbot.sh                     # 실행 스크립트
├── requirements.txt               # 패키지 목록
└── README.md                      # 프로젝트 설명서
```

## 🔧 주요 기능

### 1. 질문 유형 분류기
- KLUE-BERT 기반 5개 카테고리 분류
- F1 Score 기반 성능 평가
- JSON 형식 결과 출력

### 2. 챗봇 모델
- 카테고리별 맞춤 응답 생성
- 키워드 기반 구체적 답변 제공
- JSON 형식 테스트 결과 출력

### 3. 웹 UI
- Streamlit 기반 사용자 친화적 인터페이스
- 실시간 채팅 형식 구현
- 카테고리별 색상 구분

### 4. 실시간 정보 반영 (Optional)
- 웹 크롤링을 통한 최신 정보 수집
- 캐시 시스템으로 효율적 데이터 관리
- 공지사항, 셔틀버스, 식단 등 실시간 업데이트

## 💻 사용 방법

### 웹 UI 사용
1. `./chatbot.sh` 실행
2. 브라우저에서 `http://localhost:8501` 접속
3. 질문 입력하여 챗봇과 대화

### API 사용 (코드)
```python
from src.chatbot_model import CampusChatBot

# 챗봇 초기화
chatbot = CampusChatBot()

# 질문하기
result = chatbot.chat("졸업까지 몇 학점을 들어야 하나요?")
print(result["response"])
```

## 📊 성능 평가

### 분류기 성능
- **평가 지표**: F1 Score (Weighted)
- **모델**: KLUE-BERT-base
- **데이터셋**: 5개 카테고리 균형 데이터

### 챗봇 성능
- **UI 구동**: 10점
- **Chat Interaction**: 10점  
- **응답 품질**: 40점

## 🔍 예시 질문 및 응답

**졸업요건 관련**
- Q: "졸업까지 몇 학점을 들어야 하나요?"
- A: "일반적으로 총 130학점 이상을 이수해야 졸업할 수 있습니다..."

**식단 안내**
- Q: "오늘 학식 뭐 나와요?"
- A: "오늘(2024-06-09, 일요일) 식단입니다: 🍽️ 중식: 김치찌개..."

**셔틀버스**
- Q: "셔틀버스 시간표를 알려주세요"
- A: "🚌 셔틀버스 실시간 정보: 현재 상태: 등교 시간 운행 중..."

## 🛠️ 기술 스택

- **Language**: Python 3.10.12
- **ML Framework**: PyTorch 2.5.1, Transformers 4.35.0
- **Web Framework**: Streamlit 1.28.1
- **Data Processing**: Pandas, NumPy, Scikit-learn
- **Web Scraping**: Requests, BeautifulSoup4

## 📝 개발 노트

### 훈련 과정
1. **데이터 수집**: 5개 카테고리별 균형있는 학습 데이터 구축
2. **전처리**: 텍스트 정규화 및 토큰화
3. **모델 훈련**: KLUE-BERT fine-tuning (3 epochs)
4. **성능 평가**: F1 Score 기반 모델 선택

### 주요 도전과제 및 해결방안
- **데이터 부족**: 샘플 데이터 증강 및 다양한 표현 방식 학습
- **실시간 정보**: 캐시 시스템으로 API 호출 최적화
- **응답 품질**: 키워드 기반 매칭으로 구체적 답변 제공

## 👥 팀 정보

- **팀명**: {조}조
- **프로젝트 기간**: 2024.05 - 2024.06
- **소속**: 충남대학교 컴퓨터공학과

## 📞 문의사항

프로젝트 관련 문의사항이 있으시면 이슈로 등록해주세요.

---

**충남대학교 컴퓨터공학과 자연어처리 Term Project**  
*Last Updated: 2024-06-09*