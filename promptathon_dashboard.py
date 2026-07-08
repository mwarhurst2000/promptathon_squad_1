"""
People Pulse - Stage 2: dashboard shell.
9 lifecycle tiles + Academy filter. No AI layer yet (that's Stage 3/4).
"""
import pandas as pd
import streamlit as st

from load_data import (
    load_data, headcount_summary, er_case_summary, onboarding_summary,
    performance_summary, bench_summary, engagement_summary,
    pay_review_summary, probation_summary, ftc_summary, team_activity_summary,
)

DATA_PATH = "Global_People_Intelligence_Dummy_Data (1).xlsx"

st.set_page_config(page_title="People Pulse", layout="wide")


@st.cache_data
def get_data():
    return load_data(DATA_PATH)


data = get_data()

# ---------- Header + filter ----------
st.title("People Pulse")
academies = ["All"] + sorted(data["People_Master"]["Academy"].dropna().unique().tolist())
academy = st.selectbox("Academy", academies)

st.divider()

# ---------- Row 1: Headcount / ER / Onboarding ----------
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Headcount")
    hc = headcount_summary(data, academy)
    st.metric("Total", hc["total_headcount"], f"{hc['active']} active")
    st.bar_chart(pd.Series(hc["by_department"], name="Headcount"))

with col2:
    st.subheader("ER Cases")
    er = er_case_summary(data, academy)
    st.metric("Open cases", er["open_cases"])
    if er["avg_days_open_closed"] is not None:
        st.caption(f"Avg resolution: {er['avg_days_open_closed']} days")
    st.bar_chart(pd.Series(er["by_severity"], name="Cases"))

with col3:
    st.subheader("Onboarding")
    onb = onboarding_summary(data, academy)
    st.metric("In progress / total", f"{onb.get('by_status', {}).get('In Progress', 0)} / {onb['total_onboarding']}")
    if onb["avg_induction_feedback"] is not None:
        st.metric("Avg induction feedback", onb["avg_induction_feedback"])
    st.bar_chart(pd.Series(onb["by_status"], name="Count"))

st.divider()

# ---------- Row 2: Performance / Bench / Engagement ----------
col4, col5, col6 = st.columns(3)

with col4:
    st.subheader("Performance Reviews")
    perf = performance_summary(data, academy)
    st.bar_chart(pd.Series(perf["rating_distribution"], name="Reviews"))
    st.caption("By review type: " + ", ".join(f"{k}: {v}" for k, v in perf["by_review_type"].items()))

with col5:
    st.subheader("Bench")
    bench = bench_summary(data, academy)
    st.metric("On bench", bench["on_bench"])
    if bench["avg_days_on_bench"] is not None:
        st.metric("Avg days on bench", bench["avg_days_on_bench"])
    st.bar_chart(pd.Series(bench["by_risk_flag"], name="Count"))

with col6:
    st.subheader("Engagement")
    eng = engagement_summary(data, academy)
    trend = pd.Series(eng["satisfaction_trend_by_wave"], name="Satisfaction")
    st.line_chart(trend)
    st.bar_chart(pd.Series(eng["enps_breakdown"], name="Count"))

st.divider()

# ---------- Row 3: Pay Reviews / Probation / FTC ----------
col7, col8, col9 = st.columns(3)

with col7:
    st.subheader("Pay Reviews")
    pay = pay_review_summary(data, academy)
    if pay["approved_budget_impact_gbp"] is not None:
        st.metric("Approved budget impact", f"£{pay['approved_budget_impact_gbp']:,}")
    st.bar_chart(pd.Series(pay["by_status"], name="Count"))

with col8:
    st.subheader("Probation")
    prob = probation_summary(data, academy)
    if prob["pass_rate_pct"] is not None:
        st.metric("Pass rate", f"{prob['pass_rate_pct']}%")
    st.bar_chart(pd.Series(prob["by_status"], name="Count"))

with col9:
    st.subheader("FTC Tracking")
    ftc = ftc_summary(data, academy)
    if ftc["expiring_within_90_days"] is not None:
        st.metric("Expiring within 90 days", ftc["expiring_within_90_days"])
    st.bar_chart(pd.Series(ftc["by_status"], name="Count"))

st.divider()

# ---------- Row 4: Team activity (full width) ----------
st.subheader("People Team Activity")
team = team_activity_summary(data, academy)
tcol1, tcol2 = st.columns(2)
with tcol1:
    st.metric("Total hours logged", team["total_hours"])
    st.bar_chart(pd.Series(team["by_activity_type"], name="Hours"))
with tcol2:
    st.bar_chart(pd.Series(team["by_team_member"], name="Hours"))

st.caption("AI Insight Panel and NL query box land in Stage 3/4 — this is the data-verified dashboard shell.")