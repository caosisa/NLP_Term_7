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
│   └── train.json                 # 학습 데이터
├── src/                           # 소스 코드
│   ├── classifier.ipynb           # 질문 유형 분류기
│   ├── chatbot_model.py           # 챗봇 모델
│   ├── chatbot_ui.py              # 웹 UI
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
- 모델: klue/roberta-large
- 5개 카테고리 분류
- JSON 형식 결과 출력

### 2. 챗봇 모델
- 모델: Qwen/Qwen3-14B-AWQ
- 키워드 기반 구체적 답변 제공
- JSON 형식 테스트 결과 출력

### 3. 웹 UI
- gradio 기반 인터페이스
- 실시간 질문 입력 및 응답 확인 가능

### 4. 실시간 정보 반영 (Optional)
- 셔틀버스/식단/공지사항 웹 크롤링 구현
- 실시간 업데이트 대응 가능 구조로 설계됨

## 📊 성능 요약

- **분류 모델**: KLUE RoBERTa-Large (337M)
- **테스트 성능**: 쉬운 질문: 100%, 혼동 질문: 83.33%
- **챗봇 모델**: Qwen3-14B-AWQ (4bit 양자화)

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
- **ML Framework**: PyTorch 2.5.1, Transformers 4.52.4
- **Web Framework**: Gradio
- **Data Processing**: Pandas, NumPy, Scikit-learn
- **Web Scraping**: Requests, BeautifulSoup4

## 📝 개발 노트

- 학습 데이터는 GPT 기반 생성 → 수동 검수 및 보정
- LLM 프롬프트 길이 제한으로 분류기를 활용하려 했으나, 오분류 우려로 미사용

## 👥 팀 정보

- **팀명**: 7조
- **프로젝트 기간**: 2024.05 - 2024.06
- **소속**: 충남대학교 인공지능학과

## 📞 문의사항

프로젝트 관련 문의사항이 있으시면 이슈로 등록해주세요.

---

**충남대학교 컴퓨터공학과 자연어처리 Term Project**  
*Last Updated: 2024-06-09*
