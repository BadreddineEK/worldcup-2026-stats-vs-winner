"""
pages/6_Finale_et_Predictions.py

La page WOW pour LinkedIn : bracket du tournoi, profil des finalistes,
prediction du champion par le modele IA, comparaison avec les champions
historiques de la Coupe du Monde.

Tournoi CDM 2026 (USA/Mexique/Canada) :
  Demi-finales : 16-17 juillet | Finale : 19 juillet 2026
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analysis import annotate_matches
from src.clustering import champion_similarity, get_historical_champions
from src.data_build import load_matches
from src.team_analysis import build_ml_dataset, build_team_profiles, radar_data
from src.ui import GREEN, RED, get_data, insight_card, render_sidebar, transparency_banner

st.set_page_config(page_title="Finale & Predictions", page_icon="trophy", layout="wide")

# Auto-refresh toutes les 10 min : nouveau resultat = nouvelles donnees automatiquement
# st.fragment permet de recharger sans recharger toute la page
@st.fragment(run_every="10m")
def _auto_refresh():
    from src.ui import clear_cache
    clear_cache()

_auto_refresh()

df_raw, meta = get_data()
render_sidebar(meta)

st.title("La Finale en chiffres")
st.markdown(
    "Le Data Lab suit le tournoi en direct. Voici ce que **97+ matchs de donnees reelles** "
    "disent sur les equipes encore en lice - et sur qui devrait soulever le trophee."
)
transparency_banner(meta, compact=True)

st.divider()

df = pd.read_csv("data/matches_2026.csv")
tp = build_team_profiles(df)

# ─────────────────────────────────────────────────────────────
# BRACKET : parcours des equipes
# ─────────────────────────────────────────────────────────────
st.subheader("Le chemin vers la finale")

_order = {"Quarter-finals": 0, "Semi-finals": 1}
knockout_matches = df[df["round"].isin(["Quarter-finals", "Semi-finals"])].copy()
knockout_matches["_sort"] = knockout_matches["round"].map(_order)
knockout_matches = knockout_matches.sort_values(["_sort", "date"]).reset_index(drop=True)

# Afficher en colonnes
cols = st.columns(2)
col_names = {"Quarter-finals": "Quarts de finale", "Semi-finals": "Demi-finales"}
for round_name in ["Quarter-finals", "Semi-finals"]:
    col = cols[_order[round_name]]
    with col:
        st.markdown(f"**{col_names[round_name]}**")
        rnd = knockout_matches[knockout_matches["round"] == round_name]
        if rnd.empty:
            st.info("Resultats attendus...")
        else:
            for _, r in rnd.iterrows():
                winner = r["home_team"] if r["winner"] == "home" else r["away_team"] if r["winner"] == "away" else "Egal."
                note = "AET" if r["status"] == "AET" else "Pens" if r["status"] == "PEN" else ""
                score_str = f"{int(r['home_goals'])}-{int(r['away_goals'])}"
                if note:
                    score_str += f" ({note})"
                is_winner_home = r["winner"] == "home"
                ht_bold = f"**{r['home_team']}**" if is_winner_home else r["home_team"]
                at_bold = f"**{r['away_team']}**" if not is_winner_home and r["winner"] == "away" else r["away_team"]
                st.markdown(f"{ht_bold} {score_str} {at_bold}")

# Trouver qui est encore en lice (equipes qui ont gagne leur derniere phase)
def get_active_teams(df_ko):
    """Retourne les equipes encore en competition."""
    rounds_order = ["Quarter-finals", "Semi-finals", "Final"]
    active = set()
    # Chercher le dernier round joue
    played = [r for r in rounds_order if r in df_ko["round"].values]
    if not played:
        return set()
    last_round = played[-1]
    last_matches = df_ko[df_ko["round"] == last_round]
    for _, m in last_matches.iterrows():
        w = m["winner"]
        if w == "home":
            active.add(m["home_team"])
        elif w == "away":
            active.add(m["away_team"])
        else:  # draw possible only before pens
            active.add(m["home_team"])
            active.add(m["away_team"])
    return active

active_teams = get_active_teams(knockout_matches)
# Si pas de SF termine, les 4 QF winners sont en lice
if not active_teams:
    qf_done = knockout_matches[knockout_matches["round"] == "Quarter-finals"]
    for _, m in qf_done.iterrows():
        w = m["winner"]
        active_teams.add(m["home_team"] if w == "home" else m["away_team"])

if active_teams:
    sf_label = "finalistes" if len(active_teams) == 2 else "demi-finalistes" if len(active_teams) == 4 else "equipes encore en lice"
    st.success(f"**{sf_label.capitalize()} :** {' — '.join(sorted(active_teams))}")

st.divider()

# ─────────────────────────────────────────────────────────────
# PROFILS DES EQUIPES EN LICE
# ─────────────────────────────────────────────────────────────
st.subheader("Le profil statistique des equipes encore en lice")
st.markdown(
    "Chaque metrique est une moyenne sur **tous** leurs matchs du tournoi. "
    "Ce sont les memes chiffres qu a entraIne le modele."
)

# Toutes les equipes arrivees en QF ou au-dela
qf_teams_all = set(
    knockout_matches[["home_team", "away_team"]].values.flatten()
)
# Enrichir avec les 8 QF teams meme si pas toutes dans le CSV quarts
r16_winners = set()
for _, m in df[df["round"] == "Round of 16"].iterrows():
    w = m["winner"]
    r16_winners.add(m["home_team"] if w == "home" else m["away_team"])
contenders = qf_teams_all | r16_winners

tp_contenders = tp[tp["team"].isin(contenders)].copy()
tp_contenders = tp_contenders.sort_values("efficiency_score", ascending=False).head(8)

DISP_COLS = {
    "team": "Equipe",
    "matches": "Matchs",
    "wins": "V",
    "win_rate": "Win %",
    "avg_possession": "Poss. moy.",
    "avg_shots": "Tirs/m",
    "avg_shot_accuracy": "Precision %",
    "avg_conversion_rate": "Conv. %",
    "efficiency_score": "Eff. score",
}
disp = tp_contenders[list(DISP_COLS)].rename(columns=DISP_COLS)
st.dataframe(disp, use_container_width=True, hide_index=True)

st.divider()

# ─────────────────────────────────────────────────────────────
# SIMULATEUR DE FINALE (prédiction du modele)
# ─────────────────────────────────────────────────────────────
st.subheader("Simulateur de finale — que dit le modele ?")
st.markdown(
    "Selectionne deux equipes. Le modele de regression logistique entraine "
    "sur les 101 matchs du tournoi calcule leur probabilite de victoire "
    "**si leurs stats moyennes de tournoi se reproduisent en finale.**"
)

all_team_list = sorted(tp["team"].tolist())
# Pré-sélectionner les équipes en lice si connues
default_a = sorted(active_teams)[0] if active_teams else "Spain"
default_b = sorted(active_teams)[1] if len(active_teams) >= 2 else "England"

col_a, col_b = st.columns(2)
with col_a:
    team_a = st.selectbox("Equipe A", all_team_list,
                          index=all_team_list.index(default_a) if default_a in all_team_list else 0,
                          key="fin_a")
with col_b:
    team_b = st.selectbox("Equipe B", all_team_list,
                          index=all_team_list.index(default_b) if default_b in all_team_list else 1,
                          key="fin_b")

if team_a == team_b:
    st.warning("Choisis deux equipes differentes.")
else:
    row_a = tp[tp["team"] == team_a]
    row_b = tp[tp["team"] == team_b]

    if row_a.empty or row_b.empty:
        st.error("Donnees manquantes pour une des equipes.")
    else:
        ra, rb = row_a.iloc[0], row_b.iloc[0]

        # Prediction via le modele
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler

        @st.cache_data(ttl=3600)
        def get_model_pred(n_matches):
            ml = build_ml_dataset(pd.read_csv("data/matches_2026.csv"))
            FEATURES = ["poss_diff", "shots_diff", "sot_diff", "passes_diff", "corners_diff"]
            X = ml[FEATURES].values
            y = ml["won"].values
            sc = StandardScaler().fit(X)
            lr = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
            lr.fit(sc.transform(X), y)
            return lr, sc, FEATURES

        lr, sc, FEATURES = get_model_pred(meta["n_matches"])

        def predict_clash(row_home, row_away):
            diffs = np.array([[
                row_home["avg_possession"] - row_away["avg_possession"],
                row_home["avg_shots"] - row_away["avg_shots"],
                row_home["avg_shots_on_target"] - row_away["avg_shots_on_target"],
                row_home["avg_passes"] - row_away["avg_passes"],
                row_home["avg_corners"] - row_away["avg_corners"],
            ]])
            prob = lr.predict_proba(sc.transform(diffs))[0][1]
            return float(prob)

        # Simulation dans les deux sens, moyenne
        prob_a = predict_clash(ra, rb)
        prob_b = predict_clash(rb, ra)
        # Normaliser
        total = prob_a + prob_b
        prob_a_norm = prob_a / total if total > 0 else 0.5
        prob_b_norm = 1 - prob_a_norm

        col_r1, col_vs, col_r2 = st.columns([2, 1, 2])
        with col_r1:
            color_a = GREEN if prob_a_norm > 0.5 else "#888"
            st.metric(f"{team_a}", f"{prob_a_norm*100:.1f}%", "Probabilite de titre")
            st.progress(prob_a_norm)
        with col_vs:
            st.markdown("### VS")
        with col_r2:
            color_b = GREEN if prob_b_norm > 0.5 else "#888"
            st.metric(f"{team_b}", f"{prob_b_norm*100:.1f}%", "Probabilite de titre")
            st.progress(prob_b_norm)

        # Insight narratif
        winner_pred = team_a if prob_a_norm > 0.5 else team_b
        margin = abs(prob_a_norm - 0.5) * 100
        if margin < 5:
            insight_card(
                f"<b>Match ultra-serre</b> — les donnees ne departent pas clairement "
                f"{team_a} et {team_b}. Tout se jouera sur le terrain.",
                "#f39c12",
            )
        elif prob_a_norm > 0.5:
            insight_card(
                f"<b>Le modele avantage {team_a}</b> ({prob_a_norm*100:.0f}%) "
                f"sur la base de son profil statistique du tournoi. "
                f"Possession : {ra['avg_possession']:.0f}% vs {rb['avg_possession']:.0f}%. "
                f"Conversion : {ra['avg_conversion_rate']:.0f}% vs {rb['avg_conversion_rate']:.0f}%.",
                GREEN,
            )
        else:
            insight_card(
                f"<b>Le modele avantage {team_b}</b> ({prob_b_norm*100:.0f}%) "
                f"sur la base de son profil statistique du tournoi. "
                f"Possession : {rb['avg_possession']:.0f}% vs {ra['avg_possession']:.0f}%. "
                f"Conversion : {rb['avg_conversion_rate']:.0f}% vs {ra['avg_conversion_rate']:.0f}%.",
                GREEN,
            )

        # Radar comparatif
        st.subheader("Comparaison radar")
        labels_a, vals_a = radar_data(ra, tp)
        labels_b, vals_b = radar_data(rb, tp)

        fig_r = go.Figure()
        for name, vals, color in [(team_a, vals_a, GREEN), (team_b, vals_b, "#3498db")]:
            v_closed = vals + [vals[0]]
            l_closed = labels_a + [labels_a[0]]
            fig_r.add_trace(go.Scatterpolar(
                r=v_closed, theta=l_closed,
                fill="toself", name=name,
                line_color=color, fillcolor=color,
                opacity=0.35,
            ))
        fig_r.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            template="plotly_dark",
            height=420,
            margin=dict(t=30, b=10),
        )
        st.plotly_chart(fig_r, width="stretch")

        st.divider()

        # ─────────────────────────────────────────────────────────────
        # PROTOTYPE DU CHAMPION HISTORIQUE
        # ─────────────────────────────────────────────────────────────
        st.subheader("Le champion prototype — contexte historique")
        st.markdown(
            "Quel vainqueur de Coupe du Monde rappelle le plus le profil "
            "statistique de chaque finaliste ?"
        )

        hist = get_historical_champions()

        col_h1, col_h2 = st.columns(2)
        for col, team, row in [(col_h1, team_a, ra), (col_h2, team_b, rb)]:
            sims = champion_similarity(row, hist)
            with col:
                st.markdown(f"**{team}** ressemble le plus a :")
                if not sims.empty:
                    best = sims.iloc[0]
                    st.markdown(
                        f"**{best['champion']} {int(best['year'])}** "
                        f"(similarite : {best['similarity']:.0f}%)"
                    )
                    st.caption(best["note"])
                    if len(sims) > 1:
                        st.dataframe(
                            sims[["year", "champion", "similarity", "note"]].rename(
                                columns={"year": "Annee", "champion": "Champion", "similarity": "Sim. %", "note": "Contexte"}
                            ),
                            use_container_width=True,
                            hide_index=True,
                        )
                else:
                    st.info("Donnees insuffisantes pour la comparaison.")

st.divider()
st.caption(
    "Prediction basee sur un modele de regression logistique entraine sur "
    f"{meta['n_matches']} matchs reels du tournoi. "
    "A titre analytique et pedagogique — pas un pronostic de paris."
)
