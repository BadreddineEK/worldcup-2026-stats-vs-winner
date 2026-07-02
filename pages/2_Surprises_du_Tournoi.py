"""
pages/2_Surprises_du_Tournoi.py — Quand le résultat défie les statistiques.

On liste les matchs où l'équipe qui a dominé les stats (possession/tirs/tirs
cadrés) n'a pas gagné, et on met en avant les matchs les plus serrés
(faible écart de buts, prolongation, séance de tirs au but).
"""

import streamlit as st

from src.analysis import find_surprises
from src.ui import get_data, na, no_data_hint, transparency_banner

st.set_page_config(page_title="Surprises du tournoi", page_icon="🎲", layout="wide")

st.title("🎲 Surprises du tournoi — le foot contre les chiffres")
df, meta = get_data()
transparency_banner(meta)

if meta["n_matches"] == 0:
    no_data_hint()
    st.stop()

st.divider()

surprises = find_surprises(df)

st.markdown(
    "Une **surprise** = l'équipe qui a dominé les statistiques du match "
    "(majorité de possession, tirs, tirs cadrés) **n'a pas gagné**. "
    "C'est là que le football raconte une autre histoire que les chiffres."
)

st.metric("Surprises détectées", len(surprises),
          help=f"Sur {meta['n_matches']} match(s) joué(s) au {meta['last_updated_str']}.")

if surprises.empty:
    st.success(
        "Aucune surprise pour l'instant : quand une équipe domine les stats, "
        "elle gagne. (Ou pas encore assez de matchs joués pour en voir.)"
    )
    st.stop()

st.divider()
st.subheader("Les matchs qui ont trahi les statistiques")

for _, row in surprises.iloc[::-1].iterrows():
    dom = row.get("dominant_side")
    dom_team = row["home_team"] if dom == "home" else row["away_team"]
    result = f"{row['home_team']} {na(row['home_goals'])}–{na(row['away_goals'])} {row['away_team']}"

    with st.container(border=True):
        st.markdown(f"### {result}")
        st.caption(f"{row.get('round') or 'Phase non disponible'} · {str(row['date'])[:10]}")
        st.write(
            f"**{dom_team}** dominait les statistiques mais n'a pas su convertir. "
        )
        cols = st.columns(3)
        cols[0].metric("Possession",
                       f"{na(row['home_possession'])}% – {na(row['away_possession'])}%")
        cols[1].metric("Tirs",
                       f"{na(row['home_shots'])} – {na(row['away_shots'])}")
        cols[2].metric("Tirs cadrés",
                       f"{na(row['home_shots_on_target'])} – {na(row['away_shots_on_target'])}")

st.divider()

# ─────────────────────────────────────────────────────────────
# MATCHS SERRÉS (faible écart de buts)
# ─────────────────────────────────────────────────────────────
st.subheader("⚔️ Les matchs les plus serrés")
tight = df.copy()
tight = tight[tight["home_goals"].notna() & tight["away_goals"].notna()]
if tight.empty:
    st.info("Pas encore de score complet disponible.")
else:
    tight["ecart"] = (tight["home_goals"] - tight["away_goals"]).abs()
    tight["prolongation"] = tight["status"].isin(["AET", "PEN"])
    tight = tight.sort_values(["ecart", "prolongation"], ascending=[True, False]).head(6)
    show = tight[["date", "round", "home_team", "home_goals",
                  "away_goals", "away_team", "status"]].copy()
    show["date"] = show["date"].astype(str).str[:10]
    show["status"] = show["status"].map(
        {"FT": "Temps réglementaire", "AET": "Prolongation", "PEN": "Tirs au but"}
    ).fillna(show["status"])
    show.columns = ["Date", "Phase", "Domicile", "Buts (D)",
                    "Buts (E)", "Extérieur", "Fin du match"]
    st.dataframe(show, use_container_width=True, hide_index=True)
    st.caption(
        "Un match nul en temps réglementaire tranché aux tirs au but (comme "
        "peut l'être un Belgique–Sénégal) apparaît ici comme « Tirs au but »."
    )
