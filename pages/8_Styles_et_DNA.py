"""
pages/8_Styles_et_DNA.py — Clustering des styles de jeu (PCA + K-Means).

48 equipes, 5 dimensions, 4 profils. Visualisation PCA en 2D.
Et la question ultime : quel profil produit les champions ?
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.clustering import CLUSTER_COLORS, CLUSTER_FEATURES, champion_similarity, cluster_teams, get_historical_champions
from src.team_analysis import build_team_profiles
from src.ui import get_data, insight_card, render_sidebar, transparency_banner

st.set_page_config(page_title="Styles & DNA", page_icon="dna", layout="wide")

df_raw, meta = get_data()
render_sidebar(meta)

st.title("Styles de jeu & DNA des equipes")
st.markdown(
    "K-Means + PCA sur les 5 dimensions statistiques de chaque equipe. "
    "4 profils emergent naturellement des donnees. "
    "Lequel produit les champions ?"
)
transparency_banner(meta, compact=True)

df = pd.read_csv("data/matches_2026.csv")
tp = build_team_profiles(df)

clustered, var_ratio, cluster_stats = cluster_teams(tp)

if clustered is None:
    st.info("Pas assez d equipes avec suffisamment de matchs pour le clustering.")
    st.stop()

st.divider()

# ─────────────────────────────────────────────────────────────
# EXPLICATION PCA
# ─────────────────────────────────────────────────────────────
ev1, ev2 = var_ratio[0] * 100, var_ratio[1] * 100
st.caption(
    f"PCA 2D : composante 1 explique **{ev1:.1f}%** de la variance, "
    f"composante 2 explique **{ev2:.1f}%**. "
    f"Total : **{ev1+ev2:.1f}%** de l information capturee."
)

# ─────────────────────────────────────────────────────────────
# SCATTER PCA avec clusters
# ─────────────────────────────────────────────────────────────
st.subheader("Les 4 DNA du Mondial 2026")

fig = px.scatter(
    clustered,
    x="pca_x", y="pca_y",
    color="cluster_name",
    color_discrete_map=CLUSTER_COLORS,
    text="team",
    size="matches",
    hover_data={
        "team": True,
        "cluster_name": True,
        "avg_possession": ":.0f",
        "avg_conversion_rate": ":.0f",
        "win_rate": ":.0f",
        "matches": True,
    },
    labels={
        "pca_x": f"Dimension 1 ({ev1:.0f}% variance)",
        "pca_y": f"Dimension 2 ({ev2:.0f}% variance)",
        "cluster_name": "Profil",
    },
    template="plotly_dark",
    height=560,
)
fig.update_traces(textposition="top center", textfont_size=8)
fig.update_layout(margin=dict(t=20, b=20), legend_title_text="Profil")
st.plotly_chart(fig, width="stretch")

# ─────────────────────────────────────────────────────────────
# DESCRIPTION DES CLUSTERS
# ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("Les 4 profils")

cluster_descriptions = {
    "Champions Techniques": {
        "icon": "🟢",
        "desc": "Equipes qui **combinent** domination du ballon et efficacite devant le but. "
                "Le profil ideal sur le papier.",
    },
    "Dominateurs Frustres": {
        "icon": "🔵",
        "desc": "Beaucoup de possession, peu de conversion. "
                "Brillantes dans le jeu, decevantes dans les resultats.",
    },
    "Pragmatiques Cliniques": {
        "icon": "🟡",
        "desc": "Peu de ballon mais une efficacite redoutable. "
                "Le contre-modele qui gagne sans dominer.",
    },
    "Defensifs Compteurs": {
        "icon": "🔴",
        "desc": "Attente et compteur. Peu de statistiques offensives, "
                "gestion du resultat en priorite.",
    },
}

cols = st.columns(len(CLUSTER_COLORS))
for i, (cname, color) in enumerate(CLUSTER_COLORS.items()):
    with cols[i]:
        teams_in_cluster = clustered[clustered["cluster_name"] == cname]["team"].tolist()
        desc = cluster_descriptions.get(cname, {})
        st.markdown(f"{desc.get('icon', '')} **{cname}**")
        st.markdown(desc.get("desc", ""))
        st.markdown(f"*{len(teams_in_cluster)} equipes*")
        if cluster_stats is not None and cname in cluster_stats.index:
            s = cluster_stats.loc[cname]
            st.caption(
                f"Poss. moy. {s.get('avg_possession', 0):.0f}% | "
                f"Conv. {s.get('avg_conversion_rate', 0):.0f}% | "
                f"Win rate {s.get('win_rate', 0):.0f}%"
            )
        with st.expander("Voir les equipes"):
            st.write(", ".join(sorted(teams_in_cluster)))

st.divider()

# ─────────────────────────────────────────────────────────────
# QUEL PROFIL PRODUIT LES CHAMPIONS ?
# ─────────────────────────────────────────────────────────────
st.subheader("Le profil qui mene au titre")

hist = get_historical_champions()

# Classifier les champions historiques dans nos clusters
# via la similarite avec chaque centroide
if cluster_stats is not None:
    centroids = clustered.groupby("cluster_name")[CLUSTER_FEATURES].mean()
    champ_profiles = []
    for _, hr in hist.iterrows():
        best_sim = -1
        best_cluster = "Inconnu"
        for cn, crow in centroids.iterrows():
            feats = ["avg_possession", "avg_shots", "avg_conversion_rate"]
            team_v = [hr.get("avg_possession", 0), hr.get("avg_shots", 0), hr.get("avg_conversion_rate", 0)]
            cent_v = [crow.get("avg_possession", 0), crow.get("avg_shots", 0), crow.get("avg_conversion_rate", 0)]
            import numpy as np
            d = np.linalg.norm(np.array(team_v) - np.array(cent_v))
            if best_sim == -1 or d < best_sim:
                best_sim = d
                best_cluster = cn
        champ_profiles.append({"year": hr["year"], "champion": hr["champion"], "cluster": best_cluster})

    champ_df = pd.DataFrame(champ_profiles)
    cluster_wins = champ_df["cluster"].value_counts().reset_index()
    cluster_wins.columns = ["Profil", "Titres"]

    col_pie, col_insight = st.columns([1, 2])
    with col_pie:
        fig_pie = px.pie(
            cluster_wins,
            names="Profil",
            values="Titres",
            color="Profil",
            color_discrete_map=CLUSTER_COLORS,
            template="plotly_dark",
            hole=0.4,
        )
        fig_pie.update_layout(height=300, margin=dict(t=20, b=10))
        st.plotly_chart(fig_pie, width="stretch")

    with col_insight:
        dominant_profile = cluster_wins.iloc[0]["Profil"] if not cluster_wins.empty else "N/A"
        st.markdown(f"#### Le profil {dominant_profile} a gagne {cluster_wins.iloc[0]['Titres']} des 5 dernieres finales.")
        st.dataframe(
            champ_df.rename(columns={"year": "Annee", "champion": "Champion", "cluster": "Profil"}),
            use_container_width=True, hide_index=True,
        )

        # Ou se placent les equipes encore en lice ?
        r16_winners = set()
        for _, m in df[df["round"] == "Round of 16"].iterrows():
            w = m["winner"]
            r16_winners.add(m["home_team"] if w == "home" else m["away_team"])

        contenders_cluster = clustered[clustered["team"].isin(r16_winners)][["team", "cluster_name", "win_rate"]].copy()
        contenders_cluster = contenders_cluster.sort_values("win_rate", ascending=False)

        if not contenders_cluster.empty:
            st.markdown("**Les 8 derniers encore en lice :**")
            st.dataframe(
                contenders_cluster.rename(
                    columns={"team": "Equipe", "cluster_name": "Profil", "win_rate": "Win %"}
                ),
                use_container_width=True, hide_index=True,
            )

st.divider()

# ─────────────────────────────────────────────────────────────
# EVOLUTION PAR PHASE (possession)
# ─────────────────────────────────────────────────────────────
st.subheader("Evolution de la possession par phase")
st.markdown(
    "La possession reflète la manière dont une équipe joue. "
    "Une ligne qui monte = l'équipe contrôle de plus en plus. "
    "Les équipes avec des lignes stables = style constant."
)

_order_rounds = {
    "Group": 0, "Round of 32": 1, "Round of 16": 2,
    "Quarter-finals": 3, "Semi-finals": 4,
}
_phase_labels = {
    0: "Groupes",
    1: "R. de 32",
    2: "Huitièmes",
    3: "Quarts",
    4: "Demi-finales",
    5: "Finale",
}

teams_for_momentum = sorted(r16_winners) if r16_winners else []
if not teams_for_momentum:
    teams_for_momentum = sorted(tp.nlargest(8, "win_rate")["team"].tolist())

selected_m = st.multiselect(
    "Équipes à comparer",
    options=sorted(tp["team"].tolist()),
    default=teams_for_momentum[:4] if len(teams_for_momentum) >= 4 else teams_for_momentum,
    key="momentum_sel",
)

if selected_m:
    # Collecter possession par equipe et par phase
    poss_rows = []
    for _, r in df.iterrows():
        for side, other in [("home", "away"), ("away", "home")]:
            team = r[f"{side}_team"]
            if team not in selected_m:
                continue
            poss = r.get(f"{side}_possession")
            rnd  = r["round"]
            phase_sort = next((v for k, v in _order_rounds.items() if k.lower() in rnd.lower()), 9)
            if pd.notna(poss) and phase_sort < 9:
                poss_rows.append({"team": team, "phase_sort": phase_sort, "possession": float(poss)})

    if poss_rows:
        poss_df  = pd.DataFrame(poss_rows)
        # Moyenne de possession par équipe et par phase
        agg_poss = (
            poss_df.groupby(["team", "phase_sort"])["possession"]
            .mean()
            .reset_index()
        )
        agg_poss = agg_poss.sort_values(["team", "phase_sort"])

        played_phases = sorted(agg_poss["phase_sort"].unique())

        fig_mom = go.Figure()
        colors_cycle = ["#00B140", "#3498db", "#f39c12", "#e74c3c",
                        "#9b59b6", "#1abc9c", "#e67e22", "#2ecc71"]
        for i, team in enumerate(selected_m):
            team_data = agg_poss[agg_poss["team"] == team].sort_values("phase_sort")
            if not team_data.empty:
                color = colors_cycle[i % len(colors_cycle)]
                fig_mom.add_trace(go.Scatter(
                    x=team_data["phase_sort"].tolist(),
                    y=team_data["possession"].tolist(),
                    mode="lines+markers",
                    name=team,
                    marker=dict(size=9, color=color),
                    line=dict(width=2.5, color=color),
                    hovertemplate=f"<b>{team}</b><br>%{{customdata}}<br>Possession : %{{y:.0f}}%<extra></extra>",
                    customdata=[_phase_labels.get(p, str(p)) for p in team_data["phase_sort"].tolist()],
                ))

        # Ligne de référence à 50%
        fig_mom.add_hline(y=50, line_dash="dot", line_color="#555",
                          annotation_text="50% (équilibre)", annotation_position="right")

        fig_mom.update_xaxes(
            ticktext=[_phase_labels.get(p, str(p)) for p in played_phases],
            tickvals=played_phases,
            title_text=None,
        )
        fig_mom.update_yaxes(
            title_text="Possession moyenne (%)",
            range=[25, 80],
        )
        fig_mom.update_layout(
            template="plotly_dark",
            height=380,
            margin=dict(t=20, b=10),
            legend_title_text="Équipe",
        )
        st.plotly_chart(fig_mom, width="stretch")
        st.caption(
            f"Possession moyenne par phase de tournoi. "
            f"Calculée sur tous les matchs de chaque phase pour chaque équipe. "
            f"Données : {meta['n_matches']} matchs."
        )
    else:
        st.info("Sélectionne des équipes dans la liste pour voir leur évolution.")

st.divider()
st.caption(
    f"Clustering K-Means (k=4) + PCA sur 5 features statistiques. "
    f"Données : {meta['n_matches']} matchs au {meta['last_updated_str']}."
)
