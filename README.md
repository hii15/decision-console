# UA Decision Support Console

A Streamlit-based UA performance analysis and budget decision support tool.

## Features

- D7 LTV & ROAS calculation
- Media Source & Campaign level aggregation
- Channel strategy multiplier (Performance / Hybrid / Branding)
- Deterministic budget decision engine
- Decision visualization table

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