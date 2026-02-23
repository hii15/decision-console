# config/target_config.py

"""
Target Configuration

- Base Target은 app.py에서 입력 받음
- 여기서는 Channel Type별 Multiplier 기본값 정의
- 전략 가중치 기본 세팅
"""

# ===== Channel Type Multiplier Defaults =====
DEFAULT_MULTIPLIER = {
    "Performance": 1.0,   # 엄격 평가
    "Hybrid": 0.85,       # 일부 완화
    "Branding": 0.65      # 전략적 완화
}

# ===== Probability Threshold Defaults =====
# (향후 UI에서 조정 가능하도록 확장 가능)

DEFAULT_PROBABILITY_THRESHOLDS = {
    "scale": 0.75,
    "test": 0.50,
    "reduce": 0.40
}

# ===== Payback Threshold Defaults =====
DEFAULT_PAYBACK_THRESHOLDS = {
    "scale": 10,     # 10일 이내
    "test": 14,      # 14일 이내
    "reduce": 20     # 20일 초과 시 리스크
}