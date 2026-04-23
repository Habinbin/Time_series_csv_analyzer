# Time Series CSV Analyzer

시계열 CSV 데이터를 브라우저에서 인터랙티브하게 시각화하는 풀스택 웹 애플리케이션.  
EnergyPlus 시뮬레이션 결과(`eplusout.csv`) 등 대용량 시계열 CSV를 드래그&드롭으로 업로드하고, 다양한 변수를 동시에 비교할 수 있습니다.

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| **CSV 드래그&드롭 업로드** | 브라우저에서 CSV를 드롭하면 SQLite에 즉시 반영 |
| **다변수 동시 시각화** | 축(Axis)별로 여러 변수를 선택해 하나의 차트에 오버레이 |
| **LTTB 다운샘플링** | 수십만 행 데이터를 시각 품질 손실 없이 1,000~1,200포인트로 압축 |
| **인터랙티브 Zoom** | 마우스 휠·슬라이더로 구간 확대, 백엔드가 해당 구간만 재조회 |
| **날짜 레이블 제어** | Start/End 날짜 셀렉터로 X축 날짜 표기 조정 (데이터 개수는 고정) |
| **단위 변환** | 변수별 소스/타겟 단위 선택으로 자동 변환 (W↔kW 등) |
| **차트 내보내기** | PNG(300 DPI) / SVG 고해상도 저장, 클립보드 복사 |
| **Y축 레이블 인라인 편집** | Y축 이름 텍스트를 직접 클릭해 제자리 수정 |
| **다중 Axis 추가** | `+ Add Axis`로 독립적인 Y축을 가진 차트 패널을 무제한 추가 |
| **차트 타입 전환** | Line / Scatter / Area 전환 |
| **색상·선 스타일 지정** | 변수별 색상, 선 종류(solid/dashed/dotted 등) 개별 설정 |

---

## 아키텍처

```
Time_series_csv_analyzer/
├── backend/                  # FastAPI (Python 3.12)
│   ├── main.py               # CORS, SPA 폴백 서빙, 라우터 등록
│   └── features/
│       └── simulation/
│           ├── router.py     # /api/v1/simulation/* 엔드포인트
│           ├── service.py    # SQLite 조회, LTTB 다운샘플링 로직
│           └── schemas.py    # Pydantic 요청/응답 스키마
│   └── simulation_results.sqlite  # CSV 업로드 시 여기 저장됨
│
├── frontend/                 # SvelteKit 5 (Svelte 5 Runes)
│   └── src/lib/features/
│       └── interactive-viewer/
│           ├── InteractiveViewer.svelte  # 최상위 뷰어 (날짜 컨트롤, Axis 목록)
│           ├── AxisRow.svelte            # 단일 Axis 행 (ChartControls + SingleChart)
│           ├── state.svelte.ts           # 전역 Reactive State (ViewerState 클래스)
│           ├── units.ts                  # 단위 변환 유틸
│           └── components/
│               ├── SingleChart.svelte    # ECharts 차트 렌더러
│               └── ChartControls.svelte  # 변수 선택, 색상, 범위 등 컨트롤
│
├── Dockerfile                # 멀티스테이지 빌드 (Railway 배포용)
├── eplusout.csv              # 예제 EnergyPlus 시뮬레이션 결과
└── simulation_results.sqlite # (심볼릭 또는 복사본, 백엔드 내부 경로와 동기화)
```

### 데이터 흐름

```
CSV 업로드
  → backend/features/simulation/service.py (pandas chunksize 청크 처리)
  → simulation_results.sqlite (ashpb_pv_ess_1yr 테이블)

차트 렌더링
  → state.svelte.ts fetchResults()
  → POST /api/v1/simulation/results  { variables, threshold, xmin, xmax(0~1 ratio), dates }
  → service.get_downsampled_data()
      ├─ rowid 슬라이싱: min_idx = xmin × n_total  (날짜와 무관, 항상 전체 행 기준)
      ├─ X축 스케일:    minutes_per_point = span_days × 1440 / n_total
      └─ LTTB 압축:    threshold=1200 포인트로 다운샘플
  → SingleChart.svelte (ECharts 렌더링)
```

---

## 기술 스택

### Backend
| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| FastAPI | ≥0.135.3 | REST API 서버 |
| uvicorn | ≥0.44.0 | ASGI 서버 |
| pandas | ≥3.0.1 | CSV 파싱, SQLite 저장 |
| lttb | ≥0.3.1 | Largest-Triangle-Three-Buckets 다운샘플링 |
| python-multipart | ≥0.0.26 | 파일 업로드 |
| SQLite | 내장 | 시뮬레이션 결과 저장소 |

### Frontend
| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| SvelteKit | ^2.57.0 | 풀스택 프레임워크 |
| Svelte | ^5.55.2 | UI (Runes 모드) |
| ECharts | ^6.0.0 | 인터랙티브 차트 |
| openapi-fetch | ^0.17.0 | 타입세이프 API 클라이언트 |
| Vite | ^8.0.7 | 빌드 도구 |

