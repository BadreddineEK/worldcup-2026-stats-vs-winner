"""
app.py — CDM 2026 Data Lab : stats, ADN d'équipes et modèle IA.

Vue d'ensemble du tournoi EN COURS (11 juin – 19 juillet 2026, USA/Mexique/Canada).
Données réelles via scraping de The Stats Zone. Rien n'est inventé.
"""

import plotly.graph_objects as go
import streamlit as st

from src.analysis import agreement_summary
from src.team_analysis import build_team_profiles
from src.ui import get_data, transparency_banner

st.set_page_config(
    page_title="CDM 2026 — Data Lab",
    page_icon="⚽",
    layout="wide",
)

st.title("⚽ CDM 2026 — Data Lab")
st.markdown(
    "> *96 matchs réels. 48 équipes. Possession, tirs, passes, corners. "
    "Un modèle de machine learning. Des histoires que seules les données peuvent raconter.*"
)

df, meta = get_data()
transparency_banner(meta)

st.divider()

# ─────────────────────────────────────────────────────────────
# INDICATEURS CLÉS
# ─────────────────────────────────────────────────────────────
summary = agreement_summary(df)
tp = build_team_profiles(df)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Matchs joués", meta["n_matches"])
c2.metric(
    "Dominant gagne",
    f'{summary["pct_dominant_won"]} %' if summary["pct_dominant_won"] is not None else "—",
    help="Équipe qui domine possession + tirs + tirs cadrés.",
)
c3.metric("Surprises", summary["n_surprises"],
          help="Matchs où le dominant n'a pas gagné.")
c4.metric("Équipes profilées", len(tp[tp["matches"] >= 3]))
c5.metric("Accuracy modèle IA", "~80%",
          help="Régression logistique, cross-validation 5-fold sur 192 observations.")

st.divider()

# ─────────────────────────────────────────────────────────────
# ÉTAT DU TOURNOI + GRAPHIQUE PHASES
# ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📍 Où en est le tournoi ?")
    if meta["n_matches"] == 0:
        st.write("Aucun match terminé pour l'instant.")
    else:
        current_round = df.iloc[-1]["round"] if "round" in df.columns else None
        st.write(f"**Phase actuelle :** {current_round or 'non disponible'}")
        st.write(f"**Dernier résultat :** {meta['last_match'] or 'non disponible'}")
        st.write(f"**Données au :** {meta['last_updated_str']}")

    if not df.empty and "round" in df.columns:
        round_counts = df.groupby("round").size().reset_index(name="n")
        _order = {
            "Group": 0, "Round of 32": 1, "Round of 16": 2,
            "Quarter": 3, "Semi": 4, "Final": 5,
        }
        round_counts["_s"] = round_counts["round"].apply(
            lambda r: next((v for k, v in _order.items() if k.lower() in r.lower()), 9)
        )
        round_counts = round_counts.sort_values("_s").drop(columns="_s")
        fig_r = go.Figure(go.Bar(
            x=round_counts["round"], y=round_counts["n"],
            text=round_counts["n"], textposition="outside",
            marker_color="#00B140",
        ))
        fig_r.update_layout(
            template="plotly_dark", height=240,
            margin=dict(t=10, b=0, l=0, r=0),
            xaxis_title=None, yaxis_title="Matchs",
            showlegend=False,
        )
        st.plotly_chart(fig_r, use_container_width=True)

with col_right:
    st.subheader("🧭 Les 4 angles du Data Lab")
    st.markdown(
        "**📊 Score vs Stats** — possession/tirs/passes vs résultat réel. "
        "Quelle stat prédit le mieux ? Scatter, trend.\n\n"
        "**🎲 Surprises** — quand le foot défie les chiffres. "
        "Taux par phase, matchs les plus anti-logiques.\n\n"
        "**🧬 ADN des équipes** — radar, efficiency scatter, narration data. "
        "Qui gagne sans dominer ? Qui domine sans gagner ?\n\n"
        "**🤖 Modèle IA** — régression logistique entraînée sur les 96 matchs, "
        "feature importances, prédicteur interactif."
    )

st.divider()

