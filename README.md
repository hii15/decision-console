# UA Decision Support Console

A Streamlit-based UA performance analysis and budget decision support tool.

## Features

- D7 LTV & ROAS calculation
- Media Source & Campaign level aggregation
- Channel strategy multiplier (Performance / Hybrid / Branding)
- Deterministic budget decision engine
- Decision visualization table
- MMP Adapter 기반 입력 정규화 (AppsFlyer / Adjust / Singular)

## Project Structure

config/ - Channel & target configuration  
data_processing/ - LTV, cohort, momentum, bayesian logic  
decision/ - Budget decision engine  
visualization/ - Styled decision tables & charts  
app.py - Streamlit main app  

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Multi-MMP Design

AppsFlyer/Adjust/Singular 등 MMP별 export를 어댑터로 표준 스키마로 정규화하여, 분석/의사결정 로직은 MMP에 독립적으로 동작합니다.
