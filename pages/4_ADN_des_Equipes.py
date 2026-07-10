"""
pages/4_ADN_des_Equipes.py — Le profil statistique de chaque équipe.

Répond à : « Quelles équipes gagnent SANS dominer ? Qui domine SANS gagner ? »
Radar chart + scatter efficiency + narration data-driven par équipe.
"""

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
import pandas as pd

from src.team_analysis import build_team_profiles, radar_data, team_narrative
from src.ui import GREEN, BLUE, get_data, insight_card, render_sidebar, transparency_banner

st.set_page_config(page_title="ADN des Équipes", page_icon="🧬", layout="wide")

df, meta = get_data()
render_sidebar(meta)

st.title("🧬 ADN des équipes")
st.markdown(
    "Chaque équipe a un **style statistique** unique. "
    "Norway gagne à 80% avec seulement 53% de possession. "
    "Spain contrôle le ballon (65%) mais Spain n’est pas invincible. "
    "**Les chiffres révèlent l’ADN de chaque camp mieux qu’un commentateur.**"
)
transparency_banner(meta, compact=True)

if meta["n_matches"] == 0:
    st.info("Pas encore de données. Revenez après les premiers matchs ⚽")
    st.stop()

tp = build_team_profiles(df)

st.divider()

# ─────────────────────────────────────────────────────────────
# SCATTER PRINCIPAL : Possession vs Taux de victoire
# ─────────────────────────────────────────────────────────────
st.subheader("La grande question : possession = victoire ?")
st.markdown(
    "Chaque point = une équipe. La zone verte (haut-droite) = domine **et** gagne. "
    "La zone rouge (bas-droite) = domine **mais** ne gagne pas. "
    "La zone surprenante = **haut-gauche** : gagne *sans* dominer."
)

# Filtre : équipes avec au moins 3 matchs
tp_plot = tp[tp["matches"] >= 3].copy()
tp_plot["label_efficiency"] = tp_plot.apply(
    lambda r: (
        "Dominant & gagnant" if r["avg_possession"] >= 55 and r["win_rate"] >= 60
        else "Pragmatique gagnant" if r["avg_possession"] < 55 and r["win_rate"] >= 60
        else "Dominant frustrant" if r["avg_possession"] >= 55 and r["win_rate"] < 40
        else "En difficulté"
    ),
    axis=1,
)

color_map = {
    "Dominant & gagnant": "#00B140",
    "Pragmatique gagnant": "#3498db",
    "Dominant frustrant": "#e74c3c",
    "En difficulté": "#888",
}

fig = px.scatter(
    tp_plot,
    x="avg_possession",
    y="win_rate",
    size="goals_for",
    color="label_efficiency",
    color_discrete_map=color_map,
    hover_name="team",
    hover_data={
        "matches": True,
        "avg_possession": ":.1f",
        "win_rate": ":.0f",
        "avg_shot_accuracy": ":.1f",
        "avg_conversion_rate": ":.1f",
        "goals_for": True,
        "label_efficiency": False,
    },
    labels={
        "avg_possession": "Possession moyenne (%)",
        "win_rate": "Taux de victoire (%)",
        "goals_for": "Buts marqués (total)",
    },
    text="team",
    template="plotly_dark",
    height=520,
)
fig.update_traces(textposition="top center", textfont_size=10)
fig.add_vline(x=50, line_dash="dot", line_color="#555",
              annotation_text="50% possession", annotation_position="bottom right")
fig.add_hline(y=50, line_dash="dot", line_color="#555",
              annotation_text="50% victoires", annotation_position="right")
fig.update_layout(
    margin=dict(t=30, b=20),
    legend_title_text="Profil",
)
st.plotly_chart(fig, use_container_width=True)

# Insights auto-générés
col1, col2, col3 = st.columns(3)
most_efficient = tp_plot.loc[tp_plot["efficiency_score"].idxmax()]
most_dominant_loser = tp_plot.loc[
    (tp_plot["avg_possession"] >= 55) & (tp_plot.index == (
        tp_plot[tp_plot["avg_possession"] >= 55]["win_rate"].idxmin()
    ))
]
top_converter = tp_plot.loc[tp_plot["avg_conversion_rate"].idxmax()]

col1.metric(
    "Équipe la plus efficace",
    most_efficient["team"],
    f"{most_efficient['win_rate']:.0f}% victoires | {most_efficient['avg_possession']:.0f}% possession",
    help="Ratio victoires/possession le plus élevé."
)
col2.metric(
    "Meilleure conversion",
    top_converter["team"],
    f"{top_converter['avg_conversion_rate']:.0f}% des tirs cadrés = but",
    help="Taux de conversion (buts/tirs cadrés) le plus élevé.",
)
if not most_dominant_loser.empty:
    dom_row = most_dominant_loser.iloc[0]
    col3.metric(
        "Dominant frustrant",
        dom_row["team"],
        f"{dom_row['avg_possession']:.0f}% possession mais {dom_row['win_rate']:.0f}% victoires",
        help="La plus forte possession avec le plus faible taux de victoire.",
    )

st.divider()

# ─────────────────────────────────────────────────────────────
# TABLEAU DES STYLES — Shot accuracy vs Conversion
# ─────────────────────────────────────────────────────────────
st.subheader("Précision vs Efficacité devant le but")
st.markdown(
    "**Précision** = % des tirs qui cadrent. **Conversion** = % des tirs cadrés qui entrent. "
    "Une équipe peut être précise sans être efficace, et vice-versa."
)