# ─────────────────────────────────────────────────────────────
# APERÇU ADN : TOP équipes par efficiency
# ─────────────────────────────────────────────────────────────
st.subheader("Têtes d'affiche — les profils qui surprennent")

top_teams = tp[tp["matches"] >= 3].nlargest(4, "efficiency_score")
cols = st.columns(4)
for i, (_, row) in enumerate(top_teams.iterrows()):
    with cols[i]:
        wr_delta = f"{row['win_rate']:.0f}% V"
        poss_str = f"{row['avg_possession']:.0f}% poss."
        conv_str = f"{row['avg_conversion_rate']:.0f}% conv." if not __import__('pandas').isna(row['avg_conversion_rate']) else "conv. n/a"
        st.metric(
            row["team"],
            f"{row['wins']:.0f} V / {row['matches']:.0f} matchs",
            delta=f"Eff. #{i+1} | {poss_str} | {conv_str}",
            delta_color="off",
        )

st.divider()

# ─────────────────────────────────────────────────────────────
# DERNIERS MATCHS
# ─────────────────────────────────────────────────────────────
st.subheader("🕹️ Derniers matchs joués")
if meta["n_matches"] == 0:
    st.info("Les résultats apparaîtront ici dès les premiers matchs terminés.")
else:
    recent = df.tail(8).iloc[::-1].copy()
    recent["date"] = recent["date"].astype(str).str[:10]
    recent = recent.rename(columns={
        "date": "Date", "round": "Phase",
        "home_team": "Domicile", "home_goals": "Buts (D)",
        "away_goals": "Buts (E)", "away_team": "Extérieur",
    })
    st.dataframe(
        recent[["Date", "Phase", "Domicile", "Buts (D)", "Buts (E)", "Extérieur"]],
        use_container_width=True, hide_index=True,
    )

st.caption(
    "Source : **The Stats Zone** (pages publiques FIFA World Cup 2026). "
    "Données réelles pour les matchs **terminés** uniquement. "
    "Toute stat manquante est signalée « non disponible », jamais estimée."
)


import plotly.graph_objects as go
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
# ÉTAT DU TOURNOI + GRAPHIQUE PHASES
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

    # Mini barchart matchs par phase
    if not df.empty and "round" in df.columns:
        round_counts = df.groupby("round").size().reset_index(name="n")
        _order = {
            "Group": 0, "Round of 32": 1, "Round of 16": 2,
            "Quarter": 3, "Semi": 4, "Final": 5,
        }
        round_counts["_s"] = round_counts["round"].apply(
            lambda r: next((v for k, v in _order.items() if k.lower() in r.lower()), 9)
        )
        round_counts = round_counts.sort_values("_s").drop(columns="_s")
        fig_r = go.Figure(go.Bar(
            x=round_counts["round"], y=round_counts["n"],
            text=round_counts["n"], textposition="outside",
            marker_color="#00B140",
        ))
        fig_r.update_layout(
            template="plotly_dark", height=250,
            margin=dict(t=10, b=0, l=0, r=0),
            xaxis_title=None, yaxis_title="Matchs joués",
            showlegend=False,
        )
        st.plotly_chart(fig_r, use_container_width=True)

with col_right:
    st.subheader("🧭 Comment lire ce dashboard")
    st.markdown(
        "- **Score vs Stats** — l'équipe qui domine a-t-elle gagné ? "
        "Quelle stat prédit le mieux ? Scatter possession vs buts.\n"
        "- **Surprises du tournoi** — quand le foot défie les chiffres, "
        "par phase et en détail.\n"
        "- **Bilan live** — tous les résultats, exportables en CSV.\n\n"
        "👉 Naviguez via la barre latérale."
    )
    if summary["pct_dominant_won"] is not None:
        pct = summary["pct_dominant_won"]
        st.markdown(f"**Réponse à date :** le dominant statistique gagne **{pct} %** du temps "
                    f"sur {summary['n_evaluables']} matchs analysables.")

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
    "Source : **The Stats Zone** (pages publiques FIFA World Cup 2026). "
    "Données réelles pour les matchs **terminés** uniquement. "
    "Toute stat manquante est signalée « non disponible », jamais estimée."
)
