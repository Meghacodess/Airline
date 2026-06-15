"""
Loyalty Retention Command Center — Streamlit prototype
Run:  pip install streamlit pandas plotly  →  streamlit run app.py
Expects scored_members.csv (produced by Airline_Loyalty_Churn_Colab.ipynb) in the same folder.
"""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Loyalty Retention Command Center", page_icon="✈️", layout="wide")

@st.cache_data
def load():
    return pd.read_csv("scored_members.csv")

df = load()

PLAYS = {
    "Core Frequent Flyers": "Maintain. No retention spend — quarterly statement only.",
    "Cooling Veterans": "“We've missed you” + tier-protection notice within 30 days of the 2-month silence mark.",
    "New Climbers": "First-redemption onboarding journey: waive redemption minimum once in first 90 days.",
    "Sleeping Enrollees": "One points-expiry win-back, then suppress from paid campaigns.",
    "Phantom Redeemers (anomaly)": "Route to finance/IT audit — points redeemed with zero recorded flights.",
}
def action(row):
    if row["segment"] == "Phantom Redeemers (anomaly)": return "Audit (finance/IT)"
    if row["priority"] == "P1": return "Loyalty-desk call + redemption-unlock offer (7 days)"
    if row["priority"] == "P2":
        return "Points-expiry win-back email" if row["segment"] == "Sleeping Enrollees" else "Day-60 inactivity email + redemption nudge"
    return "None — quarterly statement"

st.title("✈️ Loyalty Retention Command Center")
st.caption("Scored as of December 2018 · out-of-time validated gradient-boosting churn model "
           "(top-decile lift 5.5×) · risk = probability of zero flights or cancellation in the next 6 months")

hi = df["churn_risk"] > 0.6
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Active members scored", f"{len(df):,}")
c2.metric("High risk (>60%)", f"{hi.sum():,}")
c3.metric("CLV in high-risk band", f"${df.loc[hi,'clv'].sum():,.0f}")
c4.metric("P1 — contact this week", f"{(df.priority=='P1').sum():,}")
c5.metric("P2 — automated campaign", f"{(df.priority=='P2').sum():,}")

st.info("**How to use:** filter below; the table is your call list, riskiest members first. "
        "P1 = act this week, P2 = automated campaign, P3 = no retention spend. Download to hand to operations.")

st.subheader("Segments")
seg = df.groupby("segment").agg(members=("member","size"), avg_risk=("churn_risk","mean"),
                                avg_clv=("clv","mean"), avg_months_silent=("recency","mean")).round(2)
seg["play"] = seg.index.map(PLAYS)
st.dataframe(seg, use_container_width=True)

st.subheader("Action list")
f1, f2, f3, f4 = st.columns([1,1,1,2])
pri = f1.multiselect("Priority", ["P1","P2","P3"], default=["P1","P2"])
sgs = f2.multiselect("Segment", sorted(df.segment.unique()))
prv = f3.multiselect("Province", sorted(df.Province.unique()))
q = f4.text_input("Search member #")

v = df[df.priority.isin(pri)] if pri else df
if sgs: v = v[v.segment.isin(sgs)]
if prv: v = v[v.Province.isin(prv)]
if q: v = v[v.member.astype(str).str.contains(q)]
v = v.sort_values("churn_risk", ascending=False).copy()
v["recommended_action"] = v.apply(action, axis=1)
v["churn_risk"] = (v["churn_risk"]*100).round(0).astype(int).astype(str) + "%"

show = ["member","segment","priority","churn_risk","clv","fwd_value","recency","flights_6m","Loyalty Card","Province","recommended_action"]
st.write(f"**{len(v):,} members match**")
st.dataframe(v[show].head(500), use_container_width=True, hide_index=True)
st.download_button("⬇ Export call list (CSV)", v[show].to_csv(index=False), "retention_call_list.csv", "text/csv")