acc_conv = tp_plot.dropna(subset=["avg_shot_accuracy", "avg_conversion_rate"]).copy()
fig2 = px.scatter(
    acc_conv,
    x="avg_shot_accuracy",
    y="avg_conversion_rate",
    size="avg_shots",
    color="win_rate",
    color_continuous_scale="RdYlGn",
    range_color=[0, 100],
    hover_name="team",
    hover_data={
        "avg_shots": ":.1f",
        "avg_shot_accuracy": ":.1f",
        "avg_conversion_rate": ":.1f",
        "win_rate": ":.0f",
    },
    labels={
        "avg_shot_accuracy": "Précision des tirs (% cadrés / tentatives)",
        "avg_conversion_rate": "Conversion (% buts / tirs cadrés)",
        "avg_shots": "Tirs / match",
        "win_rate": "Win rate %",
    },
    text="team",
    template="plotly_dark",
    height=480,
)
fig2.update_traces(textposition="top center", textfont_size=9)
med_acc = acc_conv["avg_shot_accuracy"].median()
med_conv = acc_conv["avg_conversion_rate"].median()
fig2.add_vline(x=med_acc, line_dash="dot", line_color="#555",
               annotation_text=f"Médiane précision ({med_acc:.0f}%)")
fig2.add_hline(y=med_conv, line_dash="dot", line_color="#555",
               annotation_text=f"Médiane conversion ({med_conv:.0f}%)")
fig2.update_layout(margin=dict(t=30, b=20), coloraxis_showscale=True)
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ─────────────────────────────────────────────────────────────
# RADAR / SPIDER — ADN d'une équipe
# ─────────────────────────────────────────────────────────────
st.subheader("Radar — l'empreinte statistique d'une équipe")

teams_available = sorted(tp["team"].tolist())
col_sel1, col_sel2 = st.columns(2)
with col_sel1:
    team_a = st.selectbox("Équipe A", teams_available,
                          index=teams_available.index("France") if "France" in teams_available else 0)
with col_sel2:
    team_b = st.selectbox("Équipe B (comparaison optionnelle)",
                          ["—"] + teams_available,
                          index=teams_available.index("Norway") + 1 if "Norway" in teams_available else 0)

def make_radar(team_name: str, color: str, tp_df: pd.DataFrame) -> go.Scatterpolar | None:
    row = tp_df[tp_df["team"] == team_name]
    if row.empty:
        return None
    labels, values = radar_data(row.iloc[0], tp_df)
    values_closed = values + [values[0]]
    labels_closed = labels + [labels[0]]
    return go.Scatterpolar(
        r=values_closed, theta=labels_closed,
        fill="toself", name=team_name,
        line_color=color, fillcolor=color,
        opacity=0.35,
    )

fig3 = go.Figure()
trace_a = make_radar(team_a, "#00B140", tp)
if trace_a:
    fig3.add_trace(trace_a)
if team_b != "—":
    trace_b = make_radar(team_b, "#3498db", tp)
    if trace_b:
        fig3.add_trace(trace_b)

fig3.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickfont_size=9)),
    template="plotly_dark",
    height=500,
    margin=dict(t=40, b=40),
    showlegend=True,
)
st.plotly_chart(fig3, use_container_width=True)

# Métriques clés sous le radar
def show_team_kpis(name: str, tp_df: pd.DataFrame) -> None:
    row = tp_df[tp_df["team"] == name]
    if row.empty:
        return
    r = row.iloc[0]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Victoires", f"{r['wins']:.0f}/{r['matches']:.0f}", f"{r['win_rate']:.0f}%")
    c2.metric("Buts / match", f"{r['goals_per_match']:.1f}")
    c3.metric("Possession moy.", f"{r['avg_possession']:.0f}%")
    c4.metric("Conversion", f"{r['avg_conversion_rate']:.0f}%" if pd.notna(r['avg_conversion_rate']) else "—")
    c5.metric("Tirs / match", f"{r['avg_shots']:.1f}")

col_ka, col_kb = st.columns(2)
with col_ka:
    st.markdown(f"**{team_a}**")
    show_team_kpis(team_a, tp)
if team_b != "—":
    with col_kb:
        st.markdown(f"**{team_b}**")
        show_team_kpis(team_b, tp)

st.divider()

# ─────────────────────────────────────────────────────────────
# NARRATION PAR ÉQUIPE
# ─────────────────────────────────────────────────────────────
st.subheader("Ce que disent les données de cette équipe")

selected_team = st.selectbox(
    "Choisir une équipe",
    sorted(tp["team"].tolist()),
    key="narrative_selector",
    index=sorted(tp["team"].tolist()).index(team_a) if team_a in tp["team"].tolist() else 0,
)
row_n = tp[tp["team"] == selected_team].iloc[0]
st.markdown(team_narrative(row_n, tp))

st.divider()

# ─────────────────────────────────────────────────────────────
# CLASSEMENT COMPLET
# ─────────────────────────────────────────────────────────────
with st.expander("Voir le classement complet des 48 équipes"):
    show_cols = {
        "team": "Équipe",
        "matches": "Matchs",
        "wins": "V",
        "draws": "N",
        "losses": "D",
        "goals_for": "Buts +",
        "goals_against": "Buts -",
        "win_rate": "Win % ",
        "avg_possession": "Poss. moy.",
        "avg_shots": "Tirs/m",
        "avg_shot_accuracy": "Précision %",
        "avg_conversion_rate": "Conv. %",
        "efficiency_score": "Eff. score",
    }
    display = tp[list(show_cols.keys())].rename(columns=show_cols)
    st.dataframe(display, use_container_width=True, hide_index=True)

st.caption(
    f"Basé sur {meta['n_matches']} matchs joués au {meta['last_updated_str']}. "
    "Source : The Stats Zone (pages publiques FIFA World Cup 2026)."
)
