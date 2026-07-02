"""
pages/3_Bilan_Live.py — Le tournoi en direct, remis à jour à chaque lancement.

Cette page recharge les données à chaque ouverture (dans la limite du cache TTL)
et affiche les tout derniers résultats, la progression du tournoi et un rappel
clair du périmètre : « X matchs joués au [date] ».
"""

import streamlit as st

from src.analysis import agreement_summary
from src.ui import clear_cache, get_data, na, transparency_banner

st.set_page_config(page_title="Bilan live", page_icon="🔴", layout="wide")

st.title("🔴 Bilan live du tournoi")

col_a, col_b = st.columns([3, 1])
with col_b:
    if st.button("🔄 Forcer la mise à jour", use_container_width=True):
        clear_cache()
        st.rerun()

df, meta = get_data()
transparency_banner(meta)

st.divider()

if meta["n_matches"] == 0:
    st.info("Aucun match terminé pour l'instant. Revenez après les premiers matchs ⚽")
    st.stop()

# ─────────────────────────────────────────────────────────────
# SYNTHÈSE LIVE
# ─────────────────────────────────────────────────────────────
summary = agreement_summary(df)
c1, c2, c3 = st.columns(3)
c1.metric("Matchs joués", meta["n_matches"])
c2.metric("Dominant vainqueur",
          f'{summary["pct_dominant_won"]} %' if summary["pct_dominant_won"] is not None else "—")
c3.metric("Surprises", summary["n_surprises"])

st.markdown(f"#### 🕒 Dernier match enregistré\n**{meta['last_match'] or 'non disponible'}**")
st.caption(f"Données arrêtées au {meta['last_updated_str']} · source : {meta['source']}.")

st.divider()

# ─────────────────────────────────────────────────────────────
# TOUS LES MATCHS JOUÉS
# ─────────────────────────────────────────────────────────────
st.subheader("Tous les matchs joués à date")

full = df.copy()
full["Date"] = full["date"].astype(str).str[:10]
full["Score"] = full.apply(
    lambda r: f"{na(r['home_goals'])} – {na(r['away_goals'])}", axis=1
)
full["Dominant a gagné"] = full["dominant_won"].map(
    {True: "✅ oui", False: "❌ non"}
).fillna("—")

show = full[["Date", "round", "home_team", "Score", "away_team", "Dominant a gagné"]]
show = show.rename(columns={"round": "Phase", "home_team": "Domicile",
                            "away_team": "Extérieur"})
st.dataframe(show.iloc[::-1], use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────────────────────
st.download_button(
    "⬇️ Télécharger les données (CSV)",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name=f"matches_2026_{meta['last_updated'].strftime('%Y%m%d')}.csv",
    mime="text/csv",
)

st.caption(
    "Chaque ligne = un match réellement terminé. Les stats manquantes sont "
    "laissées vides (« non disponible »), jamais estimées."
)
