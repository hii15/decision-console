📦 LLM CONTEXT SNAPSHOT

(UA Decision Support Console – 2026 Snapshot)

1. 프로젝트 목적

이 프로젝트는:

MMP raw 데이터 (installs / events 분리 구조)

install cohort 기반 분석

실무 UA 전략 의사결정 보조 도구 제작

포트폴리오 제출용 전략 콘솔

을 목표로 한다.

단순 대시보드가 아닌:

실무 회의에서 예산 증액 / 축소 판단 보조

도구가 목적이다.

2. 데이터 구조
업로드 형태

installs_raw.csv

events_raw.csv

installs 필수 컬럼

appsflyer_id

install_time_utc → install_time

install_date

media_source

campaign

cost (없으면 더미 생성)

events 필수 컬럼

appsflyer_id

event_time_utc → event_time

event_name

af_revenue_usd → revenue

3. 분석 설계 철학

모든 분석은:

install cohort 기준

으로 이루어진다.

즉:

D7 revenue = install 후 7일 이내 누적 revenue

LTV curve = install 이후 누적 수익 커브

Heatmap = install_date × source 기준 D7 ROAS

4. 구현 기능
A. Decision Engine

D7 LTV 계산

D7 ROAS 계산

channel_type multiplier

adjusted_target_roas

Deterministic rule:

if roas >= target: Scale
elif roas >= target * 0.8: Test
else: Reduce
B. Risk Heatmap

Install Cohort 기반

level:

media_source

campaign

media_source_campaign

기간 필터 (14/30/60/All)

low-volume masking

ROAS는 target 중심 diverging color

Finviz 스타일 Red ↔ White ↔ Green

C. LTV Curve

지원:

level 선택 (3가지)

metric:

ltv

roas

revenue

day_points: (0,1,3,7)

Top N 자동 선택

legend:

installs(N)

cost

ROAS:

target line 표시

불확실성 표현:

installs 기반 opacity 감소

5. 현재 설계 수준

이 콘솔은:

Raw MMP 기반 분석 가능

Cohort 분석 구조 완성

실무 전략 판단 지원 가능

단순 대시보드 단계를 넘어선 상태

6. 아직 미구현 영역
1) Export 기능

CSV export

Pivot export

2) Trend 분석

어제 대비

3일 이동평균

3) Payback Day 계산
4) Cost report 업로드 & 조인
5) Data quality diagnostics

appsflyer_id match rate

missing revenue check

timezone 경고

7. 설계 철학 (중요)

Bayesian 통계는 현재 제외

자동 예산 제안은 위험하므로 보류

엔진은 deterministic rule 기반

실무 안전성 > 통계적 과잉모형

8. 다음 작업 우선순위

Export 기능

Trend / MA3

Payback

Cost report join