# NanumSlide

AI 기반 프레젠테이션 생성기 - Windows 데스크톱 애플리케이션

## 개요

NanumSlide는 AI를 활용하여 프레젠테이션을 자동 생성하는 Windows 데스크톱 애플리케이션입니다.
PySide6(Qt)를 기반으로 제작되어 네이티브 성능과 사용자 경험을 제공합니다.

## 주요 기능

- **AI 프레젠테이션 생성**: 프롬프트 기반으로 전문적인 프레젠테이션 자동 생성
- **다양한 AI 모델 지원**: OpenAI GPT-5.2, Google Gemini 3, Anthropic Claude 4.5, Ollama
- **DALL-E 이미지 생성**: OpenAI DALL-E 3로 슬라이드에 맞는 이미지 자동 생성
- **참고 자료 업로드**: PDF, DOCX, PPTX, TXT, MD 파일을 참고하여 프레젠테이션 생성
- **PowerPoint 내보내기**: .pptx 형식으로 내보내기
- **다양한 테마**: 여러 가지 프레젠테이션 테마 제공
- **다국어 지원**: 한국어, 영어, 일본어, 중국어

## 스크린샷

(추가 예정)

## 설치

### 사전 요구사항

- Python 3.12 이상
- [uv](https://github.com/astral-sh/uv) 패키지 매니저 (권장)

### 설치 방법

```powershell
# 저장소 클론
git clone https://github.com/kimmingul/NanumSlide.git
cd NanumSlide

# 의존성 설치
uv sync
```

## 실행

### 개발 모드

```powershell
# 가상환경 활성화
.venv\Scripts\activate

# 실행
python -m src.main
```

### 빌드 (실행 파일 생성)

```powershell
# PyInstaller로 빌드
uv run pyinstaller --name NanumSlide --windowed --onefile src/main.py
```

## 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 설정합니다:

```env
# LLM 설정 (openai / google / anthropic / ollama 중 선택)
LLM_PROVIDER=openai

# OpenAI (GPT-5.2 시리즈)
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-5.2  # gpt-5.2, gpt-5.2-pro, gpt-4.1, o4-mini 등

# Google Gemini (Gemini 3 시리즈)
# GOOGLE_API_KEY=your_api_key
# GOOGLE_MODEL=gemini-3-flash-preview  # gemini-3-pro-preview, gemini-2.5-flash 등

# Anthropic Claude (Claude 4.5 시리즈)
# ANTHROPIC_API_KEY=your_api_key
# ANTHROPIC_MODEL=claude-sonnet-4-5-20250514  # claude-opus-4-5, claude-haiku-4-5 등

# Ollama (로컬 AI - Llama 4, DeepSeek 등)
# OLLAMA_URL=http://localhost:11434
# OLLAMA_MODEL=llama4  # llama4, llama3.3, deepseek-r1, qwen3 등

# 이미지 생성 설정 (dall-e-3 / pexels / pixabay / disabled)
IMAGE_PROVIDER=dall-e-3

# Pexels (DALL-E 대신 사용할 경우)
# PEXELS_API_KEY=your_pexels_api_key

# Pixabay (DALL-E 대신 사용할 경우)
# PIXABAY_API_KEY=your_pixabay_api_key
```

## 사용 방법

1. **API 키 설정**: 설정 메뉴에서 OpenAI API 키를 입력합니다.
2. **프롬프트 입력**: 우측 패널에서 프레젠테이션 주제를 입력합니다.
3. **옵션 설정**: 슬라이드 수, AI 모델, 언어, 테마를 선택합니다.
4. **참고 자료 업로드** (선택): PDF, DOCX 등의 파일을 업로드하여 참고 자료로 활용합니다.
5. **생성**: "프레젠테이션 생성" 버튼을 클릭합니다.
6. **편집**: 생성된 슬라이드를 확인하고 필요시 수정합니다.
7. **내보내기**: 파일 메뉴에서 PowerPoint로 내보냅니다.

## 지원 파일 형식

### 참고 자료 업로드

- PDF (`.pdf`) - PyMuPDF 필요
- Word (`.docx`, `.doc`) - python-docx 필요
- PowerPoint (`.pptx`, `.ppt`) - python-pptx 필요
- 텍스트 (`.txt`, `.md`) - 기본 지원

### 내보내기

- PowerPoint (`.pptx`)

## 프로젝트 구조

```
NanumSlide/
├── src/
│   ├── main.py                    # 앱 진입점
│   ├── config.py                  # 설정 관리
│   ├── ui/                        # UI 컴포넌트
│   │   ├── main_window.py         # 메인 윈도우
│   │   ├── slide_editor.py        # 슬라이드 에디터
│   │   ├── dialogs/               # 대화상자
│   │   │   └── settings_dialog.py # 설정 대화상자
│   │   └── widgets/               # 위젯
│   │       ├── prompt_panel.py    # AI 프롬프트 패널
│   │       └── slide_thumbnail.py # 슬라이드 썸네일
│   ├── core/                      # 핵심 비즈니스 로직
│   │   ├── presentation.py        # 프레젠테이션 모델
│   │   ├── themes.py              # 테마 정의
│   │   └── export/                # 내보내기
│   │       └── pptx_exporter.py   # PowerPoint 내보내기
│   └── services/                  # 외부 서비스 연동
│       ├── llm_client.py          # LLM 클라이언트
│       ├── image_service.py       # 이미지 서비스 (DALL-E, Pexels, Pixabay)
│       ├── presentation_generator.py # 프레젠테이션 생성기
│       └── generation_worker.py   # 백그라운드 생성 워커
├── resources/                     # 리소스 파일
│   ├── icons/
│   └── styles/
├── tests/
├── pyproject.toml
└── README.md
```

## 의존성

주요 패키지:

- `pyside6` - Qt 기반 GUI
- `openai` - OpenAI API (Responses API)
- `anthropic` - Anthropic Claude API
- `google-generativeai` - Google Gemini API
- `python-pptx` - PowerPoint 생성
- `pymupdf` - PDF 텍스트 추출
- `python-docx` - Word 문서 읽기
- `httpx` - HTTP 클라이언트
- `pydantic` - 데이터 검증

## 라이선스

Apache 2.0
