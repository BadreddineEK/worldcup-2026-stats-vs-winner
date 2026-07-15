"""
pages/6_Finale_et_Predictions.py — Bracket + prediction de la finale CDM 2026.

Tournoi CDM 2026 (USA/Mexique/Canada) :
  Quarts : 12-13 juillet | Demi-finales : 16-17 juillet | Finale : 19 juillet 2026
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.bracket import build_bracket_figure
from src.clustering import champion_similarity, get_historical_champions
from src.team_analysis import build_ml_dataset, build_team_profiles, radar_data
from src.ui import GREEN, RED, get_data, insight_card, render_sidebar, transparency_banner

st.set_page_config(page_title="Finale & Predictions", page_icon="trophy", layout="wide")

# Auto-refresh toutes les 10 min (les resultats arrivent en continu)
@st.fragment(run_every="10m")
def _auto_refresh():
    from src.ui import clear_cache
    clear_cache()
_auto_refresh()

df_raw, meta = get_data()
render_sidebar(meta)

st.title("La Finale en chiffres")
st.markdown(
    "Le Data Lab suit le tournoi en direct. "
    "**101+ matchs de donnees reelles** — bracket interactif, "
    "profil des finalistes, prediction du champion."
)
transparency_banner(meta, compact=True)

df = pd.read_csv("data/matches_2026.csv")
tp = build_team_profiles(df)

# ─────────────────────────────────────────────────────────────
# BRACKET COMPLET
# ─────────────────────────────────────────────────────────────
st.subheader("Le parcours vers la finale")
fig_bracket = build_bracket_figure(df)
st.plotly_chart(fig_bracket, use_container_width=True)

st.divider()

# ─────────────────────────────────────────────────────────────
# TEAMS EN LICE (semi-finalistes / finalistes)
# ─────────────────────────────────────────────────────────────
knockout_rounds = ["Quarter-finals", "Semi-finals", "Final"]
ko = df[df["round"].isin(knockout_rounds)].copy()

def get_active_teams(df_ko):
    order = ["Quarter-finals", "Semi-finals", "Final"]
    played = [r for r in order if r in df_ko["round"].values]
    if not played:
        return set()
    last_r = played[-1]
    active = set()
    for _, m in df_ko[df_ko["round"] == last_r].iterrows():
        w = m["winner"]
        if w == "home":
            active.add(m["home_team"])
        elif w == "away":
            active.add(m["away_team"])
        else:
            active.add(m["home_team"]); active.add(m["away_team"])
    return active

active_teams = get_active_teams(ko)
if not active_teams:
    qf_done = df[df["round"] == "Quarter-finals"]
    for _, m in qf_done.iterrows():
        w = m["winner"]
        active_teams.add(m["home_team"] if w == "home" else m["away_team"])

if active_teams:
    nb = len(active_teams)
    stage = "finalistes" if nb == 2 else "demi-finalistes" if nb == 4 else "equipes en lice"
    st.success(f"**{stage.capitalize()} :** {' — '.join(sorted(active_teams))}")

# Tableau des profils
r16_winners = set()
for _, m in df[df["round"] == "Round of 16"].iterrows():
    w = m["winner"]
    r16_winners.add(m["home_team"] if w == "home" else m["away_team"])
contenders = active_teams | r16_winners

tp_c = tp[tp["team"].isin(contenders)].sort_values("efficiency_score", ascending=False).head(8)
st.subheader("Profil statistique des equipes encore en lice")

COLS = {
    "team": "Equipe", "matches": "Matchs", "wins": "V",
    "win_rate": "Win %", "avg_possession": "Poss.",
    "avg_shots": "Tirs/m", "avg_conversion_rate": "Conv. %",
    "efficiency_score": "Eff.",
}
st.dataframe(tp_c[list(COLS)].rename(columns=COLS), use_container_width=True, hide_index=True)

st.divider()

# ─────────────────────────────────────────────────────────────
# SIMULATEUR INTERACTIF (st.fragment = ne recharge QUE cette section)
# ─────────────────────────────────────────────────────────────
@st.fragment
def prediction_clash():
    st.subheader("Simulateur de finale — que dit le modele ?")
    st.markdown(
        "Selectionne deux equipes. Le modele predit leur probabilite de victoire "
        "**si leurs stats moyennes du tournoi se reproduisent en finale.**"
    )

    all_teams = sorted(tp["team"].tolist())
    sorted_active = sorted(active_teams)
    default_a = sorted_active[0] if sorted_active else "Spain"
    default_b = sorted_active[1] if len(sorted_active) >= 2 else "England"

    col_a, col_b = st.columns(2)
    with col_a:
        team_a = st.selectbox(
            "Equipe A", all_teams,
            index=all_teams.index(default_a) if default_a in all_teams else 0,
            key="fin_a",
        )
    with col_b:
        team_b = st.selectbox(
            "Equipe B", all_teams,
            index=all_teams.index(default_b) if default_b in all_teams else 1,
            key="fin_b",
        )

    if team_a == team_b:
        st.warning("Choisis deux equipes differentes.")
        return

    ra = tp[tp["team"] == team_a]
    rb = tp[tp["team"] == team_b]
    if ra.empty or rb.empty:
        st.error("Donnees manquantes.")
        return
    ra, rb = ra.iloc[0], rb.iloc[0]

    # Modele
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    @st.cache_data(ttl=3600, show_spinner=False)
    def _get_model(n):
        ml = build_ml_dataset(pd.read_csv("data/matches_2026.csv"))
        F = ["poss_diff", "shots_diff", "sot_diff", "passes_diff", "corners_diff"]
        X = ml[F].values; y = ml["won"].values
        sc = StandardScaler().fit(X)
        lr = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
        lr.fit(sc.transform(X), y)
        return lr, sc, F

    lr, sc, F = _get_model(meta["n_matches"])

    def _pred(r1, r2):
        diffs = np.array([[
            r1["avg_possession"] - r2["avg_possession"],
            r1["avg_shots"] - r2["avg_shots"],
            r1["avg_shots_on_target"] - r2["avg_shots_on_target"],
            r1["avg_passes"] - r2["avg_passes"],
            r1["avg_corners"] - r2["avg_corners"],
        ]])
        return float(lr.predict_proba(sc.transform(diffs))[0][1])

    p_a = _pred(ra, rb); p_b = _pred(rb, ra)
    total = p_a + p_b
    pa = p_a / total if total > 0 else 0.5
    pb = 1 - pa

    c1, c_vs, c2 = st.columns([2, 1, 2])
    with c1:
        st.metric(team_a, f"{pa*100:.1f}%", "P(victoire)")
        st.progress(pa)
    with c_vs:
        st.markdown("### VS")
    with c2:
        st.metric(team_b, f"{pb*100:.1f}%", "P(victoire)")
        st.progress(pb)

    fav = team_a if pa > pb else team_b
    margin = abs(pa - 0.5) * 100
    if margin < 5:
        insight_card(f"<b>Match trop serre</b> pour trancher. Les donnees ne favorisent pas clairement {team_a} ni {team_b}.", "#f39c12")
    else:
        col = GREEN if pa > 0.5 else GREEN
        pct = max(pa, pb) * 100
        insight_card(
            f"<b>Le modele avantage {fav}</b> ({pct:.0f}%) d apres les stats moyennes du tournoi. "
            f"Possession : {ra['avg_possession']:.0f}% vs {rb['avg_possession']:.0f}%. "
            f"Conversion : {ra['avg_conversion_rate']:.0f}% vs {rb['avg_conversion_rate']:.0f}%.",
            col,
        )

    # Radar
    st.subheader("Comparaison radar")
    la, va = radar_data(ra, tp)
    lb, vb = radar_data(rb, tp)
    fig_r = go.Figure()
    for name, vals, color in [(team_a, va, GREEN), (team_b, vb, "#3498db")]:
        vc = vals + [vals[0]]; lc = la + [la[0]]
        fig_r.add_trace(go.Scatterpolar(
            r=vc, theta=lc, fill="toself", name=name,
            line_color=color, fillcolor=color, opacity=0.35,
        ))
    fig_r.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        template="plotly_dark", height=400, margin=dict(t=30, b=10),
    )
    st.plotly_chart(fig_r, use_container_width=True)

    # Champion historique
    st.subheader("Champion prototype — contexte historique")
    hist = get_historical_champions()
    c_h1, c_h2 = st.columns(2)
    for col, team, row in [(c_h1, team_a, ra), (c_h2, team_b, rb)]:
        sims = champion_similarity(row, hist)
        with col:
            st.markdown(f"**{team}** ressemble le plus a :")
            if not sims.empty:
                b = sims.iloc[0]
                st.markdown(f"**{b['champion']} {int(b['year'])}** (sim. {b['similarity']:.0f}%)")
                st.caption(b["note"])
            else:
                st.info("Donnees insuffisantes.")

    st.caption(
        f"Prediction : regression logistique sur {meta['n_matches']} matchs. "
        "A titre analytique — pas un pronostic de pari."
    )

prediction_clash()
