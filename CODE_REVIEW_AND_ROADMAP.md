# UA Decision Console 코드리뷰 & 개발 방향 제안

## 1) 한 줄 요약
현재 코드는 **install cohort 기반 D7 의사결정 콘솔의 MVP로는 충분히 동작**하며, `LLM_CONTEXT_SNAPSHOT.md`의 핵심 철학(결정론적 엔진, cohort 중심 분석)과 대체로 일치합니다. 다만 운영 안정성 관점에서 **데이터 품질 진단, 테스트 자동화, Export/Trend/Payback 기능의 제품화 우선순위 관리**가 필요합니다.

---

## 2) 현 상태 코드리뷰 (강점)

### A. 스냅샷 철학과 구현 정합성 높음
- app 단에서 탭 구조(`Decision View`, `Risk Heatmap`, `LTV Curve`)가 명확하고, cohort 기반 계산 파이프라인이 일관됩니다.
- 결정 엔진이 `base_target × channel multiplier` 기반의 deterministic rule을 유지하고 있어, 스냅샷의 “실무 안전성 우선” 원칙과 일치합니다.

### B. 전처리 방어 코드가 비교적 탄탄함
- installs/events의 time 컬럼 alias 대응(`*_utc`, `*_time`, `*_date`)과 numeric coercion이 잘 되어 있어 실무 raw 데이터 흡수력이 높습니다.
- `ltv_calculator`에서 merge suffix 이슈를 별도 처리해 컬럼 충돌로 깨지는 케이스를 예방합니다.

### C. 시각화 UX의 실무 친화성
- heatmap low-volume mask, lookback 선택, ROAS 중심 색상축(center) 등 실무 회의용 해석성이 좋습니다.
- curve 탭에서 Top-N 자동 추천 + 수동 멀티셀렉트 조합이 “빠른 탐색 + 정밀 검토” 둘 다 가능하게 합니다.

---

## 3) 리스크/개선 포인트 (우선순위 포함)

## P0 (바로 개선 권장)

1. **테스트 부재**
- 핵심 계산 함수(`calculate_d7_ltv`, `compute_daily_d7_metrics`, `compute_ltv_curve`, `run_decision_engine`)에 회귀 테스트가 없습니다.
- 현재는 UI 수동 확인 의존도가 높아, 로직 변경 시 무의식적 오류가 들어가기 쉽습니다.

2. **데이터 품질 진단 미노출**
- 스냅샷에서 강조한 `appsflyer_id match rate`, timezone/결측 경고가 UI에 없습니다.
- 실제 현업에서는 “결과값”만큼 “데이터 신뢰도”가 중요하므로, 진단 패널이 필요합니다.

3. **비어 있는 모듈 존재 (`momentum.py`, `payback.py`, `bayesian.py`)**
- 로드맵 상 기능이지만 현재 empty file 상태입니다.
- 내부/외부 기여자 입장에서 “구현 의도” 파악이 어려워집니다.

## P1 (다음 스프린트)

4. **Export 기능 부재**
- Decision table / Heatmap source / Curve summary를 CSV로 내려받는 기능이 없어 실무 공유성이 제한됩니다.

5. **Trend 해석 레이어 부재**
- 현재는 cohort 단면 중심이고, 스냅샷의 “어제 대비 / MA3”가 미구현입니다.
- 예산 회의에서는 “절대값 + 추세”를 함께 봐야 의사결정 신뢰가 올라갑니다.

## P2 (중기)

6. **도메인 룰 확장성**
- 엔진 rule이 단순하고 투명한 장점이 있으나, 앱/국가/OS별 분기 정책 확장 시 설정 구조(룰 테이블화)가 필요합니다.

---

## 4) 권장 개발 방향 (6주 제안)

## Sprint 1 (주 1-2): 신뢰성 기반 만들기
- [ ] `tests/` 도입 + 핵심 계산 함수 단위테스트 작성
- [ ] 샘플 fixture(csv) 2종(정상/이상치) 추가
- [ ] CI에서 `pytest` 자동 실행
- [ ] App 내 **Data Quality Panel** 추가
  - installs/events row count
  - appsflyer_id match rate
  - invalid timestamp 비율
  - purchase event coverage

**완료 기준**
- 동일 입력 대비 핵심 지표(D7 revenue, D7 ROAS, decision) 회귀 테스트 통과
- 업로드 직후 품질 진단표 1개 이상 노출

## Sprint 2 (주 3-4): 스냅샷 우선순위 기능 구현
- [ ] Export 기능
  - Decision 결과 CSV
  - Daily metric pivot CSV
  - Curve long-format CSV
- [ ] Trend/MA3
  - level별 D7 ROAS trend line
  - MA3/DoD 표시
- [ ] Payback Day v1
  - 누적 revenue >= cost 달성일 계산
  - 미달성 cohort는 `Not reached`

**완료 기준**
- 버튼 클릭으로 3종 CSV 다운로드 가능
- Trend 차트에서 최소 `D7 ROAS + MA3` 제공
- Payback 결과를 decision table 옆 요약으로 표시

## Sprint 3 (주 5-6): 운영성/확장성
- [ ] cost report join(선택 업로드)
- [ ] target/multiplier를 UI 외부 설정파일(.yaml/.json)로 분리
- [ ] rule engine 버전 태깅(`engine_version`) 및 결과 컬럼에 기록

**완료 기준**
- Raw installs cost 부재 시에도 external cost upload로 대체 가능
- 룰 버전이 결과물에 남아, 회의 로그/재현성 확보

---

## 5) 아키텍처 가이드 (앞으로의 유지보수 원칙)

1. **계산 함수는 순수 함수화 유지**
- I/O(Streamlit UI)와 계산 로직을 계속 분리해야 테스트 가능성이 유지됩니다.

2. **UI state는 "입력-파생-출력" 3단 분리**
- 입력(업로드/필터), 파생(집계 df), 출력(차트/테이블)을 명시적으로 나누면 디버깅이 쉬워집니다.

3. **결정 엔진은 설명가능성 우선**
- Bayesian/자동예산은 연구 트랙으로 분리하고, 프로덕션 엔진은 deterministic 규칙을 유지합니다.

---

## 6) 즉시 실행 가능한 TODO (짧은 체크리스트)
- [ ] `tests/test_ltv_calculator.py` 추가
- [ ] `tests/test_decision_engine.py` 추가
- [ ] `app.py`에 Data Quality expander 추가
- [ ] Export 버튼 3개(Decision/Daily/Curve) 추가
- [ ] `momentum.py`, `payback.py`에 최소 함수 시그니처와 docstring 작성

---

## 7) 결론
이 프로젝트는 이미 “보여주기용 대시보드”를 넘어 **실무 의사결정 콘솔의 뼈대**를 갖췄습니다. 다음 단계는 알고리즘 고도화보다, **신뢰성(테스트/진단) + 운영성(Export/추세) + 재현성(룰 버전 관리)**을 먼저 강화하는 것이 가장 높은 ROI를 냅니다.
