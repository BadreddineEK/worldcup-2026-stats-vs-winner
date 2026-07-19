"""
pages/7_xG_et_Chance.py — Expected Goals et facteur chance.

Question : les equipes qui ont marque ont-elles vraiment MERITE leurs buts ?
Buts attendus (proxy) = shots_on_target x taux_conversion_tournoi.
Sur-performance = "facteur chance". Sous-performance = "manque de realisme".
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.ui import GREEN, RED, get_data, insight_card, render_sidebar, transparency_banner
from src.xg import compute_match_xg, team_xg_summary, xg_label

st.set_page_config(page_title="Facteur chance", page_icon="chart_with_upwards_trend", layout="wide")

df_raw, meta = get_data()
render_sidebar(meta)

st.title("Facteur chance & buts attendus")
st.markdown(
    "Pour chaque match, combien de buts une equipe **meritait-elle** de marquer "
    "selon ses tirs cadres ? La difference avec les buts reels = le **facteur chance**.\n\n"
    "> **Note methode :** l indicateur utilise ici est un *proxy simplifie* : "
    "`tirs_cadres x taux_de_conversion_moyen_du_tournoi`. "
    "Ce n est **pas** le vrai xG (qui necessite les coordonnees de chaque tir "
    "et un modele de regression sur des millions de tirs). "
    "C est un indicateur reproductible, documente et suffisant pour comparer les equipes entre elles."
)
transparency_banner(meta, compact=True)

df = pd.read_csv("data/matches_2026.csv")
summary = team_xg_summary(df)

if summary.empty:
    st.info("Pas assez de donnees pour calculer les buts attendus.")
    st.stop()

st.divider()

# ─────────────────────────────────────────────────────────────
# CHIFFRES CLES
# ─────────────────────────────────────────────────────────────
total_goals = df["home_goals"].sum() + df["away_goals"].sum()
total_sot = df["home_shots_on_target"].sum() + df["away_shots_on_target"].sum()
base_rate = total_goals / total_sot if total_sot > 0 else 0.3

c1, c2, c3 = st.columns(3)
c1.metric("Buts marques (total)", int(total_goals))
c2.metric("Taux de conversion moyen", f"{base_rate*100:.1f}%",
          help="Buts / tirs cadres sur l ensemble du tournoi")
c3.metric("Val. 1 tir cadre", f"{base_rate:.2f}",
          help="Valeur d un tir cadre moyen dans ce tournoi")

insight_card(
    f"La <b>base de calcul</b> dans ce tournoi : chaque tir cadre vaut "
    f"<b>{base_rate*100:.1f}%</b> de but en moyenne. "
    f"Un tir non cadre n apporte que {base_rate*100*0.08:.1f}%. "
    f"Ce taux sera compare aux performances reelles de chaque equipe.",
    "#3498db",
)

st.divider()

# ─────────────────────────────────────────────────────────────
# SCATTER : buts reels vs xG
# ─────────────────────────────────────────────────────────────
st.subheader("Buts reels vs Expected Goals — qui a ete chanceux ?")
st.markdown(
    "Au-dessus de la diagonale = **sur-performance** (plus de buts que prevu). "
    "En dessous = **sous-performance** (moins de buts que prevu)."
)

plot_df = summary[summary["matches"] >= 3].copy()
plot_df["label"] = plot_df["overperf_total"].apply(xg_label)

fig = px.scatter(
    plot_df,
    x="xg_total",
    y="goals_total",
    text="team",
    size="matches",
    color="overperf_total",
    color_continuous_scale="RdYlGn",
    color_continuous_midpoint=0,
    hover_data={
        "team": True,
        "matches": True,
        "goals_total": True,
        "xg_total": ":.1f",
        "overperf_total": ":.1f",
        "pct_vs_expected": True,
    },
    labels={
        "xg_total": "Buts attendus (proxy)",
        "goals_total": "Buts reels (total)",
        "overperf_total": "Surperf. (buts - xG)",
    },
    template="simple_white",
)

# Diagonale de reference
max_val = max(plot_df["xg_total"].max(), plot_df["goals_total"].max()) + 1
fig.add_trace(go.Scatter(
    x=[0, max_val], y=[0, max_val],
    mode="lines",
    line=dict(color="#888", dash="dash", width=1),
    name="Proxy = buts reels",
    showlegend=True,
))
fig.update_traces(textposition="top center", textfont_size=9, selector=dict(mode="markers+text"))
fig.update_layout(height=500, margin=dict(t=30, b=10), coloraxis_showscale=True)
st.plotly_chart(fig, width="stretch")

# ─────────────────────────────────────────────────────────────
# CLASSEMENT PAR SURPERFORMANCE
# ─────────────────────────────────────────────────────────────
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("Les plus chanceux")
    lucky = summary.nlargest(5, "overperf_total")[
        ["team", "goals_total", "xg_total", "overperf_total", "pct_vs_expected"]
    ].rename(columns={
        "team": "Equipe",
        "goals_total": "Buts reels",
        "xg_total": "xG",
        "overperf_total": "Surperf.",
        "pct_vs_expected": "% vs attendu",
    })
    st.dataframe(lucky, use_container_width=True, hide_index=True)
    top = lucky.iloc[0]
    insight_card(
        f"<b>{top['Equipe']}</b> a marque <b>{top['Surperf.']:+.1f}</b> buts de plus "
        f"que ses buts attendus (proxy) ({top['% vs attendu']:.0f}% de l attendu). "
        "Realisme exceptionnel ou facteur chance ?",
        GREEN,
    )

with col2:
    st.subheader("Les plus malchanceux")
    unlucky = summary.nsmallest(5, "overperf_total")[
        ["team", "goals_total", "xg_total", "overperf_total", "pct_vs_expected"]
    ].rename(columns={
        "team": "Equipe",
        "goals_total": "Buts reels",
        "xg_total": "xG",
        "overperf_total": "Surperf.",
        "pct_vs_expected": "% vs attendu",
    })
    st.dataframe(unlucky, use_container_width=True, hide_index=True)
    bot = unlucky.iloc[0]
    insight_card(
        f"<b>{bot['Equipe']}</b> a marque <b>{bot['Surperf.']:.1f}</b> buts de moins "
        f"que ses buts attendus (proxy). En finale, elle aurait pu aller beaucoup plus loin.",
        RED,
    )

st.divider()

# ─────────────────────────────────────────────────────────────
# EVOLUTION PAR PHASE : surperformance
# ─────────────────────────────────────────────────────────────
st.subheader("Surperformance par phase")
st.markdown("La chance est-elle uniforme au fil du tournoi, ou se concentre-t-elle en phase de groupes ?")

raw = compute_match_xg(df)
_order = {"Group": 0, "Round of 32": 1, "Round of 16": 2, "Quarter-finals": 3, "Semi-finals": 4}
raw["phase_sort"] = raw["round"].apply(
    lambda r: next((v for k, v in _order.items() if k.lower() in r.lower()), 9)
)
phase_stats = (
    raw.groupby("round")
    .agg(avg_overperf=("overperformance", "mean"), n=("goals", "count"))
    .reset_index()
)
phase_stats["phase_sort"] = phase_stats["round"].apply(
    lambda r: next((v for k, v in _order.items() if k.lower() in r.lower()), 9)
)
phase_stats = phase_stats.sort_values("phase_sort")

fig2 = go.Figure(go.Bar(
    x=phase_stats["round"],
    y=phase_stats["avg_overperf"],
    text=[f"{v:+.2f}" for v in phase_stats["avg_overperf"]],
    textposition="outside",
    marker_color=["#00B140" if v > 0 else "#e74c3c" for v in phase_stats["avg_overperf"]],
    customdata=phase_stats[["n"]].values,
    hovertemplate="%{x}<br>Surperf. moy. : %{y:.2f}<br>Observations : %{customdata[0]}<extra></extra>",
))
fig2.add_hline(y=0, line_color="#888", line_dash="dot")
fig2.update_layout(
    template="simple_white", height=350,
    yaxis_title="Surperf. moyenne (buts reels - buts attendus)",
    margin=dict(t=30, b=10),
)
st.plotly_chart(fig2, width="stretch")

st.divider()

# ─────────────────────────────────────────────────────────────
# FOCUS : equipe selectionnee
# ─────────────────────────────────────────────────────────────
st.subheader("Focus equipe")
all_teams_xg = sorted(summary["team"].tolist())
selected = st.selectbox("Choisir une equipe", all_teams_xg, key="xg_team_sel")
row_s = summary[summary["team"] == selected].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Buts reels", int(row_s["goals_total"]))
c2.metric("Expected Goals", f"{row_s['xg_total']:.1f}")
c3.metric("Surperformance", f"{row_s['overperf_total']:+.1f}")
c4.metric("% vs attendu", f"{row_s['pct_vs_expected']:.0f}%")
st.markdown(f"**Verdict :** {xg_label(row_s['overperf_total'])} — {row_s['team']}")

# Match par match
team_matches = raw[raw["team"] == selected].sort_values("date")
if not team_matches.empty:
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=team_matches["round"] + " " + team_matches["date"],
        y=team_matches["overperformance"],
        marker_color=["#00B140" if v > 0 else "#e74c3c" for v in team_matches["overperformance"]],
        text=[f"{v:+.1f}" for v in team_matches["overperformance"]],
        textposition="outside",
        name="Surperf. / match",
    ))
    fig3.add_hline(y=0, line_color="#888", line_dash="dot")
    fig3.update_layout(
        template="simple_white", height=320,
        yaxis_title="Surperf. (buts reels - buts attendus)",
        margin=dict(t=20, b=10),
    )
    st.plotly_chart(fig3, width="stretch")

st.caption(
    "xG proxy = shots_on_target x taux_conversion_tournoi + shots_off_target x 0.08 x taux. "
    "Methode documentee, reproductible, sans boite noire. "
    f"Calcule sur {meta['n_matches']} matchs au {meta['last_updated_str']}."
)
