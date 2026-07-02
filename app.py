"""
app.py — Coupe du Monde 2026 : les stats prédisent-elles le vainqueur ?

Vue d'ensemble du tournoi EN COURS (11 juin – 19 juillet 2026, USA/Mexique/Canada) :
combien de matchs joués, phase actuelle, dernier résultat, et la question centrale
du projet en un chiffre.

Données réelles via API-Football. Rien n'est inventé : une stat absente est
affichée "non disponible", et l'analyse est toujours bornée aux matchs déjà joués.
"""

import streamlit as st

from src.analysis import agreement_summary
from src.ui import get_data, transparency_banner

st.set_page_config(
    page_title="CDM 2026 — Stats vs Vainqueur",
    page_icon="⚽",
    layout="wide",
)

st.title("⚽ Coupe du Monde 2026 — les stats prédisent-elles le vainqueur ?")
st.markdown(
    "> *Pendant que le tournoi se joue (11 juin → 19 juillet 2026, "
    "USA · Mexique · Canada), je confronte, match après match, les "
    "**statistiques** (possession, tirs, tirs cadrés) au **résultat réel**. "
    "L'équipe qui domine le jeu gagne-t-elle vraiment ?*"
)

df, meta = get_data()
transparency_banner(meta)

st.divider()

# ─────────────────────────────────────────────────────────────
# INDICATEURS CLÉS
# ─────────────────────────────────────────────────────────────
summary = agreement_summary(df)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Matchs joués", meta["n_matches"])
c2.metric("Matchs analysables", summary["n_evaluables"],
          help="Matchs où une équipe domine clairement les stats disponibles.")
c3.metric(
    "Le dominant a gagné",
    f'{summary["pct_dominant_won"]} %' if summary["pct_dominant_won"] is not None else "—",
    help="Part des matchs où l'équipe qui domine les stats l'emporte.",
)
c4.metric("Surprises", summary["n_surprises"],
          help="Matchs où le dominant statistique n'a PAS gagné.")

st.divider()

# ─────────────────────────────────────────────────────────────
# ÉTAT DU TOURNOI
# ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📍 Où en est le tournoi ?")
    if meta["n_matches"] == 0:
        st.write("Aucun match terminé pour l'instant.")
    else:
        current_round = df.iloc[-1]["round"] if "round" in df.columns else None
        st.write(f"**Phase du dernier match joué :** {current_round or 'non disponible'}")
        st.write(f"**Dernier résultat :** {meta['last_match'] or 'non disponible'}")
        st.write(f"**Données arrêtées au :** {meta['last_updated_str']}")

with col_right:
    st.subheader("🧭 Comment lire ce dashboard")
    st.markdown(
        "- **Score vs Stats** — l'équipe qui domine a-t-elle gagné ?\n"
        "- **Surprises du tournoi** — quand le foot défie les chiffres.\n"
        "- **Bilan live** — les tout derniers résultats, à chaque lancement.\n\n"
        "👉 Naviguez via la barre latérale."
    )

st.divider()

# ─────────────────────────────────────────────────────────────
# DERNIERS MATCHS
# ─────────────────────────────────────────────────────────────
st.subheader("🕹️ Derniers matchs joués")
if meta["n_matches"] == 0:
    st.info("Les résultats apparaîtront ici dès les premiers matchs terminés.")
else:
    recent = df.tail(8).iloc[::-1]
    show = recent[["date", "round", "home_team", "home_goals",
                   "away_goals", "away_team"]].copy()
    show["date"] = show["date"].astype(str).str[:10]
    show.columns = ["Date", "Phase", "Domicile", "Buts (D)", "Buts (E)", "Extérieur"]
    st.dataframe(show, use_container_width=True, hide_index=True)

st.caption(
    "Transparence — les statistiques proviennent d'API-Football pour les matchs "
    "**terminés** uniquement. Toute donnée manquante est signalée "
    "« non disponible » et jamais estimée. Détails des sources dans le README."
)
