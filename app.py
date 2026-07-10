"""
app.py â€” CDM 2026 Data Lab : tableau de bord principal.

Fil conducteur : les statistiques de match peuvent-elles prÃ©dire le vainqueur ?
On rÃ©pond sous 4 angles : corrÃ©lation brute, surprises, ADN des Ã©quipes, IA.
"""

import plotly.graph_objects as go
import streamlit as st

from src.analysis import agreement_summary
from src.team_analysis import build_team_profiles
from src.ui import GREEN, RED, get_data, insight_card, render_sidebar, transparency_banner

st.set_page_config(
    page_title="CDM 2026 â€” Data Lab",
    page_icon="âš½",
    layout="wide",
)

df, meta = get_data()
render_sidebar(meta)

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# EN-TÃŠTE
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.title("âš½ CDM 2026 â€” Data Lab")

summary = agreement_summary(df)
pct = summary["pct_dominant_won"]

col_hook, col_kpi = st.columns([3, 2])
with col_hook:
    st.markdown("### Les stats prÃ©disent-elles le vainqueur ?")
    st.markdown(
        "Pendant que la Coupe du Monde 2026 se joue "
        "(11 juin â†’ 19 juillet, USA Â· Mexique Â· Canada), "
        "ce Data Lab confronte les **chiffres rÃ©els** de chaque match "
        "au rÃ©sultat final."
    )
    if pct is not None:
        color = GREEN if pct >= 60 else "#f39c12" if pct >= 50 else RED
        insight_card(
            f"<b>RÃ©ponse Ã  date :</b> l'Ã©quipe dominante gagne <b>{pct}%</b> du temps "
            f"sur {summary['n_evaluables']} matchs analysables. "
            f"Mais {summary['n_surprises']} matchs ont dÃ©fiÃ© les chiffres.",
            color,
        )

with col_kpi:
    tp = build_team_profiles(df)
    c1, c2 = st.columns(2)
    c1.metric("Matchs analysÃ©s", meta["n_matches"])
    c2.metric("Dominant gagne", f"{pct} %" if pct else "â€”")
    c3, c4 = st.columns(2)
    c3.metric("Surprises", summary["n_surprises"])
    c4.metric("ModÃ¨le IA", "~79%", help="Accuracy cross-validation 5-fold.")

transparency_banner(meta, compact=True)

st.divider()

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# LES 4 ANGLES
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.subheader("Les 4 angles du projet")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown("#### ðŸ“Š Stats vs RÃ©sultats")
    st.markdown(
        "Quelle stat prÃ©dit le mieux ? "
        "Spoiler : ce n'est *pas* la possession â€” "
        "c'est la **prÃ©cision** des tirs."
    )
with c2:
    st.markdown("#### ðŸŽ² Surprises")
    st.markdown(
        f"**{summary['n_surprises']} matchs** oÃ¹ les chiffres ont menti. "
        "Le football dans toute sa beautÃ© imprÃ©visible."
    )
with c3:
    st.markdown("#### ðŸ§¬ ADN des Ã©quipes")
    st.markdown(
        "Norway : 80% de victoires avec 53% de possession. "
        "Chaque Ã©quipe a une empreinte unique."
    )
with c4:
    st.markdown("#### ðŸ¤– ModÃ¨le IA")
    st.markdown(
        "79% d'accuracy. Et un rÃ©sultat contre-intuitif : "
        "plus de tirs bruts = *moins* de chances de gagner."
    )

st.divider()

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# TOURNOI : graphique phases + derniers rÃ©sultats
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("ðŸ“ Avancement du tournoi")
    if not df.empty and "round" in df.columns:
        _order = {
            "Group": 0, "Round of 32": 1, "Round of 16": 2,
            "Quarter": 3, "Semi": 4, "Final": 5,
        }
        rc = df.groupby("round").size().reset_index(name="n")
        rc["_s"] = rc["round"].apply(
            lambda r: next((v for k, v in _order.items() if k.lower() in r.lower()), 9)
        )
        rc = rc.sort_values("_s").drop(columns="_s")
        colors = [
            "#00B140" if "Group" in r
            else "#3498db" if ("32" in r or "16" in r)
            else "#f39c12"
            for r in rc["round"]
        ]
        fig = go.Figure(go.Bar(
            x=rc["round"], y=rc["n"],
            text=rc["n"], textposition="outside",
            marker_color=colors,
        ))
        fig.update_layout(
            template="plotly_dark", height=260,
            margin=dict(t=10, b=0, l=0, r=0),
            yaxis_title="Matchs", xaxis_title=None, showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("ðŸ•¹ï¸ Derniers rÃ©sultats")
    if not df.empty:
        for _, r in df.tail(5).iloc[::-1].iterrows():
            date = str(r["date"])[:10]
            score = f"{int(r['home_goals'])}â€“{int(r['away_goals'])}"
            st.markdown(f"**{r['home_team']}** {score} **{r['away_team']}** `{date}`")

st.divider()

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# TOP Ã‰QUIPES (teaser)
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
st.subheader("ðŸ† Les 6 Ã©quipes les plus efficaces")
st.caption(
    "Efficiency score = taux de victoire / possession moyenne. "
    "Un score Ã©levÃ© = beaucoup de victoires sans forcÃ©ment dominer le ballon."
)

import pandas as pd

top = tp[tp["matches"] >= 3].nlargest(6, "efficiency_score")
cols_t = st.columns(6)
for i, (_, r) in enumerate(top.iterrows()):
    conv = r["avg_conversion_rate"]
    conv_str = f"{conv:.0f}% conv" if pd.notna(conv) else "conv. n/d"
    with cols_t[i]:
        st.metric(
            r["team"],
            f"{int(r['wins'])}/{int(r['matches'])} V",
            delta=f"{r['avg_possession']:.0f}% poss Â· {conv_str}",
            delta_color="off",
        )

st.caption(
    f"DonnÃ©es au {meta['last_updated_str']} Â· "
    "Source : [The Stats Zone](https://www.thestatszone.com/fwc26/) Â· "
    "[Code source](https://github.com/BadreddineEK/worldcup-2026-stats-vs-winner)"
)

