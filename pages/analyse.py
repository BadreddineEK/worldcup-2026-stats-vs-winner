"""
pages/analyse.py — Ce que les stats revelent.
Stats vs resultats, Top 5 upsets visuels, facteur chance.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analysis import agreement_summary, annotate_matches, find_surprises, stat_agreement_by_type
from src.i18n import t
from src.ui import GREEN, RED, get_data, insight_card, render_sidebar, transparency_banner
from src.xg import team_xg_summary

st.set_page_config(page_title="Stats", page_icon=":material/analytics:", layout="wide")
df_raw, meta = get_data()
lang = st.session_state.get("lang", "fr")
render_sidebar(meta)

st.title(t("analyse_title", lang))
st.markdown(t("analyse_intro", lang))
transparency_banner(meta, compact=True)

df = pd.read_csv("data/matches_2026.csv")
summary = agreement_summary(df_raw)
pct = summary["pct_dominant_won"]

st.divider()

# ── LE CHIFFRE CLE ───────────────────────────────────────────────────────────
col_gauge, col_text = st.columns([1, 2])
with col_gauge:
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct or 0,
        number={"suffix": "%", "font": {"size": 42}},
        title={"text": t("analyse_dom_pct", lang), "font": {"size": 13}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#00B140" if (pct or 0) >= 60 else "#f39c12"},
            "steps": [{"range": [0, 50], "color": "#f1f5f9"}, {"range": [50, 100], "color": "#e8f5e9"}],
            "threshold": {"line": {"color": "#64748b", "width": 2}, "value": 50},
        },
    ))
    fig_g.update_layout(height=220, margin=dict(t=30, b=0, l=20, r=20),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_g, width="stretch")
with col_text:
    st.markdown(f"### {pct}% des matchs — et ce n\'est pas la stat la plus intéressante" if lang == "fr"
                else f"### {pct}% of matches — and this isn\'t the most interesting stat")
    st.markdown(
        t("analyse_on_N", lang).format(summary["n_evaluables"])
        + f" · **{summary['n_surprises']}** " + ("surprises" if lang == "fr" else "upsets")
    )
    # Par stat
    by_type = stat_agreement_by_type(df_raw)
    if not by_type.empty:
        st.caption("**Quelle stat prédit le mieux ?**" if lang == "fr" else "**Which stat predicts best?**")
        for _, row in by_type.iterrows():
            pct_stat = row["Taux (%)"]
            bar = "█" * int(pct_stat / 10) + "░" * (10 - int(pct_stat / 10))
            st.text(f"{row['Statistique']:20} {bar} {pct_stat:.0f}%")

st.divider()

# ── TOP 5 UPSETS ─────────────────────────────────────────────────────────────
st.subheader(t("analyse_surprises", lang))
st.caption(t("analyse_upsets_intro", lang))

annotated = annotate_matches(df_raw)
surprises = find_surprises(annotated).copy()
if not surprises.empty:
    surprises["poss_diff"] = (surprises["home_possession"] - surprises["away_possession"]).abs()
    top5 = surprises.nlargest(min(5, len(surprises)), "poss_diff")
    for _, row in top5.iterrows():
        dom  = row["home_team"] if row["dominant_side"] == "home" else row["away_team"]
        win  = row["home_team"] if row["winner"] == "home" else row["away_team"]
        score = f"{int(row['home_goals'])}–{int(row['away_goals'])}"
        rnd   = row["round"]
        diff  = row["poss_diff"]
        with st.container(border=True):
            ca, cb, cc = st.columns([3, 2, 2])
            with ca:
                st.markdown(f"**{row['home_team']}** {score} **{row['away_team']}**")
                st.caption(rnd)
            with cb:
                adv_label = t("analyse_dominated", lang)
                st.metric(adv_label, dom, f"+{diff:.0f}% " + t("analyse_poss_adv", lang))
            with cc:
                win_label = t("analyse_winner", lang)
                st.metric(win_label, win, "🔄")

st.divider()

# ── TAUX PAR PHASE ────────────────────────────────────────────────────────────
st.subheader(t("analyse_by_phase", lang))
st.caption(t("analyse_phase_intro", lang))
if "round" in df_raw.columns and "dominant_won" in df_raw.columns:
    _ord = {"Group": 0, "Round of 32": 1, "Round of 16": 2, "Quarter": 3, "Semi": 4, "Final": 5}
    rs = (df_raw[df_raw["dominant_won"].notna()]
          .groupby("round")
          .agg(N=("dominant_won","count"), Won=("dominant_won", lambda x: (x==True).sum()))
          .reset_index())
    rs["pct"] = (rs["Won"] / rs["N"] * 100).round(1)
    rs["_s"]  = rs["round"].apply(lambda r: next((v for k,v in _ord.items() if k.lower() in r.lower()), 9))
    rs = rs.sort_values("_s")
    fig_r = go.Figure(go.Bar(
        x=rs["round"], y=rs["pct"],
        text=[f"{v:.0f}%" for v in rs["pct"]],
        textposition="outside",
        marker_color=["#00B140" if v >= 60 else "#f59e0b" if v >= 50 else "#ef4444" for v in rs["pct"]],
        customdata=rs[["N"]].values,
        hovertemplate="%{x}<br>%{y:.1f}% (%{customdata[0]} matchs)<extra></extra>",
    ))
    fig_r.add_hline(y=50, line_dash="dot", line_color="#94a3b8")
    fig_r.update_layout(yaxis_range=[0, 100], template="simple_white", height=320,
                        margin=dict(t=20, b=10), yaxis_title=t("analyse_dom_pct", lang) + " (%)")
    st.plotly_chart(fig_r, width="stretch")

st.divider()

# ── FACTEUR CHANCE ────────────────────────────────────────────────────────────
st.subheader(t("analyse_xg_title", lang))
st.caption(t("analyse_xg_intro", lang))

xg_sum = team_xg_summary(df)
if not xg_sum.empty:
    plot_df = xg_sum[xg_sum["matches"] >= 3].copy()
    fig_xg = go.Figure()
    fig_xg.add_shape(type="line", x0=0, y0=0, x1=plot_df["xg_total"].max()+2,
                     y1=plot_df["xg_total"].max()+2, line=dict(color="#94a3b8", dash="dot"))
    for _, r in plot_df.iterrows():
        color = "#00B140" if r["overperf_total"] > 0.5 else "#ef4444" if r["overperf_total"] < -0.5 else "#64748b"
        fig_xg.add_trace(go.Scatter(
            x=[r["xg_total"]], y=[r["goals_total"]],
            mode="markers+text",
            text=[r["team"][:7]], textposition="top center",
            textfont=dict(size=8, color=color),
            marker=dict(size=10, color=color, opacity=0.8),
            hovertemplate=f"<b>{r['team']}</b><br>Buts: {r['goals_total']}<br>Attendus: {r['xg_total']:.1f}<br>Surperf: {r['overperf_total']:+.1f}<extra></extra>",
            showlegend=False,
        ))
    fig_xg.update_layout(
        xaxis_title="Buts attendus (proxy)" if lang == "fr" else "Expected goals (proxy)",
        yaxis_title="Buts réels" if lang == "fr" else "Actual goals",
        template="simple_white", height=400, margin=dict(t=20, b=10),
    )
    st.plotly_chart(fig_xg, width="stretch")
    # Top lucky / unlucky
    c1, c2 = st.columns(2)
    with c1:
        lucky = xg_sum.nlargest(3, "overperf_total")[["team","goals_total","xg_total","overperf_total"]]
        lucky.columns = (["Équipe","Buts","Attendus","Surperf."] if lang == "fr"
                         else ["Team","Goals","Expected","Over-perf."])
        st.caption("🍀 **Les plus chanceux**" if lang == "fr" else "🍀 **Luckiest teams**")
        st.dataframe(lucky, use_container_width=True, hide_index=True)
    with c2:
        unlucky = xg_sum.nsmallest(3, "overperf_total")[["team","goals_total","xg_total","overperf_total"]]
        unlucky.columns = (["Équipe","Buts","Attendus","Surperf."] if lang == "fr"
                           else ["Team","Goals","Expected","Over-perf."])
        st.caption("😬 **Les plus malchanceux**" if lang == "fr" else "😬 **Unluckiest teams**")
        st.dataframe(unlucky, use_container_width=True, hide_index=True)

st.caption(f"{t('data_at', lang)} {meta['last_updated_str']} · {t('source_label', lang)} : The Stats Zone")
