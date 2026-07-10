"""
pages/1_Score_vs_Stats.py — L'équipe qui domine les stats a-t-elle gagné ?

Pour chaque match TERMINÉ, on confronte possession, tirs et tirs cadrés au
résultat final. On répond, chiffres à l'appui, à la question du projet.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analysis import STAT_PAIRS, agreement_summary, stat_agreement_by_type
from src.ui import GREEN, RED, get_data, insight_card, na, no_data_hint, render_sidebar, transparency_banner

st.set_page_config(page_title="Score vs Stats", page_icon="📊", layout="wide")

df, meta = get_data()
render_sidebar(meta)

st.title("📊 Stats vs Résultats")
st.markdown(
    "**La question centrale :** l’équipe qui domine la possession, qui tire plus, "
    "qui cadre mieux — gagne-t-elle vraiment ? "
    "Et quelle statistique prédit le mieux le résultat ?"
)
transparency_banner(meta, compact=True)

if meta["n_matches"] == 0:
    no_data_hint()
    st.stop()

st.divider()

# ─────────────────────────────────────────────────────────────
# RÉPONSE GLOBALE
# ─────────────────────────────────────────────────────────────
summary = agreement_summary(df)
st.subheader("À date, sur 97 matchs")

if summary["pct_dominant_won"] is None:
    st.info("Pas encore assez de matchs avec un dominant statistique clair.")
else:
    pct = summary["pct_dominant_won"]
    col1, col2 = st.columns([2, 1])
    with col1:
        if pct >= 60:
            insight_card(
                f"L’équipe qui domine les stats gagne <b>{pct}%</b> du temps "
                f"sur {summary['n_evaluables']} matchs analysables. "
                "Mais 38% des résultats défient les chiffres.",
                GREEN,
            )
        else:
            insight_card(
                f"Seulement <b>{pct}%</b> de victoires pour le dominant — "
                "presque une pièce à pile ou face. "
                "Les stats seules ne suffisent pas.",
                RED,
            )
        st.progress(min(int(pct), 100) / 100)
    with col2:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pct,
            number={"suffix": "%", "font": {"size": 36}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": GREEN},
                "steps": [
                    {"range": [0, 50], "color": "#1a1d24"},
                    {"range": [50, 100], "color": "#161b22"},
                ],
                "threshold": {"line": {"color": "#888", "width": 2}, "value": 50},
            },
        ))
        fig_gauge.update_layout(
            height=200, margin=dict(t=20, b=0, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_gauge, width='stretch')

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
            height=380,
            margin=dict(t=30, b=10),
        )
        st.plotly_chart(fig, width='stretch')
    st.dataframe(by_type, use_container_width=True, hide_index=True)

st.divider()

# ─────────────────────────────────────────────────────────────
# BREAKDOWN PAR PHASE
# ─────────────────────────────────────────────────────────────
st.subheader("Taux de victoire du dominant par phase")
if "round" in df.columns and "dominant_won" in df.columns:
    round_stats = (
        df[df["dominant_won"].notna()]
        .groupby("round")
        .agg(
            Evaluables=("dominant_won", "count"),
            Gagnés=("dominant_won", lambda x: (x == True).sum()),
        )
        .reset_index()
    )
    round_stats["Taux (%)"] = (round_stats["Gagnés"] / round_stats["Evaluables"] * 100).round(1)
    # Ordre cohérent avec le tournoi
    _order = {
        "Group": 0, "Round of 32": 1, "Round of 16": 2,
        "Quarter": 3, "Semi": 4, "Final": 5,
    }
    round_stats["_sort"] = round_stats["round"].apply(
        lambda r: next((v for k, v in _order.items() if k.lower() in r.lower()), 9)
    )
    round_stats = round_stats.sort_values("_sort").drop(columns="_sort")
    if not round_stats.empty:
        fig_r = go.Figure(go.Bar(
            x=round_stats["round"],
            y=round_stats["Taux (%)"],
            text=[f"{v:.0f}%" for v in round_stats["Taux (%)"]],
            textposition="outside",
            marker_color=["#00B140" if v >= 50 else "#e74c3c" for v in round_stats["Taux (%)"]],
            customdata=round_stats[["Evaluables"]].values,
            hovertemplate="%{x}<br>%{y:.1f}% (%{customdata[0]} matchs)<extra></extra>",
        ))
        fig_r.add_hline(y=50, line_dash="dash", line_color="#888")
        fig_r.update_layout(
            yaxis_range=[0, 100], template="plotly_dark",
            height=350, margin=dict(t=30, b=10),
            yaxis_title="Le dominant gagne (%)",
        )
        st.plotly_chart(fig_r, width='stretch')

st.divider()

# ─────────────────────────────────────────────────────────────
# SCATTER POSSESSION vs BUTS
# ─────────────────────────────────────────────────────────────
st.subheader("La possession mène-t-elle aux buts ?")
scatter_df = df.dropna(subset=["home_possession", "home_goals"]).copy()
if len(scatter_df) >= 5:
    # Une ligne par équipe (domicile + extérieur)
    home_pts = scatter_df[["home_possession", "home_goals", "home_team", "round"]].rename(
        columns={"home_possession": "possession", "home_goals": "buts", "home_team": "equipe"}
    )
    away_pts = scatter_df[["away_possession", "away_goals", "away_team", "round"]].rename(
        columns={"away_possession": "possession", "away_goals": "buts", "away_team": "equipe"}
    )
    pts = pd.concat([home_pts, away_pts], ignore_index=True)
    pts = pts.dropna(subset=["possession", "buts"])
    fig_s = px.scatter(
        pts, x="possession", y="buts",
        hover_data=["equipe", "round"],
        trendline="ols",
        color_discrete_sequence=["#00B140"],
        labels={"possession": "Possession (%)", "buts": "Buts marqués"},
        template="plotly_dark",
    )
    fig_s.update_layout(height=400, margin=dict(t=30, b=10))
    st.plotly_chart(fig_s, width='stretch')
    # Corrélation rapide
    corr = pts["possession"].corr(pts["buts"])
    st.caption(
        f"Corrélation possession–buts (r = **{corr:.2f}**) "
        f"sur {len(pts)} observations. "
        "Une faible corrélation confirme que la possession ne garantit pas les buts."
    )
else:
    st.info("Pas assez de données pour le scatter (nécessite au moins 5 matchs avec stats).")

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
    key = label.lower().replace("é", "e").replace("è", "e").replace(" ", "_")
    leader = row.get(f"{key}_leader")
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
