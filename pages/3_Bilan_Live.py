"""
pages/3_Bilan_Live.py — Le tournoi en direct, remis à jour à chaque lancement.
"""

import plotly.graph_objects as go
import streamlit as st

from src.analysis import agreement_summary
from src.ui import clear_cache, get_data, insight_card, na, render_sidebar, transparency_banner

st.set_page_config(page_title="Bilan live", page_icon="🔴", layout="wide")

df, meta = get_data()
render_sidebar(meta)

st.title("🔴 Bilan live")
st.markdown(
    "Le tournoi en temps réel. Tous les résultats, la progression par phase, "
    "et l’évolution des grands indicateurs. **Actualisé à chaque ouverture.**"
)
transparency_banner(meta, compact=True)

st.divider()

if meta["n_matches"] == 0:
    st.info("Aucun match terminé pour l'instant. Revenez après les premiers matchs ⚽")
    st.stop()

# ─────────────────────────────────────────────────────────────
# SYNTHÈSE LIVE
# ─────────────────────────────────────────────────────────────
summary = agreement_summary(df)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Matchs joués", meta["n_matches"])
c2.metric("Matchs analysables", summary["n_evaluables"])
c3.metric("Dominant vainqueur",
          f'{summary["pct_dominant_won"]} %' if summary["pct_dominant_won"] is not None else "—")
c4.metric("Surprises", summary["n_surprises"])

st.markdown(f"#### Dernier match enregistré\n**{meta['last_match'] or 'non disponible'}**")
st.caption(f"Données arrêtées au {meta['last_updated_str']} · source : {meta['source']}.")

st.divider()

# ─────────────────────────────────────────────────────────────
# ÉVOLUTION PAR PHASE
# ─────────────────────────────────────────────────────────────
st.subheader("Progression du tournoi — matchs joués par phase")
if "round" in df.columns:
    round_counts = df.groupby("round").size().reset_index(name="Matchs joués")
    _order = {
        "Group": 0, "Round of 32": 1, "Round of 16": 2,
        "Quarter": 3, "Semi": 4, "Final": 5,
    }
    round_counts["_sort"] = round_counts["round"].apply(
        lambda r: next((v for k, v in _order.items() if k.lower() in r.lower()), 9)
    )
    round_counts = round_counts.sort_values("_sort").drop(columns="_sort")
    if not round_counts.empty:
        fig_pc = go.Figure(go.Bar(
            x=round_counts["round"], y=round_counts["Matchs joués"],
            text=round_counts["Matchs joués"], textposition="outside",
            marker_color="#00B140",
        ))
        fig_pc.update_layout(
            template="plotly_dark", height=300,
            margin=dict(t=20, b=10), yaxis_title="Matchs",
        )
        st.plotly_chart(fig_pc, width='stretch')

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
    key="dl_csv",
)

st.caption(
    "Chaque ligne = un match réellement terminé. Les stats manquantes sont "
    "laissées vides (« non disponible »), jamais estimées."
)
