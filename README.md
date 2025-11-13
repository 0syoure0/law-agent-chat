# ⚖️ 법령 AI 어시스턴트

민법 기반 RAG(Retrieval-Augmented Generation) 챗봇 시스템

## 📋 목차

- [프로젝트 소개](#-프로젝트-소개)
- [주요 기능](#-주요-기능)
- [기술 스택](#-기술-스택)
- [시스템 아키텍처](#-시스템-아키텍처)
- [설치 방법](#-설치-방법)
- [실행 방법](#-실행-방법)
- [사용 방법](#-사용-방법)
- [API 문서](#-api-문서)
- [성능 최적화](#-성능-최적화)
- [트러블슈팅](#-트러블슈팅)

## 🎯 프로젝트 소개

공무원과 법률 실무자들이 업무 수행 시 필요한 법령 정보를 쉽고 빠르게 찾을 수 있도록 돕는 AI 기반 챗봇입니다.

### 핵심 가치
- 💡 **쉬운 이해**: 복잡한 법령을 일상 언어로 설명
- ⚡ **빠른 검색**: 1210개 민법 조문에서 즉시 검색
- 📚 **정확한 출처**: 참조 조문 자동 표시
- 🎯 **실무 적용**: 구체적인 예시와 가이드 제공
- 💾 **스마트 캐싱**: 동일 질문 즉시 응답
- 🔒 **안전한 사용**: Rate Limiting으로 안정적 운영

## ✨ 주요 기능

### 1. RAG 기반 법령 검색
- **ChromaDB** 벡터 데이터베이스
- **HuggingFace** 다국어 임베딩 모델
- 의미 기반 유사도 검색 (Top-K: 7)
- 1210개 민법 조문 실시간 검색

### 2. 정확한 답변 생성
- **Google Gemini 1.5 Flash** 사용
- RAG 컨텍스트 기반 답변
- 참조 조문 자동 표시
- 대화 히스토리 관리
- 출처 추적 가능

### 3. 성능 최적화
- **응답 캐싱** (30분 TTL, 최대 100개)
- **Rate Limiting** (분당 10회)
- **재시도 로직** (지수 백오프)
- API 할당량 관리

### 4. 직관적인 UI
- 실시간 채팅 인터페이스
- 대화 히스토리 관리
- 반응형 디자인
- 로딩 상태 표시

## 🛠 기술 스택

### Backend
- **Python** 3.10+
- **FastAPI** - 고성능 웹 프레임워크
- **LangChain** - LLM 체인 관리
- **ChromaDB** - 벡터 데이터베이스
- **Google Gemini 1.5 Flash** - LLM
- **HuggingFace Embeddings** - 다국어 임베딩
  - 모델: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
- **PyPDF** - PDF 파싱

### Frontend
- **React** 18+
- **JavaScript** (ES6+)
- **CSS3**
- **Fetch API**

### DevOps
- **Git** - 버전 관리
- **GitHub** - 코드 저장소
- **python-dotenv** - 환경 변수 관리

## 🏗 시스템 아키텍처

```
┌─────────────┐
│ 사용자 질문 │
└──────┬──────┘
       ↓
┌──────────────────────┐
│ 질문 임베딩          │
│ (HuggingFace)        │
└──────┬───────────────┘
       ↓
┌──────────────────────┐     ┌─────────────────┐
│ ChromaDB 벡터 검색   │ ←── │ 민법 1210개 조문│
│ (Top-K: 7)           │     └─────────────────┘
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│ RAG 컨텍스트 구성    │
│ (관련 조문 병합)     │
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│ Gemini LLM 생성      │
│ (Temperature: 0.1)   │
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│ AI 답변 + 출처       │
│ (참조 조문 표시)     │
└──────────────────────┘
```

### Rate Limiting & Caching

```
요청 → Rate Limiter (분당 10회)
         ↓
      캐시 확인
         ↓
    캐시 Hit? → Yes → 즉시 응답 (0.1초)
         ↓ No
    벡터 검색 + LLM 생성 (3-5초)
         ↓
      캐시 저장
         ↓
       응답 반환
```

## 📦 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/0syoure0/law-agent-chat.git
cd law-agent-chat
```

### 2. 백엔드 설정

```bash
cd backend

# 가상환경 생성 (Windows)
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

**주요 패키지:**
```
fastapi
uvicorn[standard]
python-dotenv
pydantic
google-generativeai
langchain
langchain-google-genai
langchain-community
chromadb
pypdf
sentence-transformers
```

### 3. API 키 설정

1. [Google AI Studio](https://aistudio.google.com/app/apikey) 접속
2. **Create API key** 클릭하여 키 발급
3. `backend/.env` 파일 생성:

```env
GEMINI_API_KEY=your-api-key-here
```

**⚠️ 중요:** `.env` 파일을 Git에 커밋하지 마세요!

### 4. 법령 파일 확인

`backend/` 폴더에 법령 PDF 파일이 있는지 확인:
```
backend/
├── 민법(법률)(제20432호)(20250131).pdf  ✅
└── ...
```

### 5. 프론트엔드 설정

```bash
cd ../frontend

# 패키지 설치
npm install

# 또는 yarn 사용
yarn install
```

## 🚀 실행 방법

### 백엔드 서버 실행

```bash
cd backend

# 가상환경 활성화 (Windows)
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate

# 서버 실행
python api_server.py
```

**성공 메시지:**
```
🚀 법령 AI 서버 시작 중...
📊 모델: gemini-1.5-flash
⏱️  Rate Limit: 10회/60초
💾 캐시: 최대 100개, TTL 1800초
📄 법령 파일 로드 중: 1개
✅ 법령 AI 서버 준비 완료!
📚 문서 수: 1210개
INFO: Uvicorn running on http://0.0.0.0:8000
```

**⏱ 첫 실행 시간:**
- 임베딩 모델 다운로드: 1-2분 (약 1.1GB)
- 벡터 데이터베이스 생성: 2-3분
- 총 소요 시간: 3-5분

### 프론트엔드 실행

**새 터미널을 열어서:**

```bash
cd frontend

# 개발 서버 실행
npm start

# 또는 Vite 사용 시
npm run dev
```

**접속 URL:**
- 🌐 프론트엔드: http://localhost:3000
- 📡 백엔드 API: http://localhost:8000
- 📚 API 문서: http://localhost:8000/docs

## 💬 사용 방법

### 예시 질문

**기본 질문:**
```
✅ 권리능력은 언제 시작되나요?
✅ 민법 제750조의 내용은?
✅ 계약이란 무엇인가요?
```

**구체적 질문:**
```
✅ 부동산 매매계약 체결 시 주의사항은?
✅ 소유권 취득시효는 몇 년인가요?
✅ 불법행위로 인한 손해배상 청구 요건은?
```

**실무 질문:**
```
✅ 계약 해지와 해제의 차이점은?
✅ 미성년자가 체결한 계약은 유효한가요?
✅ 점유취득시효와 등기부취득시효의 차이는?
```

### 효과적인 질문 팁

1. **구체적으로 질문하기**
   - ❌ "계약에 대해 알려줘"
   - ✅ "계약의 성립 요건은 무엇인가요?"

2. **조문 번호 포함하기**
   - ✅ "민법 제750조는 어떤 내용인가요?"

3. **상황 명확히 설명하기**
   - ✅ "A가 B에게 물건을 팔았는데, 계약서를 작성하지 않았어요. 계약이 성립했나요?"

4. **대화 이어가기**
   - 이전 질문의 맥락이 유지됩니다

## 📡 API 문서

### POST /api/chat

법령 질문에 대한 답변 생성

**Request:**
```json
{
  "question": "권리능력은 언제 시작되나요?"
}
```

**Response:**
```json
{
  "answer": "권리능력은 사람이 태어난 때부터 시작됩니다. 민법 제3조에서는...",
  "sources": [
    "민법(법률)(제20432호)(20250131).pdf"
  ],
  "articles": [
    "【제3조】(권리능력의 존속기간)"
  ],
  "success": true,
  "cached": false,
  "remaining_requests": 9
}
```

**Response Fields:**
- `answer`: AI가 생성한 답변
- `sources`: 참조한 문서 목록
- `articles`: 관련 조문 목록
- `success`: 성공 여부
- `cached`: 캐시된 응답 여부
- `remaining_requests`: 남은 요청 횟수

### GET /api/health

서버 상태 확인

**Response:**
```json
{
  "status": "healthy",
  "document_count": 1210,
  "model": "gemini-1.5-flash",
  "rate_limit": {
    "max_requests": 10,
    "time_window": 60,
    "remaining": 10
  },
  "cache": {
    "size": 15,
    "max_size": 100,
    "ttl": 1800
  }
}
```

### POST /api/reset

대화 히스토리 초기화

**Response:**
```json
{
  "message": "대화가 초기화되었습니다.",
  "remaining_requests": 10
}
```

### GET /api/stats

서버 통계 조회

**Response:**
```json
{
  "rate_limit": {
    "max_requests": 10,
    "time_window": 60,
    "remaining": 8,
    "wait_time": 0
  },
  "cache": {
    "size": 25,
    "max_size": 100,
    "ttl": 1800
  },
  "documents": 1210
}
```

### POST /api/cache/clear

캐시 초기화 (관리자용)

**Response:**
```json
{
  "message": "캐시가 초기화되었습니다.",
  "cache_stats": {
    "size": 0,
    "max_size": 100,
    "ttl": 1800
  }
}
```

**자동 문서:** http://localhost:8000/docs (Swagger UI)

## ⚡ 성능 최적화

### 1. 응답 캐싱
- **TTL**: 30분 (1800초)
- **최대 크기**: 100개 답변
- **효과**: 동일 질문 0.1초 응답

### 2. Rate Limiting
- **제한**: 분당 10회
- **목적**: API 할당량 보호
- **초과 시**: 대기 시간 안내

### 3. 재시도 로직
- **최대 재시도**: 3회
- **지수 백오프**: 2초 → 4초 → 8초
- **대상**: 일시적 API 오류

### 4. 벡터 검색 최적화
- **Top-K**: 7개 조문 검색
- **Chunk Size**: 800자
- **Overlap**: 200자

### 성능 지표

| 작업 | 시간 |
|------|------|
| 캐시 Hit | 0.1초 |
| 벡터 검색 | 1-2초 |
| LLM 생성 | 3-5초 |
| 전체 (캐시 Miss) | 4-7초 |

## 🔧 트러블슈팅

### 1. API 키 오류

**증상:**
```
❌ GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.
```

**해결:**
1. `backend/.env` 파일 확인
2. API 키 형식 확인
3. 가상환경 재시작

```bash
# .env 파일 내용 확인
cat backend/.env

# 가상환경 재활성화
deactivate
.venv\Scripts\activate
```

### 2. 모델 오류

**증상:**
```
404 models/gemini-1.5-flash is not found
```

**해결:**
`api_server.py` 71번째 줄 확인:
```python
# 올바른 모델명
model_name="gemini-1.5-flash"  # ✅
```

### 3. PDF 파일 오류

**증상:**
```
❌ 법령 파일을 찾을 수 없습니다
```

**해결:**
1. PDF 파일이 `backend/` 폴더에 있는지 확인
2. 파일명이 정확한지 확인
```bash
ls backend/*.pdf
```

### 4. 패키지 오류

**증상:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**해결:**
```bash
# 가상환경 확인
which python  # Mac/Linux
where python  # Windows

# 패키지 재설치
pip install -r requirements.txt
```

### 5. 백엔드 연결 실패

**증상:**
```
Failed to fetch
백엔드 서버가 실행 중인지 확인해주세요.
```

**해결:**
1. 백엔드 서버 실행 확인
```bash
curl http://localhost:8000
```

2. 포트 충돌 확인
```bash
# Windows
netstat -ano | findstr :8000

# Mac/Linux
lsof -i :8000
```

3. CORS 설정 확인 (`api_server.py`)
```python
allow_origins=["http://localhost:3000", "http://localhost:5173"]
```

### 6. API 할당량 초과

**증상:**
```
429 You exceeded your current quota
```

**해결:**
1. Rate Limiting 설정 확인
2. 캐시 활용
3. API 키 확인 (무료 tier 제한)
4. 잠시 대기 후 재시도

### 7. 느린 응답 속도

**원인 & 해결:**

| 원인 | 해결 방법 |
|------|----------|
| 첫 실행 | 정상 (모델 로딩) |
| 캐시 미사용 | 동일 질문 재질문 |
| API 지연 | 재시도 기다리기 |
| 복잡한 질문 | 질문 단순화 |

## 🔒 보안 주의사항

### ⚠️ 절대 하지 말 것

- ❌ `.env` 파일을 Git에 커밋
- ❌ API 키를 코드에 하드코딩
- ❌ API 키를 공개 채팅방에 공유
- ❌ API 키를 스크린샷에 노출

### ✅ 해야 할 것

- ✅ `.gitignore`에 `.env` 추가 확인
- ✅ 팀원들은 각자 API 키 발급
- ✅ `.env.example`만 저장소에 공유
- ✅ API 키 주기적 재발급

**`.gitignore` 필수 내용:**
```
# Environment
.env
.env.local

# Python
.venv/
__pycache__/
*.pyc

# Database
chroma_db/

# Frontend
node_modules/
build/
dist/
```

## 👥 팀원 가이드

### 새 팀원 설정 (5분 완성!)

#### 1️⃣ 저장소 클론
```bash
git clone https://github.com/0syoure0/law-agent-chat.git
cd law-agent-chat
```

#### 2️⃣ API 키 발급
1. [Google AI Studio](https://aistudio.google.com/app/apikey) 접속
2. **Create API key** 클릭
3. 키 복사

#### 3️⃣ 백엔드 설정
```bash
cd backend

# 가상환경 생성
python -m venv .venv

# 활성화 (Windows)
.venv\Scripts\activate

# 활성화 (Mac/Linux)
source .venv/bin/activate

# 패키지 설치
pip install -r requirements.txt

# .env 파일 생성 (Windows PowerShell)
echo GEMINI_API_KEY=발급받은키 > .env

# .env 파일 생성 (Mac/Linux/Git Bash)
echo "GEMINI_API_KEY=발급받은키" > .env
```

#### 4️⃣ 프론트엔드 설정
```bash
cd ../frontend
npm install
```

#### 5️⃣ 실행!
```bash
# 터미널 1: 백엔드
cd backend
.venv\Scripts\activate
python api_server.py

# 터미널 2: 프론트엔드
cd frontend
npm start
```

### Git 작업 흐름

```bash
# 1. 최신 코드 받기
git pull origin main

# 2. 작업 브랜치 생성 (선택)
git checkout -b feature/기능명

# 3. 작업 후 커밋
git add .
git commit -m "작업 내용 설명"

# 4. Push
git push origin main
# 또는 브랜치로
git push origin feature/기능명
```

### Collaborator 권한 필요

**Push 권한이 필요하면:**
1. GitHub 계정 알려주기
2. 저장소 주인이 Settings → Collaborators에서 초대
3. 이메일 확인 후 수락

## 📁 프로젝트 구조

```
law-agent-chat/
├── backend/
│   ├── .env                      # 🔒 환경 변수 (Git 제외!)
│   ├── .env.example              # 환경 변수 예시
│   ├── api_server.py             # FastAPI 서버 (Rate Limiting, Caching)
│   ├── Law_agent.py              # RAG 엔진 (벡터 검색, LLM 호출)
│   ├── requirements.txt          # Python 패키지
│   ├── 민법(법률)(제20432호).pdf  # 법령 문서
│   └── chroma_db/                # 벡터 데이터베이스 (자동 생성)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # 메인 컴포넌트
│   │   └── App.css               # 스타일
│   ├── public/
│   ├── package.json              # npm 패키지
│   └── package-lock.json
│
├── .gitignore                    # Git 제외 파일
├── README.md                     # 프로젝트 문서
└── LICENSE                       # 라이센스 (선택)
```



## 📈 향후 계획

### 단기 (1개월)
- [x] Rate Limiting 구현
- [x] 응답 캐싱 구현
- [x] 에러 처리 개선
- [ ] 프론트엔드 UI/UX 개선
- [ ] 로딩 상태 시각화

### 중기 (2-3개월)
- [ ] 더 많은 법령 추가 (상법, 형법, 행정법)
- [ ] 대화 저장 기능
- [ ] 북마크 기능
- [ ] 검색 히스토리

### 장기 (6개월+)
- [ ] 사용자 인증 시스템
- [ ] 모바일 앱 (React Native)
- [ ] 음성 인식 질문
- [ ] 다국어 지원 (영어, 일본어)
- [ ] 법령 비교 기능

## 🧪 테스트

### 수동 테스트

```bash
# 헬스 체크
curl http://localhost:8000/api/health

# 질문 테스트
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "권리능력은 언제 시작되나요?"}'

# 통계 확인
curl http://localhost:8000/api/stats
```

### 브라우저 테스트

1. http://localhost:8000/docs 접속
2. Swagger UI에서 API 테스트
3. Try it out 버튼으로 직접 실행

## 📚 참고 자료

### 공식 문서
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [LangChain 문서](https://python.langchain.com/)
- [Google Gemini API](https://ai.google.dev/docs)
- [ChromaDB 문서](https://docs.trychroma.com/)

### 학습 자료
- [RAG 개념 이해](https://python.langchain.com/docs/tutorials/rag/)
- [벡터 데이터베이스 소개](https://www.pinecone.io/learn/vector-database/)
