# config/channel_config.py

"""
Channel Type Default Mapping

- media_source → channel_type
- 기본 전략 분류 정의
- UI에서 수정 가능하도록 app.py에서 확장됨
"""

DEFAULT_CHANNEL_MAP = {
    # ===== Performance Channels =====
    "Google UAC": "Performance",
    "Meta Ads": "Performance",
    "Apple Search Ads": "Performance",

    # ===== Hybrid Channels =====
    "Kakao Bizboard": "Hybrid",
    "Naver GFA": "Hybrid",

    # ===== Branding Channels =====
    "Naver Webtoon BB": "Branding",
    "YouTube Masthead": "Branding",
}