---

## 로컬 실행

### 사전 요구사항
- Python ≥ 3.12 + [uv](https://docs.astral.sh/uv/)
- Node.js ≥ 22 + pnpm

### Backend

```bash
cd backend
uv run uvicorn main:app --reload --port 8402
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

`.env.local` 예시:
```
VITE_API_BASE_URL=http://localhost:8402
```

---

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| `GET` | `/api/v1/simulation/variables` | 업로드된 CSV의 변수 목록 반환 |
| `POST` | `/api/v1/simulation/results` | 다운샘플된 시계열 데이터 반환 |
| `POST` | `/api/v1/simulation/upload_csv` | CSV 파일 업로드 및 SQLite 교체 |

### `POST /api/v1/simulation/results` 요청 바디

```json
{
  "variables": ["Zone Mean Air Temperature [C](Hourly)"],
  "threshold": 1200,
  "xmin": 0.0,
  "xmax": 1.0,
  "csv_start_year": 2025,
  "csv_start_month": 1,
  "csv_start_day": 1,
  "csv_end_year": 2025,
  "csv_end_month": 12,
  "csv_end_day": 31
}
```

> **참고**: `xmin` / `xmax`는 **0.0~1.0 비율**로 전체 데이터셋 내 위치를 나타냅니다.  
> 날짜 파라미터는 X축 레이블 표기에만 사용되며 데이터 슬라이싱에 영향을 주지 않습니다.

---

## Docker / Railway 배포

```bash
docker build -t time-series-analyzer .
docker run -p 8000:8000 time-series-analyzer
```

멀티스테이지 빌드:
1. **Stage 1** — Node.js로 SvelteKit 정적 빌드
2. **Stage 2** — Python slim 이미지에 백엔드 + 빌드 결과물 통합

Railway 배포 시 `PORT` 환경변수를 자동으로 읽습니다.

---

## 변경 이력 (Changelog)

### 2026-04-23
- **[Fix]** X축 시간 눈금(Tick) 렌더링 방식 전면 개편
  - 단순 `value` 방식에서 시계열 전용 `time` 타입으로 변경하여 달력 및 시간 기준(정각) 정렬 완벽 지원.
  - 임의의 시간(예: 09:28)에 줌인하더라도 모든 틱이 00:00, 06:00, 12:00 등 절대 시계 기준으로 고정됨.
  - 마이크로 줌 단계(3일 미만)에서 날짜 텍스트를 무조건 포함하도록 포맷 규칙 개선(`M/D HH:mm`).
- **[UI/UX]** 통합 Hover 툴팁(Glass-morphism) 시스템 적용
  - 브라우저 기본 `title` 툴팁을 제거하고 커스텀 UI 툴팁(삼각형 꼬리 제거, Glass 효과)으로 전역 통일.
  - 드롭다운, 복사/저장 버튼, 캘린더 인풋 등 모든 컴포넌트에 일관된 툴팁 경험 제공.
- **[UI/UX]** UI 컴포넌트 레이아웃 정렬 및 차트 Legend 고정
  - 제어 패널(변수 선택, 달력, 축 제어 등)에 CSS Grid를 적용하여 화면 크기에 무관하게 폭을 고정.
  - ECharts Legend를 항상 2줄 레이아웃으로 고정 표시하도록 강제하여 조작성 향상.
- **[Perf]** 차트 최적화 (Throttle 및 랜더링 성능)
  - ECharts Tooltip Throttle 설정 세부 조정으로 고밀도 차트에서의 스크롤/호버 버벅임 완화.
  - `axisPointer`를 `cross`에서 `line` 타입으로 단순화시켜 연산량 감소.
- **[Feature]** Start/End 날짜 변경 버그 수정 및 Ratio 시스템 고도화
  - `xmin/xmax`를 절대 일수가 아닌 **0.0~1.0 비율**로 다루도록 개선, ECharts dataZoom 시스템과 완벽 동기화.
  - 캘린더 날짜 제어기를 글로벌 데이터 구간 내에서만 선택할 수 있도록 제한 로직 추가.
- **[Fix]** Y축 스파인 렌더링 스타일 수정
  - X축의 디폴트 스파인 색상과 일치하도록 강제 지정된 `gridColor`를 제거, ECharts 텍스트/그리드 테마에 자연스럽게 동화되도록 롤백.
- **[Refactor]** 백엔드 API 라우팅 최적화
  - `router.py` 위치 인자 → 키워드 인자 명시로 안전성 향상.
- **[Fix]** Y축 레이블 편집 인터페이스 제한
  - 차트 전체가 아닌 Y축 이름 텍스트(`axisName`) 구역을 명시적으로 클릭할 때만 인라인 텍스트 편집기가 열리도록 개선.
