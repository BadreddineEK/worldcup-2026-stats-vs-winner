"""
pages/1_Score_vs_Stats.py — L'équipe qui domine les stats a-t-elle gagné ?

Pour chaque match TERMINÉ, on confronte possession, tirs et tirs cadrés au
résultat final. On répond, chiffres à l'appui, à la question du projet.
"""

import plotly.graph_objects as go
import streamlit as st

from src.analysis import STAT_PAIRS, agreement_summary, stat_agreement_by_type
from src.ui import get_data, na, no_data_hint, transparency_banner

st.set_page_config(page_title="Score vs Stats", page_icon="📊", layout="wide")

st.title("📊 Score vs Stats — la domination paie-t-elle ?")
df, meta = get_data()
transparency_banner(meta)

if meta["n_matches"] == 0:
    no_data_hint()
    st.stop()

st.divider()

# ─────────────────────────────────────────────────────────────
# RÉPONSE GLOBALE
# ─────────────────────────────────────────────────────────────
summary = agreement_summary(df)
st.subheader("La réponse, à date")

if summary["pct_dominant_won"] is None:
    st.info("Pas encore assez de matchs avec un dominant statistique clair.")
else:
    pct = summary["pct_dominant_won"]
    st.markdown(
        f"### Sur **{summary['n_evaluables']} matchs** avec un dominant clair, "
        f"l'équipe qui maîtrise les stats l'emporte **{pct} %** du temps."
    )
    st.progress(min(int(pct), 100) / 100)
    if pct >= 60:
        st.success("➡️ Dominer le jeu paie plutôt bien… mais le foot garde sa part de hasard.")
    elif pct >= 45:
        st.warning("➡️ Une quasi pièce à pile ou face : les stats ne suffisent pas à prédire.")
    else:
        st.error("➡️ Contre-intuitif : dominer les stats ne garantit pas la victoire.")

st.caption(f"Basé sur {summary['n_matches']} match(s) joué(s) au {meta['last_updated_str']}.")

st.divider()

# ─────────────────────────────────────────────────────────────
# QUELLE STAT PRÉDIT LE MIEUX ?
# ─────────────────────────────────────────────────────────────
st.subheader("Quelle statistique prédit le mieux la victoire ?")
by_type = stat_agreement_by_type(df)
if by_type.empty or by_type["Matchs évaluables"].fillna(0).sum() == 0:
    st.info("Statistiques détaillées pas encore disponibles pour les matchs joués.")
else:
    plot_df = by_type.dropna(subset=["Taux (%)"])
    if not plot_df.empty:
        fig = go.Figure(
            go.Bar(
                x=plot_df["Statistique"],
                y=plot_df["Taux (%)"],
                text=[f"{v:.0f}%" for v in plot_df["Taux (%)"]],
                textposition="outside",
                marker_color="#00B140",
            )
        )
        fig.add_hline(y=50, line_dash="dash", line_color="#888",
                      annotation_text="Hasard (50 %)")
        fig.update_layout(
            yaxis_title="Le meneur de la stat gagne (%)",
            yaxis_range=[0, 100],
            template="plotly_dark",
            height=400,
            margin=dict(t=30, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(by_type, use_container_width=True, hide_index=True)

st.divider()

# ─────────────────────────────────────────────────────────────
# DÉTAIL MATCH PAR MATCH
# ─────────────────────────────────────────────────────────────
st.subheader("Le détail, match par match")

labels = {
    f"{r['home_team']} {na(r['home_goals'])}–{na(r['away_goals'])} {r['away_team']}"
    f"  ·  {str(r['date'])[:10]}": i
    for i, r in df.iterrows()
}
choice = st.selectbox("Choisir un match", list(labels.keys())[::-1])
row = df.loc[labels[choice]]

winner_txt = {
    "home": f"🏆 {row['home_team']}",
    "away": f"🏆 {row['away_team']}",
    "draw": "🤝 Match nul",
}.get(row["winner"], "non disponible")
st.markdown(f"**Résultat :** {winner_txt}")

table_rows = []
for home_col, away_col, label in STAT_PAIRS:
    hv, av = row[home_col], row[away_col]
    leader = row.get(f"{label.lower().replace('é','e').replace('è','e').replace(' ','_')}_leader")
    lead_team = {"home": row["home_team"], "away": row["away_team"]}.get(leader, "—")
    table_rows.append(
        {
            "Statistique": label,
            row["home_team"]: na(hv),
            row["away_team"]: na(av),
            "Domine": lead_team,
        }
    )
st.table(table_rows)

dom = row.get("dominant_side")
if dom in ("home", "away"):
    dom_team = row["home_team"] if dom == "home" else row["away_team"]
    if row.get("dominant_won") is True:
        st.success(f"✅ {dom_team} dominait les stats **et** a gagné.")
    else:
        st.error(f"❌ {dom_team} dominait les stats mais **n'a pas gagné** — une surprise.")
else:
    st.info("Domination partagée ou stats indisponibles : match non tranché par les chiffres.")
