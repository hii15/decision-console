def _fmt_float(x, digits=2):
    try:
        return f"{float(x):,.{digits}f}"
    except Exception:
        return x


def style_decision_table(df):
    display_df = df.copy()

    # ROAS는 배수 형태로 보여주는 게 실무에서 더 자연스럽다
    for col in ["d7_roas", "adjusted_target_roas", "roas_gap"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda v: _fmt_float(v, 3))

    for col in ["d7_ltv", "d7_revenue", "cost"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda v: _fmt_float(v, 2))

    def highlight(val):
        if val == "Scale":
            return "background-color: #1f8b4c; color: white;"
        if val == "Test":
            return "background-color: #f0ad4e; color: black;"
        if val == "Reduce":
            return "background-color: #d9534f; color: white;"
        return ""

    return display_df.style.map(highlight, subset=["decision"])