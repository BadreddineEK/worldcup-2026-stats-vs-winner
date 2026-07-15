"""
pages/6_Finale_et_Predictions.py

Bracket interactif + prediction de la finale CDM 2026.
Modes : Reel | Simule (stats) | Historique (2022 / 2018 / 2014).
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.bracket import (
    build_bracket_figure,
    compute_simulated_winners,
)
from src.clustering import champion_similarity, get_historical_champions
from src.team_analysis import build_ml_dataset, build_team_profiles, radar_data
from src.ui import GREEN, RED, get_data, insight_card, render_sidebar, transparency_banner

st.set_page_config(page_title="Finale & Predictions", page_icon="trophy", layout="wide")

# get_data est mis en cache (TTL 20 min) : pas de rechargement inutile
# L auto-refresh est gere par le TTL, pas par un fragment agressif
df_raw, meta = get_data()
render_sidebar(meta)

st.title("La Finale en chiffres")
st.markdown(
    "Bracket interactif — parcours reel, parcours simule selon les stats, "
    "et prediction du champion pour la finale du **19 juillet 2026**."
)
transparency_banner(meta, compact=True)

df = pd.read_csv("data/matches_2026.csv")
tp = build_team_profiles(df)

# ─────────────────────────────────────────────────────────────
# ONGLETS : 2026 Reel | Simule
# ─────────────────────────────────────────────────────────────
tab_live, tab_sim = st.tabs([
    "Parcours reel",
    "Et si les stats decidaient ?",
])

with tab_live:
    st.caption("Vainqueurs reels, matchs termines en vert. TBD = a venir.")
    fig_real = build_bracket_figure(df, year=2026)
    st.plotly_chart(fig_real, use_container_width=True)

with tab_sim:
    st.markdown(
        "**Et si les stats avaient toujours decide ?** "
        "Pour chaque match, l equipe qui domine la majorite des stats "
        "(possession, tirs, tirs cadres) est dessinee en **orange** quand elle "
        "a perdu en realite. Vert = reel = simule identiques."
    )
    sim = compute_simulated_winners(df)
    surprises_ko = {
        fid: dom for fid, dom in sim.items()
        if fid > 191900  # uniquement phases eliminatoires
        and fid in df.set_index("fixture_id").index
        and dom != df.set_index("fixture_id").loc[fid, "winner"]
    }
    if surprises_ko:
        insight_card(
            f"<b>{len(surprises_ko)} match(s) surprises</b> en phase eliminatoire : "
            "le dominant statistique n a pas gagne. "
            "Orange dans le bracket = le simulé aurait franchi ce tour.",
            "#f39c12",
        )
    fig_sim = build_bracket_figure(df, year=2026, simulated_winners=sim)
    st.plotly_chart(fig_sim, use_container_width=True)

st.divider()

# ─────────────────────────────────────────────────────────────
# EQUIPES EN LICE
# ─────────────────────────────────────────────────────────────
knockout_rounds = ["Quarter-finals", "Semi-finals", "Final"]
ko = df[df["round"].isin(knockout_rounds)].copy()

def get_active(df_ko):
    order = ["Quarter-finals", "Semi-finals", "Final"]
    played = [r for r in order if r in df_ko["round"].values]
    if not played:
        return set()
    active = set()
    for _, m in df_ko[df_ko["round"] == played[-1]].iterrows():
        w = m["winner"]
        if w == "home":
            active.add(m["home_team"])
        elif w == "away":
            active.add(m["away_team"])
        else:
            active.add(m["home_team"]); active.add(m["away_team"])
    return active

active_teams = get_active(ko)
if not active_teams:
    for _, m in df[df["round"] == "Quarter-finals"].iterrows():
        active_teams.add(m["home_team"] if m["winner"] == "home" else m["away_team"])

if active_teams:
    nb = len(active_teams)
    stage = "finalistes" if nb == 2 else "demi-finalistes" if nb == 4 else "equipes en lice"
    st.success(f"**{stage.capitalize()} :** {chr(32).join([chr(8212).join(sorted(active_teams))])}")

# ─────────────────────────────────────────────────────────────
# SIMULATEUR (st.fragment = seul ce bloc se recharge au changement d equipe)
# ─────────────────────────────────────────────────────────────
@st.fragment
def prediction_clash():
    st.subheader("Simulateur de finale")
    st.markdown(
        "Selectionne deux equipes. Le modele de regression logistique "
        "entraine sur les matchs du tournoi calcule leur probabilite de victoire."
    )

    all_teams = sorted(tp["team"].tolist())
    sa = sorted(active_teams)
    def_a = sa[0] if sa else "Spain"
    def_b = sa[1] if len(sa) >= 2 else "England"

    c_sel1, c_sel2 = st.columns(2)
    with c_sel1:
        team_a = st.selectbox("Equipe A", all_teams,
                              index=all_teams.index(def_a) if def_a in all_teams else 0,
                              key="fin_a")
    with c_sel2:
        team_b = st.selectbox("Equipe B", all_teams,
                              index=all_teams.index(def_b) if def_b in all_teams else 1,
                              key="fin_b")

    if team_a == team_b:
        st.warning("Choisis deux equipes differentes.")
        return

    ra = tp[tp["team"] == team_a]
    rb = tp[tp["team"] == team_b]
    if ra.empty or rb.empty:
        return
    ra, rb = ra.iloc[0], rb.iloc[0]

    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    @st.cache_data(ttl=3600, show_spinner=False)
    def _model(n):
        ml = build_ml_dataset(pd.read_csv("data/matches_2026.csv"))
        F = ["poss_diff", "shots_diff", "sot_diff", "passes_diff", "corners_diff"]
        X = ml[F].values; y = ml["won"].values
        sc = StandardScaler().fit(X)
        lr = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
        lr.fit(sc.transform(X), y)
        return lr, sc, F

    lr, sc, _ = _model(meta["n_matches"])

    def _pred(r1, r2):
        d = np.array([[r1["avg_possession"]-r2["avg_possession"],
                       r1["avg_shots"]-r2["avg_shots"],
                       r1["avg_shots_on_target"]-r2["avg_shots_on_target"],
                       r1["avg_passes"]-r2["avg_passes"],
                       r1["avg_corners"]-r2["avg_corners"]]])
        return float(lr.predict_proba(sc.transform(d))[0][1])

    pa_raw = _pred(ra, rb); pb_raw = _pred(rb, ra)
    tot = pa_raw + pb_raw
    pa = pa_raw / tot if tot > 0 else 0.5
    pb = 1 - pa

    c1, cv, c2 = st.columns([2, 1, 2])
    with c1:
        st.metric(team_a, f"{pa*100:.1f}%", "P(victoire)")
        st.progress(pa)
    with cv:
        st.markdown("### VS")
    with c2:
        st.metric(team_b, f"{pb*100:.1f}%", "P(victoire)")
        st.progress(pb)

    fav = team_a if pa > pb else team_b
    margin = abs(pa - 0.5) * 100
    if margin < 5:
        insight_card(f"<b>Match trop serre</b> pour trancher. Moins de {margin:.0f}pt d ecart.", "#f39c12")
    else:
        pct = max(pa, pb) * 100
        insight_card(
            f"<b>Le modele avantage {fav}</b> ({pct:.0f}%) sur la base des stats du tournoi. "
            f"Possession {ra['avg_possession']:.0f}% vs {rb['avg_possession']:.0f}%. "
            f"Conversion {ra['avg_conversion_rate']:.0f}% vs {rb['avg_conversion_rate']:.0f}%.",
            GREEN,
        )

    # Radar comparatif
    st.subheader("Comparaison radar")
    la, va = radar_data(ra, tp)
    lb, vb = radar_data(rb, tp)
    fig_r = go.Figure()
    for name, vals, color in [(team_a, va, GREEN), (team_b, vb, "#3498db")]:
        vc = vals + [vals[0]]; lc = la + [la[0]]
        fig_r.add_trace(go.Scatterpolar(r=vc, theta=lc, fill="toself", name=name,
                                        line_color=color, fillcolor=color, opacity=0.35))
    fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        template="plotly_dark", height=400, margin=dict(t=30, b=10))
    st.plotly_chart(fig_r, use_container_width=True)

    # Comparaison champions historiques
    st.subheader("Quel champion historique ressemblent-ils le plus ?")
    hist = get_historical_champions()
    ch1, ch2 = st.columns(2)
    for col, team, row in [(ch1, team_a, ra), (ch2, team_b, rb)]:
        sims = champion_similarity(row, hist)
        with col:
            st.markdown(f"**{team}** ressemble le plus a :")
            if not sims.empty:
                b = sims.iloc[0]
                st.markdown(f"**{b['champion']} {int(b['year'])}** (sim. {b['similarity']:.0f}%)")
                st.caption(b["note"])
            else:
                st.info("Donnees insuffisantes.")

    st.caption(f"Modele : regression logistique sur {meta['n_matches']} matchs. A titre analytique.")

prediction_clash()
